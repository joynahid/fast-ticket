from dataclasses import dataclass, field
from random import choice
from typing import Iterator, List, Optional, Dict, Any, Tuple
from datetime import datetime
import prettytable
import logging

# Configure logging
logger = logging.getLogger("models")


@dataclass
class BoardingPoint:
    """Represents a boarding point for a train."""

    id: int
    name: str
    time: str
    date: str


@dataclass
class Trip:
    """Represents a train trip."""

    train_name: str
    departure_time: str
    arrival_time: str
    travel_time: str
    trip_id: int
    trip_route_id: int
    route_id: int
    fare: float
    vat_amount: float
    total_fare: float
    boarding_points: List[BoardingPoint]

    def find_boarding_point(self, from_city: str) -> Optional[BoardingPoint]:
        boarding_point = next(
            (bp for bp in self.boarding_points if bp.name.lower().startswith(from_city.lower())),
            None,
        )

        if not boarding_point:
            # return the first boarding point
            return self.boarding_points[0]

        return boarding_point


@dataclass
class Seat:
    """Represents a seat in a train."""

    seat_number: str
    ticket_id: int
    is_available: bool
    is_hidden: bool
    ticket_type: int

    def is_aisle(self) -> bool:
        return self.seat_number == ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Seat":
        return cls(
            seat_number=data["seat_number"],
            ticket_id=data["ticket_id"],
            is_available=data["seat_availability"] == 1,
            is_hidden=data["isHidden"],
            ticket_type=data["ticket_type"],
        )


@dataclass
class Floor:
    """Represents a floor in a train."""

    floor_number: int
    seats: List[List[Seat]]
    floor_name: str
    seat_availability: bool

    @property
    def available_seats(self) -> int:
        return sum(1 for row in self.seats for seat in row if seat.is_available)

    def find_adjacent_seats_pairs(
        self, adjacency: int = 2
    ) -> Iterator[Tuple[Seat, ...]]:
        """Yields tuples of available seats in a row.

        Args:
            adjacency (int): Number of seats to find (default: 2)

        Yields:
            Tuple[Seat, ...]: Tuples of available seats
        """
        for row in self.seats:
            available_seats = []

            # First collect all available seats in the row
            for seat in row:
                if not seat.is_aisle() and seat.is_available:
                    available_seats.append(seat)

            # Then yield groups of N seats
            for i in range(len(available_seats) - adjacency + 1):
                yield tuple(available_seats[i : i + adjacency])


@dataclass
class SeatLayout:
    """Represents the complete seat layout of a train."""

    trip_id: int = field(default=-1)
    trip_route_id: int = field(default=-1)
    floors: List[Floor] = field(default_factory=list)

    @property
    def available_floors(self) -> List[Floor]:
        return [floor for floor in self.floors if floor.seat_availability]

    def formatted_seats(self) -> Tuple[List[Seat], List[Seat]]:
        # Find seat number 0
        mid_seat = next(
            (idx for idx, seat in enumerate(self.seats) if seat.is_empty_space()), None
        )
        if mid_seat:
            first_block = self.seats[0 : mid_seat - 1]
            second_block = self.seats[mid_seat + 1 :]
            return first_block, second_block
        return [], []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeatLayout":
        floors = []
        for floor in data["seatLayout"]:
            rows = []
            for row in floor["layout"]:
                seats = []
                for seat in row:
                    seats.append(Seat.from_dict(seat))
                rows.append(seats)
            floors.append(
                Floor(
                    floor_number=floor["seat_floor"],
                    seats=rows,
                    floor_name=floor["floor_name"],
                    seat_availability=floor["seat_availability"],
                )
            )

        return cls(
            floors=floors,
        )

    def find_random_adjacent_seats(self, adjacency: int = 1) -> Tuple[Seat, ...]:
        try:
            # Random floor
            floor = choice(self.available_floors)
            return choice(list(floor.find_adjacent_seats_pairs(adjacency=adjacency)))
        except IndexError:
            logger.debug("No available seats found")
            return []

    def summary(self) -> str:
        table = prettytable.PrettyTable()
        table.field_names = ["Floor", "Rows", "Seats", "Available Seats"]
        for floor in self.floors:
            table.add_row(
                [
                    floor.floor_name,
                    len(floor.seats),
                    len(floor.seats[0]),
                    floor.available_seats,
                ]
            )
        logger.debug(table.get_string())
        return table.get_string()


@dataclass
class Passenger:
    """Represents a passenger."""

    name: str
    email: str
    mobile: str
    gender: str  # "male" or "female"
    passenger_type: str  # "Adult" or "Child"


@dataclass
class SearchCriteria:
    """Criteria for searching trips."""

    from_city: str
    to_city: str
    journey_date: str
    seat_class: str
    preferred_train: Optional[str] = None


@dataclass
class BookingRequest:
    """Request data for booking tickets."""

    trip: Trip
    passengers: List[Passenger]
    selected_seats: List[Seat]
    boarding_point: BoardingPoint
    num_seats: int
    from_city: str
    to_city: str


@dataclass
class BookingData:
    """Complete booking data for API submission."""

    is_bkash_online: bool
    boarding_point_id: int
    contactperson: int
    from_city: str
    to_city: str
    date_of_journey: str
    seat_class: str
    gender: List[str]
    page: List[str]
    passengerType: List[str]
    pemail: str
    pmobile: str
    pname: List[str]
    ppassport: List[str]
    priyojon_order_id: Optional[str]
    referral_mobile_number: Optional[str]
    ticket_ids: List[int]
    trip_id: int
    trip_route_id: int
    isShohoz: int
    enable_sms_alert: int
    first_name: List[Optional[str]]
    middle_name: List[Optional[str]]
    last_name: List[Optional[str]]
    date_of_birth: List[Optional[str]]
    nationality: List[Optional[str]]
    passport_type: List[Optional[str]]
    passport_no: List[Optional[str]]
    passport_expiry_date: List[Optional[str]]
    visa_type: List[Optional[str]]
    visa_no: List[Optional[str]]
    visa_issue_place: List[Optional[str]]
    visa_issue_date: List[Optional[str]]
    visa_expire_date: List[Optional[str]]
    otp: str
    selected_mobile_transaction: int


@dataclass
class BookingResult:
    """Result of a booking operation."""

    success: bool
    booking_id: Optional[str] = None
    error_message: Optional[str] = None
    booking_data: Optional[BookingData] = None
    confirmation_response: Optional[Dict[str, Any]] = None


@dataclass
class AuthenticationToken:
    """Authentication token with metadata."""

    token: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    mobile_number: Optional[str] = None


@dataclass
class ApiResponse:
    """Generic API response wrapper."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    exc: Optional[Exception] = None
