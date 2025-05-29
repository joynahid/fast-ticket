from typing import List, Dict, Any
import logging
from abstractions import BookingService
from business.exception import OtpVerificationFailedException
from models import BookingRequest, BookingData, BookingResult, Passenger
from infrastructure.api_client import RailwayApiClient
from config import BookingConfig

# Configure logging
logger = logging.getLogger("booking_service")


class RailwayBookingService(BookingService):
    """Railway booking service implementation."""

    def __init__(self, api_client: RailwayApiClient, config: BookingConfig):
        """
        Initialize the booking service.

        Args:
            api_client (RailwayApiClient): API client for making requests
            config (BookingConfig): Configuration object
        """
        self.api_client = api_client
        self.config = config

    async def create_booking_data(
        self, request: BookingRequest, otp: str
    ) -> BookingData:
        """
        Create booking data from request.

        Args:
            request (BookingRequest): Booking request
            otp (str): OTP for verification

        Returns:
            BookingData: Complete booking data for API submission
        """
        num_tickets = len(request.selected_seats)

        # Create empty arrays for required fields
        empty_array = [None] * num_tickets
        empty_string_array = [""] * num_tickets

        # Adjust passenger data to match number of tickets
        passenger_names = self._adjust_list(
            [p.name for p in request.passengers], num_tickets, "Passenger"
        )
        passenger_genders = self._adjust_list(
            [p.gender for p in request.passengers], num_tickets, "male"
        )
        passenger_types = self._adjust_list(
            [p.passenger_type for p in request.passengers], num_tickets, "Adult"
        )

        # Get contact info from first passenger
        contact_passenger = request.passengers[0]

        booking_data = BookingData(
            is_bkash_online=self.config.is_bkash_online,
            boarding_point_id=request.boarding_point.id,
            contactperson=0,
            from_city=request.from_city,
            to_city=request.to_city,
            date_of_journey=request.boarding_point.date,
            seat_class=self.config.seat_class,
            gender=passenger_genders,
            page=empty_string_array,
            passengerType=passenger_types,
            pemail=contact_passenger.email,
            pmobile=contact_passenger.mobile,
            pname=passenger_names,
            ppassport=empty_string_array,
            priyojon_order_id=None,
            referral_mobile_number=None,
            ticket_ids=[seat.ticket_id for seat in request.selected_seats],
            trip_id=request.trip.trip_id,
            trip_route_id=request.trip.trip_route_id,
            isShohoz=0,
            enable_sms_alert=0,
            first_name=empty_array,
            middle_name=empty_array,
            last_name=empty_array,
            date_of_birth=empty_array,
            nationality=empty_array,
            passport_type=empty_array,
            passport_no=empty_array,
            passport_expiry_date=empty_array,
            visa_type=empty_array,
            visa_no=empty_array,
            visa_issue_place=empty_array,
            visa_issue_date=empty_array,
            visa_expire_date=empty_array,
            otp=otp,
            selected_mobile_transaction=self.config.selected_mobile_transaction,
        )

        return booking_data

    async def submit_booking(self, booking_data: BookingData) -> BookingResult:
        """
        Submit booking to the API.

        Args:
            booking_data (BookingData): Complete booking data

        Returns:
            BookingResult: Result of the booking operation
        """
        logger.info("Confirming booking...")

        # Convert booking data to dictionary for API
        booking_dict = self._booking_data_to_dict(booking_data)

        logger.debug("Booking Data:")
        import json

        logger.debug(json.dumps(booking_dict, indent=2))

        response = await self.api_client.confirm_booking(booking_dict)

        if response.success:
            return BookingResult(
                success=True,
                booking_data=booking_data,
                confirmation_response=response.data,
            )
        else:
            return BookingResult(
                success=False,
                error_message=response.error_message,
                booking_data=booking_data,
            )

    async def verify_otp(
        self, trip_id: int, trip_route_id: int, ticket_ids: List[int], otp: str
    ) -> bool:
        """
        Verify OTP for booking.

        Args:
            trip_id (int): Trip ID
            trip_route_id (int): Trip route ID
            ticket_ids (List[int]): List of ticket IDs
            otp (str): OTP to verify

        Returns:
            bool: True if OTP verification successful

        Raises:
            Exception: If OTP verification fails
        """
        logger.info("Verifying OTP...")

        response = await self.api_client.verify_otp(
            trip_id, trip_route_id, ticket_ids, otp
        )

        if not response.success:
            raise OtpVerificationFailedException(response)

        logger.info("OTP verification successful")
        return True

    async def get_passenger_details(
        self, trip_id: int, trip_route_id: int, ticket_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Get passenger details after seat reservation.

        Args:
            trip_id (int): Trip ID
            trip_route_id (int): Trip route ID
            ticket_ids (List[int]): List of ticket IDs

        Returns:
            Dict[str, Any]: Passenger details response

        Raises:
            Exception: If request fails
        """
        logger.debug("Getting passenger details...")

        response = await self.api_client.get_passenger_details(
            trip_id, trip_route_id, ticket_ids
        )

        if not response.success:
            raise Exception(
                f"Failed to get passenger details: {response.error_message}"
            )

        return response.data

    def _adjust_list(
        self, items: List[str], target_length: int, default_value: str
    ) -> List[str]:
        """
        Adjust list length by padding or truncating.

        Args:
            items (List[str]): List to adjust
            target_length (int): Target length
            default_value (str): Default value for padding

        Returns:
            List[str]: Adjusted list
        """
        if len(items) < target_length:
            return items + [default_value] * (target_length - len(items))
        return items[:target_length]

    def _booking_data_to_dict(self, booking_data: BookingData) -> Dict[str, Any]:
        """
        Convert BookingData to dictionary for API submission.

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
