import asyncio
from typing import List
from abstractions import SeatService
from business.exception import ReservationFailedException
from models import Seat
from infrastructure.api_client import RailwayApiClient
import logging

# Configure logging
logger = logging.getLogger("seat_service")


class RailwaySeatService(SeatService):
    """Railway seat service implementation."""

    def __init__(self, api_client: RailwayApiClient):
        """
        Initialize the seat service.

        Args:
            api_client (RailwayApiClient): API client for making requests
        """
        self.api_client = api_client

    async def reserve_seats(self, seats: List[Seat], trip_route_id: int) -> bool:
        """
        Reserve the selected seats.

        Args:
            seats (List[Seat]): Seats to reserve
            trip_route_id (int): Trip route ID

        Returns:
            bool: True if all seats reserved successfully

        Raises:
            Exception: If reservation fails
        """
        logger.debug(f"Reserving {len(seats)} seat(s)...")

        # Reserve all seats concurrently
        reservation_tasks = [
            self.api_client.reserve_seat(seat.ticket_id, trip_route_id)
            for seat in seats
        ]

        responses = await asyncio.gather(*reservation_tasks)

        # Check if all reservations were successful
        failed_reservations = []
        for i, response in enumerate(responses):
            if not response.success:
                failed_reservations.append(
                    f"Seat {seats[i].seat_number}: {response.error_message}"
                )

        if failed_reservations:
            raise ReservationFailedException(responses[0])

        for response in responses:
            logger.debug(f"Successfully reserved a seat. Response: {response.data}")
        return True
