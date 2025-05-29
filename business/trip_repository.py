from typing import List, Dict, Any
from abstractions import TripRepository, CacheService
from models import Trip, SeatLayout, SearchCriteria, BoardingPoint, Seat
from infrastructure.api_client import RailwayApiClient
from utils import format_journey_date
from business.exception import (
    MultipleOrderAttemptException,
    OrderLimitExceededForTheDayException,
    UnauthorizedException,
)
import logging

# Configure logging
logger = logging.getLogger("trip_repository")


class RailwayTripRepository(TripRepository):
    """Railway trip repository implementation."""

    def __init__(self, api_client: RailwayApiClient, cache_service: CacheService):
        """
        Initialize the trip repository.

        Args:
            api_client (RailwayApiClient): API client for making requests
            cache_service (CacheService): Cache service for storing/retrieving data
        """
        self.api_client = api_client
        self.cache_service = cache_service

    async def search_trips(self, criteria: SearchCriteria) -> List[Trip]:
        """
        Search for trips based on criteria.

        Args:
            criteria (SearchCriteria): Search criteria

        Returns:
            List[Trip]: List of available trips

        Raises:
            Exception: If search fails
        """
        # Format journey date
        formatted_date = format_journey_date(criteria.journey_date)

        # Try to get from cache first
        cache_key = self.cache_service.generate_search_key(
            criteria.from_city, criteria.to_city, formatted_date, criteria.seat_class
        )

        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            return self._parse_trip_data(cached_result, criteria.seat_class)

        # Fetch from API
        logger.debug(
            f"Searching for trips from {criteria.from_city} to {criteria.to_city} "
            f"on {formatted_date} ({criteria.seat_class} class)..."
        )

        response = await self.api_client.search_trips_v2(
            from_city=criteria.from_city,
            to_city=criteria.to_city,
            date_of_journey=formatted_date,
            seat_class=criteria.seat_class,
        )

        if not response.success:
            raise Exception(f"Search failed: {response.error_message}")

        # Cache the result
        self.cache_service.set(cache_key, response.data)

        return self._parse_trip_data(response.data, criteria.seat_class)

    async def get_seat_layout(self, trip_id: int, trip_route_id: int) -> SeatLayout:
        """
        Get seat layout for a trip.

        Args:
            trip_id (int): Trip ID
            trip_route_id (int): Trip route ID

        Returns:
            SeatLayout: Seat layout information

        Raises:
            Exception: If retrieval fails
        """
        logger.debug(
            f"Fetching seat layout for trip {trip_id} and trip route {trip_route_id}..."
        )

        response = await self.api_client.get_seat_layout(
            str(trip_id), str(trip_route_id)
        )

        if not response.success:
            if response.status_code == 401 or response.status_code == 403:
                raise UnauthorizedException(response)

            messages = response.data.get("error", {}).get("messages", {})
            messages_str = str(messages).lower()

            if (
                response.status_code == 422
                and isinstance(response.data, dict)
                and "orderlimitexceeded" in messages_str
            ):
                raise OrderLimitExceededForTheDayException(response)
            elif (
                response.status_code == 422
                and isinstance(response.data, dict)
                and "multiple order attempt" in messages_str
            ):
                raise MultipleOrderAttemptException(response)
            else:
                raise Exception(f"Failed to get seat layout: {response.error_message}")

        return self._parse_seat_layout(response.data, trip_id, trip_route_id)

    def _parse_trip_data(
        self, search_data: Dict[str, Any], seat_class: str
    ) -> List[Trip]:
        """
        Parse trip information from search results.

        Args:
            search_data (Dict[str, Any]): Raw search data from API
            seat_class (str): Seat class to filter by

        Returns:
            List[Trip]: Parsed trip information
        """
        trips = []

        if (
            not search_data
            or not search_data.get("data")
            or not search_data["data"].get("trains")
        ):
            logger.debug("No trains found in search results")
            return trips

        for train in search_data["data"]["trains"]:
            train_name = train["trip_number"]
            departure_time = train["departure_date_time"]
            arrival_time = train["arrival_date_time"]
            travel_time = train["travel_time"]

            # Find the seat type that matches the requested class
            for seat_type in train["seat_types"]:
                if seat_type["type"] == seat_class:
                    trip_id = seat_type["trip_id"]
                    trip_route_id = seat_type["trip_route_id"]
                    route_id = seat_type["route_id"]
                    fare = seat_type["fare"]
                    vat_amount = seat_type["vat_amount"]
                    total_fare = float(fare) + vat_amount

                    # Parse boarding points
                    boarding_points = []
                    for point in train["boarding_points"]:
                        boarding_points.append(
                            BoardingPoint(
                                id=point["trip_point_id"],
                                name=point["location_name"],
                                time=point["location_time"],
                                date=point["location_date"],
                            )
                        )

                    trips.append(
                        Trip(
                            train_name=train_name,
                            departure_time=departure_time,
                            arrival_time=arrival_time,
                            travel_time=travel_time,
                            trip_id=trip_id,
                            trip_route_id=trip_route_id,
                            route_id=route_id,
                            fare=fare,
                            vat_amount=vat_amount,
                            total_fare=total_fare,
                            boarding_points=boarding_points,
                        )
                    )

                    break  # Found the matching seat class, move to next train

        return trips

    def _parse_seat_layout(
        self, layout_data: Dict[str, Any], trip_id: int, trip_route_id: int
    ) -> SeatLayout:
        """
        Parse seat layout data from API response.

        Args:
            layout_data (Dict[str, Any]): Raw seat layout data from API
            trip_id (int): Trip ID
            trip_route_id (int): Trip route ID

        Returns:
            SeatLayout: Parsed seat layout
        """
        return SeatLayout.from_dict(layout_data['data'])
