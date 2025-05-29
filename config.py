import os
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class BookingConfig:
    """Configuration for the railway booking system."""

    # Authentication
    auth_token_file: str = "auth_token.txt"
    mobile_number: str = "PHONE_NUMBER"
    password: str = "PASSWORD"

    seat_class: str = "SNIGDHA"

    auto_select_train: bool = False
 
    # Passenger details
    passenger_names: List[str] = None
    passenger_email: str = "EMAIL"
    passenger_mobile: str = "PHONE_NUMBER"
    passenger_genders: List[str] = None
    passenger_types: List[str] = None

    # Payment details
    is_bkash_online: bool = True
    selected_mobile_transaction: int = 1

    # Retry settings
    max_retry_attempts: int = 3

    # Output settings
    save_booking_info: bool = True
    booking_info_dir: str = "booking_info"

    # Cache settings
    use_search_cache: bool = True
    cache_dir: str = "cache"

    def __post_init__(self):
        """Set default values for lists if not provided."""
        if self.passenger_names is None:
            self.passenger_names = [ "PASSENGER_NAME_1","PASSENGER_NAME_2"]

        if self.passenger_genders is None:
            self.passenger_genders = ["female", "male"]

        if self.passenger_types is None:
            self.passenger_types = ["Adult", "Adult"]

    @property
    def auth_token(self) -> Optional[str]:
        """Get auth token from file if it exists."""
        try:
            with open(self.auth_token_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def save_auth_token(self, token: str) -> None:
        """Save auth token to file."""
        with open(self.auth_token_file, "w") as f:
            f.write(token)

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        os.makedirs(self.booking_info_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def clean_auth_token(self) -> None:
        """Clean auth token from file."""
        if os.path.exists(self.auth_token_file):
            os.remove(self.auth_token_file)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BookingConfig":
        """Create config from dictionary."""
        return cls(**data)
