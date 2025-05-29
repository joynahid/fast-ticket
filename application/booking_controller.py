import asyncio
import multiprocessing
import signal
import sys
import time
import traceback
import logging
from typing import Any, List, Optional, Dict
from multiprocessing import Process, Queue, Lock, Value
from rich.console import Console
from rich.table import Table
from application.booking_worker import booking_worker
from business.exception import (
    MultipleOrderAttemptException,
    OrderLimitExceededForTheDayException,
    OtpExpiredException,
    OtpVerificationFailedException,
)
from models import (
    SearchCriteria,
    BookingRequest,
    BookingResult,
    Trip,
    Passenger,
)
from business.auth_service import RailwayAuthService
from business.trip_repository import RailwayTripRepository
from business.booking_service import RailwayBookingService
from infrastructure.api_client import RailwayApiClient
from infrastructure.cache_service import FileCacheService
from infrastructure.storage_service import FileStorageService
from config import BookingConfig
from application.seat_reservation_controller import SeatReservationController

# Configure logging
logger = logging.getLogger("booking_controller")
console = Console()


class BookingController:
    """Main controller for the booking process."""

    def __init__(self, config: BookingConfig):
        """
        Initialize the booking controller.

        Args:
            config (BookingConfig): Configuration object
        """
        self.config = config

        # Ensure required directories exist
        config.ensure_directories()

        # Initialize infrastructure
        self.api_client = RailwayApiClient(config.auth_token)
        self.cache_service = FileCacheService(config.cache_dir)
        self.storage_service = FileStorageService(config.booking_info_dir)

        # Create synchronization primitives
        self._reservation_lock = Lock()
        self._is_reserved = Value("b", False)  # Shared boolean value

        # Initialize business services
        self.auth_service = RailwayAuthService(self.api_client, config)
        self.trip_repository = RailwayTripRepository(
            self.api_client, self.cache_service
        )
        self.booking_service = RailwayBookingService(self.api_client, config)
        self.seat_reservation_controller = SeatReservationController(
            self.api_client,
            self.cache_service,
            config,
            self._reservation_lock,
            self._is_reserved,
        )

    async def finalize_booking(
        self,
        reservation_data: Dict[str, Any],
        otp: str,
        from_city: str,
        to_city: str,
    ) -> bool:
        """Finalize the booking."""
        # Verify OTP
        verify_result = await self.booking_service.verify_otp(
            reservation_data["trip"].trip_id,
            reservation_data["trip"].trip_route_id,
            reservation_data["ticket_ids"],
            otp,
        )

        if verify_result:
            # Create and submit booking
            booking_request = BookingRequest(
                trip=reservation_data["trip"],
                passengers=reservation_data["passengers"],
                selected_seats=reservation_data["selected_seats"],
                boarding_point=reservation_data["trip"].find_boarding_point(from_city),
                num_seats=len(reservation_data["selected_seats"]),
                from_city=from_city,
                to_city=to_city,
            )

            booking_data = await self.booking_service.create_booking_data(
                booking_request, otp
            )

            booking_result = await self.booking_service.submit_booking(booking_data)

            if booking_result.success:
                await self._handle_successful_booking(
                    booking_result, from_city, to_city
                )
                logger.info("✅️ Booking successful")
                return True
            else:
                logger.error(f"❌️ Booking failed: {booking_result.error_message}")
                return False
        else:
            logger.error("❌️ OTP verification failed")
            return False

    async def book_ticket(
        self,
        from_city: Optional[str] = None,
        to_city: Optional[str] = None,
        selected_trip: Optional[Trip] = None,
        parallel_booking_processes: Optional[int] = None,
    ) -> bool:
        """
        Execute the complete booking process with parallel processing using all available CPU cores.

        Args:
            from_city (str, optional): Source city (overrides config)
            to_city (str, optional): Destination city (overrides config)
            selected_trip (Trip, optional): Selected trip to book

        Returns:
            bool: True if booking successful, False otherwise
        """
        processes: List[Process] = []
        result_queue = Queue()

        try:
            # Reset the reservation state
            self._is_reserved.value = False

            # Get the number of CPU cores
            num_processes = parallel_booking_processes or multiprocessing.cpu_count()
            logger.info(f"Starting {num_processes} parallel booking processes...")

            for i in range(num_processes):
                p = Process(
                    target=booking_worker,
                    args=(
                        i + 1,
                        selected_trip,
                        from_city,
                        to_city,
                        result_queue,
                        self.config.to_dict(),
                        self._reservation_lock,
                        self._is_reserved,
                    ),
                )
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            # Terminate all processes
            for p in processes:
                if p.is_alive():
                    p.terminate()

            reservation_data = result_queue.get()

            if not reservation_data:
                logger.warning("No successful reservation within timeout period")
                return False

            # Create a rich table for seat reservation display
            table = Table(title="Seats Reserved")
            table.add_column("Process", style="cyan")
            table.add_column("Seat", style="green")
            table.add_column("Passenger", style="yellow")
            table.add_column("Ticket ID", style="blue")
            table.add_column("Trip ID", style="magenta")
            table.add_column("Trip Route ID", style="red")

            for seat, passenger in zip(
                reservation_data["selected_seats"], reservation_data["passengers"]
            ):
                table.add_row(
                    str(reservation_data["process_id"]),
                    seat.seat_number,
                    passenger.name,
                    str(seat.ticket_id),
                    str(reservation_data["trip"].trip_id),
                    str(reservation_data["trip"].trip_route_id),
                )

            console.print(table)

            if table.row_count == 0:
                logger.error("❌️ No seats reserved")
                return False

            passenger_details = await self.api_client.get_passenger_details(
                reservation_data["trip"].trip_id,
                reservation_data["trip"].trip_route_id,
                reservation_data["ticket_ids"],
            )

            if not passenger_details.success:
                logger.error(f"Failed to send OTP: {passenger_details.error_message}")
                return False

            # Get OTP from user
            otp = console.input("🔑 Enter OTP: ")

            # Finalize booking
            return await self.finalize_booking(
                reservation_data, otp, from_city, to_city
            )
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt received. Stopping all processes...")
            # Terminate all processes
            for p in processes:
                if p.is_alive():
                    p.terminate()
            logger.info("All processes stopped.")
            raise
        except Exception as e:
            logger.error(f"Booking error: {e}", exc_info=True)
            return False
        finally:
            # Clean up resources
            await self.api_client.close()
            # Ensure all processes are terminated
            for p in processes:
                if p.is_alive():
                    p.terminate()

    async def _search_trips(
        self,
        from_city: Optional[str] = None,
        to_city: Optional[str] = None,
        journey_date: Optional[str] = None,
    ) -> List[Trip]:
        """Search for available trips."""
        # Use provided parameters or fall back to config
        search_from = from_city
        search_to = to_city
        search_date = journey_date

        search_criteria = SearchCriteria(
            from_city=search_from,
            to_city=search_to,
            journey_date=search_date,
            seat_class=self.config.seat_class,
            preferred_train=self.config.preferred_train,
        )

        trips = await self.trip_repository.search_trips(search_criteria)

        # Filter by preferred train if specified
        if self.config.preferred_train and trips:
            filtered_trips = [
                trip
                for trip in trips
                if self.config.preferred_train.lower() in trip.train_name.lower()
            ]
            if filtered_trips:
                trips = filtered_trips
                logger.info(f"Found preferred train: {self.config.preferred_train}")
            else:
                logger.warning(
                    f"Warning: Preferred train '{self.config.preferred_train}' not found."
                )

        # Display available trips
        self._display_available_trips(trips)
        return trips

    def _select_trip(self, trips: List[Trip], trip_number: int) -> Trip:
        """Select a trip from the available options."""
        if self.config.auto_select_train or len(trips) == 1:
            logger.info("Automatically selecting the first available train.")
            return trips[0]

        # Select based on trip number
        selected_index = trip_number - 1
        if selected_index < 0 or selected_index >= len(trips):
            logger.warning("Invalid selection, using the first trip")
            selected_index = 0

        return trips[selected_index]

    async def _prepare_passengers_async(self) -> List[Passenger]:
        """Prepare passenger information asynchronously."""
        passengers = self.passenger_service.create_passengers_from_config(
            names=self.config.passenger_names,
            email=self.config.passenger_email,
            mobile=self.config.passenger_mobile,
            genders=self.config.passenger_genders,
            types=self.config.passenger_types,
        )

        # Validate passengers
        self.passenger_service.validate_passengers(passengers)

        logger.info("Passenger Information:")
        logger.info(self.passenger_service.get_passenger_summary(passengers))

        return passengers

    async def _handle_successful_booking(
        self,
        booking_result: BookingResult,
        from_city: Optional[str],
        to_city: Optional[str],
    ) -> None:
        """Handle successful booking."""
        logger.info("Ticket booking completed successfully!")

        # Save booking information if enabled
        if self.config.save_booking_info and booking_result.booking_data:
            self.storage_service.save_booking_info(
                booking_result.booking_data, booking_result.confirmation_response or {}
            )

        # Display booking summary
        booking_data = booking_result.booking_data

        # Display booking summary
        table = Table(title="Booking Summary", title_justify="left")
        table.add_column("Journey", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Passengers", style="yellow")
        table.add_column("Contact", style="blue")
        table.add_column("Payment Link")

        table.add_row(
            f"{from_city} to {to_city}",
            booking_data.date_of_journey,
            ", ".join(booking_data.pname),
            booking_data.pmobile,
            booking_result.confirmation_response.get("data", {}).get("redirectUrl", ""),
        )
        console.print(table)

    def _display_available_trips(self, trips: List[Trip]) -> None:
        """Display available trips to the user."""
        table = Table(title="Available Trips", title_justify="left")
        table.add_column("Train", style="cyan")
        table.add_column("Departure", style="green")
        table.add_column("Arrival", style="yellow")
        table.add_column("Duration", style="blue")
        table.add_column("Fare", style="magenta")

        for trip in trips:
            table.add_row(
                trip.train_name,
                trip.departure_time,
                trip.arrival_time,
                trip.travel_time,
                str(trip.total_fare),
            )

        console.print(table)

    async def __run_with_retry(
        self,
        trip_number: int = 1,
        refresh_cache: bool = True,
        from_city: Optional[str] = None,
        to_city: Optional[str] = None,
        journey_date: Optional[str] = None,
        parallel_booking_processes: Optional[int] = None,
    ) -> None:
        """
        Run booking with retry logic.

        Args:
            trip_number (int): Trip number to book
            refresh_cache (bool): Whether to refresh cache
            from_city (str, optional): Source city (overrides config)
            to_city (str, optional): Destination city (overrides config)
            journey_date (str, optional): Journey date (overrides config)
        """

        def sigint_handler(signum, frame):
            logger.warning("Keyboard interrupt received. Cleaning up...")
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, sigint_handler)

        # Step 1: Ensure authentication
        await self.auth_service.ensure_authenticated()

        # Step 2: Clear cache if requested
        if refresh_cache:
            logger.info("Refreshing cache...")
            self.cache_service.clear_all()

        # Step 3: Search for trips
        try:
            trips = await self._search_trips(from_city, to_city, journey_date)
            if not trips:
                seat_class = self.config.seat_class
                search_from = from_city
                search_to = to_city
                logger.error(
                    f"No {seat_class} class trips found from {search_from} to {search_to}"
                )
                return False
        except Exception as e:
            logger.error(f"No trips found. {e}")
            return False

        # Step 4: Select trip
        selected_trip = self._select_trip(trips, trip_number)
        logger.info(f"Selected trip: {selected_trip.train_name}")

        attempt = 0
        while attempt < self.config.max_retry_attempts:
            attempt += 1

            success = await self.book_ticket(
                from_city, to_city, selected_trip, parallel_booking_processes
            )

            if success:
                logger.info(f"Ticket booked successfully on attempt {attempt}")
                break
            else:
                logger.warning(f"Attempt {attempt} failed. Retrying...")

        if attempt >= self.config.max_retry_attempts:
            logger.error(
                f"Failed to book ticket after {self.config.max_retry_attempts} attempts"
            )

    async def run_with_retry(
        self,
        trip_number: int = 1,
        refresh_cache: bool = True,
        from_city: Optional[str] = None,
        to_city: Optional[str] = None,
        journey_date: Optional[str] = None,
        parallel_booking_processes: Optional[int] = None,
    ) -> None:
        """Run booking with retry logic."""
        try:
            await self.__run_with_retry(
                trip_number,
                refresh_cache,
                from_city,
                to_city,
                journey_date,
                parallel_booking_processes,
            )
        except KeyboardInterrupt:
            logger.warning("Booking process interrupted by user")
        except Exception as e:
            logger.error(f"Booking process failed: {e}")
            logger.error(traceback.format_exc())
        finally:
            await self.api_client.close()
