import time
import logging
from typing import Optional, Any
from business.exception import ReservationFailedException, SeatAlreadyReservedException, UnauthorizedException
from config import BookingConfig
from models import Trip

# Configure logging
logger = logging.getLogger("booking_worker")

def booking_worker(
    process_id: int,
    selected_trip: Trip,
    from_city: Optional[str],
    to_city: Optional[str],
    result_queue: Any,
    config_dict: dict,
    reservation_lock: Any,
    is_reserved: Any,
):
    import signal
    import sys
    import asyncio
    from infrastructure.api_client import RailwayApiClient
    from infrastructure.cache_service import FileCacheService
    from application.seat_reservation_controller import SeatReservationController

    def handle_interrupt(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_interrupt)

    async def process_booking():
        try:
            config = BookingConfig.from_dict(config_dict)
            api_client = RailwayApiClient(config.auth_token)
            cache_service = FileCacheService(config.cache_dir)
            controller = SeatReservationController(
                api_client, cache_service, config, reservation_lock, is_reserved
            )

            seat_layout, passengers = await controller.find_seat_layout_and_passengers(
                selected_trip,
                process_id,
            )

            selected_seats = seat_layout.find_random_adjacent_seats(
                adjacency=len(passengers)
            )

            if len(selected_seats) == 0:
                logger.error(f"Process {process_id}: No seats found")
                return

            await controller.reserve_seats(
                selected_trip,
                selected_seats,
                passengers,
                process_id,
            )

            result_queue.put(
                {
                    "trip": selected_trip,
                    "ticket_ids": [seat.ticket_id for seat in selected_seats],
                    "process_id": process_id,
                    "selected_seats": selected_seats,
                    "passengers": passengers,
                }
            )
        finally:
            if "api_client" in locals():
                await api_client.close()

    while True:
        try:
            asyncio.run(process_booking())
        except SeatAlreadyReservedException as e:
            logger.debug(f"Process {process_id} error: {e}")
            sys.exit(0)
        except UnauthorizedException as e:
            logger.error(f"Process {process_id} error: {e}")
            sys.exit(0)
        except ReservationFailedException as e:
            logger.error(f"Process {process_id} error: {e}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Process {process_id} general exception: {e}", exc_info=True)
            sys.exit(0)
        time.sleep(0.1)
