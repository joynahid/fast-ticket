from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models import (
    Trip,
    SeatLayout,
    Passenger,
    BookingRequest,
    BookingData,
    BookingResult,
    SearchCriteria,
    AuthenticationToken,
    ApiResponse,
    Seat,
)


class AuthenticationService(ABC):
    """Abstract authentication service."""

    @abstractmethod
    async def login(self, mobile_number: str, password: str) -> AuthenticationToken:
        """Login and get authentication token."""
        pass

    @abstractmethod
    def get_current_token(self) -> Optional[str]:
        """Get current authentication token."""
        pass

    @abstractmethod
    def set_token(self, token: str) -> None:
        """Set authentication token."""
        pass


class TripRepository(ABC):
    """Abstract repository for trip operations."""

    @abstractmethod
    async def search_trips(self, criteria: SearchCriteria) -> List[Trip]:
        """Search for trips based on criteria."""
        pass

    @abstractmethod
    async def get_seat_layout(self, trip_id: int, trip_route_id: int) -> SeatLayout:
        """Get seat layout for a trip."""
        pass


class SeatService(ABC):
    """Abstract service for seat operations."""

    @abstractmethod
    async def reserve_seats(self, seats: List[Seat], trip_route_id: int) -> bool:
        """Reserve the selected seats."""
        pass


class BookingService(ABC):
    """Abstract service for booking operations."""

    @abstractmethod
    async def create_booking_data(
        self, request: BookingRequest, otp: str
    ) -> BookingData:
        """Create booking data from request."""
        pass

    @abstractmethod
    async def submit_booking(self, booking_data: BookingData) -> BookingResult:
        """Submit booking to the API."""
        pass

    @abstractmethod
    async def verify_otp(
        self, trip_id: int, trip_route_id: int, ticket_ids: List[int], otp: str
    ) -> bool:
        """Verify OTP for booking."""
        pass


class CacheService(ABC):
    """Abstract cache service."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    def clear(self, key: str) -> None:
        """Clear specific cache key."""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all cache."""
        pass


class StorageService(ABC):
    """Abstract storage service."""

    @abstractmethod
    def save_booking_info(
        self, booking_data: BookingData, confirmation_response: Dict[str, Any]
    ) -> str:
        """Save booking information and return file path."""
        pass

    @abstractmethod
    def load_booking_info(self, file_path: str) -> Dict[str, Any]:
        """Load booking information from file."""
        pass


class PassengerService(ABC):
    """Abstract service for passenger operations."""

    @abstractmethod
    def validate_passengers(self, passengers: List[Passenger]) -> bool:
        """Validate passenger information."""
        pass

    @abstractmethod
    def prepare_passenger_data(
        self, passengers: List[Passenger], num_tickets: int
    ) -> Dict[str, List[str]]:
        """Prepare passenger data for booking API."""
        pass


class ApiClient(ABC):
    """Abstract API client."""

    @abstractmethod
    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        """Make HTTP request to API."""
        pass
