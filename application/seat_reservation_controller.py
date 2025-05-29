import asyncio
from typing import List, Optional, Tuple, Dict
from multiprocessing import Lock, Value
from business.exception import SeatAlreadyReservedException
from models import Trip, Seat, SeatLayout, Passenger
from business.seat_service import RailwaySeatService
from business.trip_repository import RailwayTripRepository
from business.passenger_service import RailwayPassengerService
from infrastructure.api_client import RailwayApiClient
from infrastructure.cache_service import FileCacheService
from config import BookingConfig
import logging

# Configure logging
logger = logging.getLogger("seat_reservation_controller")


class SeatReservationController:
    """Controller for handling seat reservation operations."""

    def __init__(
        self,
        api_client: RailwayApiClient,
        cache_service: FileCacheService,
        config: BookingConfig,
        reservation_lock: Lock,
        is_reserved: Value,
    ):
        """
        Initialize the seat reservation controller.

        Args:
            api_client (RailwayApiClient): API client for making requests
            cache_service (FileCacheService): Cache service for storing data
            config (BookingConfig): Configuration object
            reservation_lock (Lock): Lock for synchronizing seat reservations
            is_reserved (Value): Shared boolean value indicating if seats are already reserved
        """
        self.api_client = api_client
        self.cache_service = cache_service
        self.config = config
        self.seat_service = RailwaySeatService(api_client)
        self.trip_repository = RailwayTripRepository(api_client, cache_service)
        self.passenger_service = RailwayPassengerService()
        self._reservation_lock = reservation_lock
        self._is_reserved = is_reserved

    async def find_seat_layout_and_passengers(
        self,
        selected_trip: Trip,
        process_id: int,
    ) -> Optional[Tuple[SeatLayout, List[Passenger]]]:
        """
        Find available seats for a trip.

        Args:
            selected_trip (Trip): The selected trip
            process_id (int): Process ID for logging

        Returns:
            Optional[Tuple[List[Seat], List[Passenger]]]: Tuple of selected seats and passengers if successful, None otherwise
        """
        # Check if seats are already reserved
        if self._is_reserved.value:
            logger.debug(
                f"Process {process_id}: Seats already reserved by another process"
            )
            raise SeatAlreadyReservedException()

        # Get seat layout and prepare passengers
        seat_layout, passengers = await asyncio.gather(
            self.trip_repository.get_seat_layout(
                selected_trip.trip_id, selected_trip.trip_route_id
            ),
            self._prepare_passengers_async(),
        )

        return seat_layout, passengers

    async def dummy_reserve_seats(
        self,
        selected_trip: Trip,
        selected_seats: List[Seat],
        passengers: List[Passenger],
        process_id: int,
    ) -> Optional[Dict]:
        """
        Dummy reserve seats for a trip.
        """
        return True

    async def reserve_seats(
        self,
        selected_trip: Trip,
        selected_seats: List[Seat],
        passengers: List[Passenger],
        process_id: int,
    ) -> Optional[Dict]:
        """
        Reserve the selected seats for a trip.

        Args:
            selected_trip (Trip): The selected trip
            selected_seats (List[Seat]): List of seats to reserve
            passengers (List[Passenger]): List of passengers
            process_id (int): Process ID for logging

        Returns:
            Optional[Dict]: Dictionary containing reservation data if successful, None otherwise
        """
        # with self._reservation_lock:
        # Double check if seats are still not reserved
        if self._is_reserved.value:
            logger.debug(f"Process {process_id}: Seats were already reserved")
            return None

        logger.debug(f"Process {process_id}: Acquired reservation lock")
        # Reserve seats
        await self.seat_service.reserve_seats(
            selected_seats, selected_trip.trip_route_id
        )
        # Mark as reserved
        self._is_reserved.value = True
        logger.debug(f"Process {process_id}: Released reservation lock")

        # Return reservation data for OTP verification
        return {
            "selected_seats": selected_seats,
            "passengers": passengers,
            "trip": selected_trip,
            "ticket_ids": [seat.ticket_id for seat in selected_seats],
        }

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

        logger.debug("\nPassenger Information:")
        logger.debug(self.passenger_service.get_passenger_summary(passengers))

        return passengers
