import json
import os
from datetime import datetime
from typing import Dict, Any
from abstractions import StorageService
from models import BookingData
import logging

# Configure logging
logger = logging.getLogger("storage_service")

class FileStorageService(StorageService):
    """File-based storage service implementation."""

    def __init__(self, storage_dir: str):
        """
        Initialize the storage service.

        Args:
            storage_dir (str): Directory for storing files
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save_booking_info(
        self, 
        booking_data: BookingData, 
        confirmation_response: Dict[str, Any]
    ) -> str:
        """
        Save booking information to a file.

        Args:
            booking_data (BookingData): The booking data
            confirmation_response (Dict[str, Any]): The confirmation response from the API

        Returns:
            str: File path where the booking information was saved
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"booking_{timestamp}.json"
        file_path = os.path.join(self.storage_dir, filename)

        # Combine data
        data = {
            "booking_request": self._booking_data_to_dict(booking_data),
            "confirmation_response": confirmation_response,
            "booking_time": timestamp,
            "passengers": [
                {
                    "name": name,
                    "email": booking_data.pemail,
                    "mobile": booking_data.pmobile,
                    "gender": gender,
                    "type": ptype,
                }
                for name, gender, ptype in zip(
                    booking_data.pname,
                    booking_data.gender,
                    booking_data.passengerType,
                )
            ],
            "journey": {
                "from": booking_data.from_city,
                "to": booking_data.to_city,
                "date": booking_data.date_of_journey,
                "seat_class": booking_data.seat_class,
                "ticket_ids": booking_data.ticket_ids,
            },
        }

        # Save to file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Booking information saved to {file_path}")
        return file_path

    def load_booking_info(self, file_path: str) -> Dict[str, Any]:
        """
        Load booking information from file.

        Args:
            file_path (str): Path to the booking info file

        Returns:
            Dict[str, Any]: Loaded booking information

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        with open(file_path, "r") as f:
            return json.load(f)

    def _booking_data_to_dict(self, booking_data: BookingData) -> Dict[str, Any]:
        """
        Convert BookingData dataclass to dictionary.

        Args:
            booking_data (BookingData): Booking data to convert

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "is_bkash_online": booking_data.is_bkash_online,
            "boarding_point_id": booking_data.boarding_point_id,
            "contactperson": booking_data.contactperson,
            "from_city": booking_data.from_city,
            "to_city": booking_data.to_city,
            "date_of_journey": booking_data.date_of_journey,
            "seat_class": booking_data.seat_class,
            "gender": booking_data.gender,
            "page": booking_data.page,
            "passengerType": booking_data.passengerType,
            "pemail": booking_data.pemail,
            "pmobile": booking_data.pmobile,
            "pname": booking_data.pname,
            "ppassport": booking_data.ppassport,
            "priyojon_order_id": booking_data.priyojon_order_id,
            "referral_mobile_number": booking_data.referral_mobile_number,
            "ticket_ids": booking_data.ticket_ids,
            "trip_id": booking_data.trip_id,
            "trip_route_id": booking_data.trip_route_id,
            "isShohoz": booking_data.isShohoz,
            "enable_sms_alert": booking_data.enable_sms_alert,
            "first_name": booking_data.first_name,
            "middle_name": booking_data.middle_name,
            "last_name": booking_data.last_name,
            "date_of_birth": booking_data.date_of_birth,
            "nationality": booking_data.nationality,
            "passport_type": booking_data.passport_type,
            "passport_no": booking_data.passport_no,
            "passport_expiry_date": booking_data.passport_expiry_date,
            "visa_type": booking_data.visa_type,
            "visa_no": booking_data.visa_no,
            "visa_issue_place": booking_data.visa_issue_place,
            "visa_issue_date": booking_data.visa_issue_date,
            "visa_expire_date": booking_data.visa_expire_date,
            "otp": booking_data.otp,
            "selected_mobile_transaction": booking_data.selected_mobile_transaction,
        } 