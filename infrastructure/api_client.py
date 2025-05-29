import json
import aiohttp
from typing import Dict, Any, Optional
from abstractions import ApiClient
from models import ApiResponse
import asyncio
import logging

# Configure logging
logger = logging.getLogger("api_client")

class RailwayApiClient(ApiClient):
    """Implementation of API client for Bangladesh Railway e-ticket API."""

    BASE_URL = "https://railspaapi.shohoz.com/v1.0/web"
    _session: Optional[aiohttp.ClientSession] = None
    _session_lock = asyncio.Lock()

    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the API client.

        Args:
            auth_token (str, optional): The authentication token for API requests
        """
        self.auth_token = auth_token
        self.headers = {
            "sec-ch-ua-platform": "macOS",
            "Referer": "https://eticket.railway.gov.bd/",
            "sec-ch-ua": '"Not:A-Brand";v="24", "Chromium";v="134"',
            "sec-ch-ua-mobile": "?0",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "DNT": "1",
            "Content-Type": "application/json",
        }

        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    async def __aenter__(self):
        """Async context manager entry."""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session with connection pooling."""
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    # Configure connection pooling
                    connector = aiohttp.TCPConnector(
                        limit=10,  # Maximum number of concurrent connections
                        ttl_dns_cache=300,  # DNS cache TTL in seconds
                        force_close=False,  # Keep connections alive
                        enable_cleanup_closed=True,  # Clean up closed connections
                    )
                    timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout
                    self._session = aiohttp.ClientSession(
                        connector=connector, timeout=timeout, headers=self.headers
                    )
        return self._session

    async def close(self):
        """Close the session if it exists."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def update_auth_token(self, auth_token: str) -> None:
        """
        Update the authentication token.

        Args:
            auth_token (str): The new authentication token
        """
        self.auth_token = auth_token
        self.headers["Authorization"] = f"Bearer {auth_token}"
        # Update session headers if session exists
        if self._session and not self._session.closed:
            self._session.headers.update({"Authorization": f"Bearer {auth_token}"})

    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        """
        Make an HTTP request to the API.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint path
            params (dict, optional): Query parameters
            data (dict, optional): Request body for POST requests

        Returns:
            ApiResponse: Structured response from the API
        """
        url = f"{self.BASE_URL}/{endpoint}"
        session = await self._get_session()

        try:
            request_kwargs = {"params": params}
            if data and method.upper() in ["POST", "PUT", "PATCH"]:
                request_kwargs["json"] = data

            async with session.request(method, url, **request_kwargs) as response:
                try:
                    response_data = await response.json()
                except Exception as e:
                    logger.error(f"Error parsing response: {e}")
                    response_data = await response.text()

                ar = ApiResponse(
                    success=response.status == 200,
                    error_message=str(response_data)
                    if response.status != 200
                    else None,
                    status_code=response.status,
                    data=response_data
                )
                if response.status != 200:
                    logger.error(f"API Error: {response.status} - {await response.text()}")
                return ar

        except Exception as e:
            return ApiResponse(success=False, error_message=str(e), status_code=None, data=None, exc=e)

    async def login(self, mobile_number: str, password: str) -> ApiResponse:
        """
        Login to the API and get an authentication token.

        Args:
            mobile_number (str): The mobile number for login
            password (str): The password for login

        Returns:
            ApiResponse: Response containing authentication token
        """
        data = {"mobile_number": mobile_number, "password": password}
        return await self.make_request("POST", "auth/sign-in", data=data)

    async def search_trips_v2(
        self, from_city: str, to_city: str, date_of_journey: str, seat_class: str
    ) -> ApiResponse:
        """
        Search for available trips between cities on a specific date using the v2 API.

        Args:
            from_city (str): Origin city name (e.g., 'Dhaka')
            to_city (str): Destination city name (e.g., 'Rajshahi')
            date_of_journey (str): Date in DD-MMM-YYYY format (e.g., '25-Mar-2025')
            seat_class (str): Class of seat (e.g., 'SNIGDHA')

        Returns:
            ApiResponse: Response containing available trips
        """
        params = {
            "from_city": from_city,
            "to_city": to_city,
            "date_of_journey": date_of_journey,
            "seat_class": seat_class,
        }
        return await self.make_request("GET", "bookings/search-trips-v2", params=params)

    async def get_seat_layout(self, trip_id: str, trip_route_id: str) -> ApiResponse:
        """
        Fetch seat layout information for a specific trip.

        Args:
            trip_id (str): The ID of the trip
            trip_route_id (str): The ID of the trip route

        Returns:
            ApiResponse: Response containing seat layout information
        """
        params = {"trip_id": trip_id, "trip_route_id": trip_route_id}
        return await self.make_request("GET", "bookings/seat-layout", params=params)

    async def reserve_seat(self, ticket_id: int, route_id: int) -> ApiResponse:
        """
        Reserve a seat for a specific ticket and route.

        Args:
            ticket_id (int): The ID of the ticket to reserve
            route_id (int): The ID of the route

        Returns:
            ApiResponse: Response containing reservation information
        """
        data = {"ticket_id": ticket_id, "route_id": route_id}
        logger.debug(f"ticket_id: {ticket_id}, route_id: {route_id}")
        return await self.make_request("PATCH", "bookings/reserve-seat", data=data)

    async def get_passenger_details(
        self, trip_id: int, trip_route_id: int, ticket_ids: list[int]
    ) -> ApiResponse:
        """
        Get passenger details after reserving a seat.

        Args:
            trip_id (int): The ID of the trip
            trip_route_id (int): The ID of the trip route
            ticket_ids (list[int]): List of ticket IDs

        Returns:
            ApiResponse: Response containing passenger details
        """
        data = {
            "trip_id": trip_id,
            "trip_route_id": trip_route_id,
            "ticket_ids": ticket_ids,
        }
        return await self.make_request("POST", "bookings/passenger-details", data=data)

    async def verify_otp(
        self, trip_id: int, trip_route_id: int, ticket_ids: list[int], otp: str
    ) -> ApiResponse:
        """
        Verify OTP for ticket booking.

        Args:
            trip_id (int): The ID of the trip
            trip_route_id (int): The ID of the trip route
            ticket_ids (list[int]): List of ticket IDs
            otp (str): OTP received via SMS

        Returns:
            ApiResponse: Response containing verification result
        """
        data = {
            "trip_id": trip_id,
            "trip_route_id": trip_route_id,
            "ticket_ids": ticket_ids,
            "otp": otp,
        }
        return await self.make_request("POST", "bookings/verify-otp", data=data)

    async def confirm_booking(self, booking_data: Dict[str, Any]) -> ApiResponse:
        """
        Confirm the ticket booking.

        Args:
            booking_data (Dict[str, Any]): Complete booking data including passenger details

        Returns:
            ApiResponse: Response containing confirmation result
        """
        return await self.make_request("PATCH", "bookings/confirm", data=booking_data)
