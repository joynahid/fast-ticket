import pickle
import threading
import traceback
import aiohttp
import asyncio
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

# ============= CONFIGURATION VARIABLES =============
# Authentication
# Set to None to use login credentials instead

try:
    with open("auth_token.txt", "r") as f:
        AUTH_TOKEN = f.read().strip()
except FileNotFoundError:
    AUTH_TOKEN = None

# Login credentials
MOBILE_NUMBER = "XXX"
PASSWORD = "XXX"

# Journey details
FROM_CITY = "Dhaka"
TO_CITY = "Rajshahi"
# Format: DD-MMM-YYYY (e.g., "25-Mar-2025")
# Set to "auto" to automatically search for the next available date
# Set to "auto+N" to search N days from today (e.g., "auto+7" for 7 days from today)
JOURNEY_DATE = "28-Mar-2025"
# Available options: "SNIGDHA", "S_CHAIR", "AC_S", etc.
SEAT_CLASS = "SNIGDHA"
# Set to None to select automatically, or specify a train name to filter
# Example: "BANALATA EXPRESS (791)"
PREFERRED_TRAIN = None
# Set to True to automatically select the first available train without prompting
AUTO_SELECT_TRAIN = False
# Number of seats to book (1 or 2)
NUM_SEATS_TO_BOOK = 1
# Set to True to look for adjacent seats (only applicable when NUM_SEATS_TO_BOOK = 2)
ADJACENT_SEATS = True

# Passenger details
# For multiple passengers, provide a list of names
PASSENGER_NAMES = ["ABDUS SALAM"]
# Common contact information for all passengers
PASSENGER_EMAIL = "xxx@gmail.com"
PASSENGER_MOBILE = MOBILE_NUMBER
# For multiple passengers, provide a list of genders
PASSENGER_GENDERS = ["male"]  # "male" or "female"
# For multiple passengers, provide a list of passenger types
PASSENGER_TYPES = ["Adult"]  # "Adult" or "Child"

# Payment details
IS_BKASH_ONLINE = True
SELECTED_MOBILE_TRANSACTION = 1

# Retry settings
MAX_RETRY_ATTEMPTS = 10000

# Output settings
SAVE_BOOKING_INFO = True
BOOKING_INFO_DIR = "booking_info"
# Cache settings
USE_SEARCH_CACHE = True  # Set to False to always fetch fresh search results
CACHE_DIR = "cache"  # Directory for storing cache files
# ===================================================


def format_journey_date(date_str: str) -> str:
    """
    Format the journey date string according to the required format (DD-MMM-YYYY).

    Args:
        date_str (str): Date string or special format like "auto" or "auto+N"

    Returns:
        str: Formatted date string
    """
    if date_str.lower().startswith("auto"):
        # Parse days offset if specified (e.g., "auto+7")
        days_offset = 0
        if "+" in date_str:
            try:
                days_offset = int(date_str.split("+")[1])
            except ValueError:
                print(f"Invalid auto date format: {date_str}. Using today + 0 days.")

        # Calculate the target date
        target_date = datetime.now() + timedelta(days=days_offset)
        return target_date.strftime("%d-%b-%Y")

    return date_str


def save_booking_info(
    booking_data: Dict[str, Any], confirmation_response: Dict[str, Any]
) -> None:
    """
    Save booking information to a file.

    Args:
        booking_data (Dict[str, Any]): The booking data sent to the API
        confirmation_response (Dict[str, Any]): The confirmation response from the API
    """
    if not SAVE_BOOKING_INFO:
        return

    # Create directory if it doesn't exist
    if not os.path.exists(BOOKING_INFO_DIR):
        os.makedirs(BOOKING_INFO_DIR)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{BOOKING_INFO_DIR}/booking_{timestamp}.json"

    # Combine data
    data = {
        "booking_request": booking_data,
        "confirmation_response": confirmation_response,
        "booking_time": timestamp,
        "passengers": [
            {
                "name": name,
                "email": PASSENGER_EMAIL,
                "mobile": PASSENGER_MOBILE,
                "gender": gender,
                "type": ptype,
            }
            for name, gender, ptype in zip(
                booking_data["pname"],
                booking_data["gender"],
                booking_data["passengerType"],
            )
        ],
        "journey": {
            "from": FROM_CITY,
            "to": TO_CITY,
            "date": booking_data["date_of_journey"],
            "seat_class": SEAT_CLASS,
            "ticket_ids": booking_data["ticket_ids"],
        },
    }

    # Save to file
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nBooking information saved to {filename}")


def create_booking_data(
    trip_id: int,
    trip_route_id: int,
    ticket_ids: List[int],
    boarding_point_id: int,
    journey_date: str,
    otp: str,
) -> Dict[str, Any]:
    """
    Create booking data for the API request based on the number of tickets.

    Args:
        trip_id (int): The ID of the trip
        trip_route_id (int): The ID of the trip route
        ticket_ids (List[int]): List of ticket IDs
        boarding_point_id (int): The ID of the boarding point
        journey_date (str): The date of the journey
        otp (str): The OTP for verification

    Returns:
        Dict[str, Any]: The booking data
    """
    # Ensure we have enough passenger information
    num_tickets = len(ticket_ids)

    # Make sure we have enough passenger names, genders, and types
    passenger_names = (
        PASSENGER_NAMES[:num_tickets]
        if len(PASSENGER_NAMES) >= num_tickets
        else PASSENGER_NAMES + ["Passenger"] * (num_tickets - len(PASSENGER_NAMES))
    )
    passenger_genders = (
        PASSENGER_GENDERS[:num_tickets]
        if len(PASSENGER_GENDERS) >= num_tickets
        else PASSENGER_GENDERS + ["male"] * (num_tickets - len(PASSENGER_GENDERS))
    )
    passenger_types = (
        PASSENGER_TYPES[:num_tickets]
        if len(PASSENGER_TYPES) >= num_tickets
        else PASSENGER_TYPES + ["Adult"] * (num_tickets - len(PASSENGER_TYPES))
    )

    # Create empty arrays for each passenger
    empty_array = [None] * num_tickets
    empty_string_array = [""] * num_tickets

    booking_data = {
        "is_bkash_online": IS_BKASH_ONLINE,
        "boarding_point_id": boarding_point_id,
        "contactperson": 0,
        "from_city": FROM_CITY,
        "to_city": TO_CITY,
        "date_of_journey": journey_date,
        "seat_class": SEAT_CLASS,
        "gender": passenger_genders,
        "page": empty_string_array,
        "passengerType": passenger_types,
        "pemail": PASSENGER_EMAIL,
        "pmobile": PASSENGER_MOBILE,
        "pname": passenger_names,
        "ppassport": empty_string_array,
        "priyojon_order_id": None,
        "referral_mobile_number": None,
        "ticket_ids": ticket_ids,
        "trip_id": trip_id,
        "trip_route_id": trip_route_id,
        "isShohoz": 0,
        "enable_sms_alert": 0,
        "first_name": empty_array,
        "middle_name": empty_array,
        "last_name": empty_array,
        "date_of_birth": empty_array,
        "nationality": empty_array,
        "passport_type": empty_array,
        "passport_no": empty_array,
        "passport_expiry_date": empty_array,
        "visa_type": empty_array,
        "visa_no": empty_array,
        "visa_issue_place": empty_array,
        "visa_issue_date": empty_array,
        "visa_expire_date": empty_array,
        "otp": otp,
        "selected_mobile_transaction": SELECTED_MOBILE_TRANSACTION,
    }

    return booking_data


class RailwayAPIClient:
    """
    A client for interacting with the Bangladesh Railway e-ticket API.
    """

    BASE_URL = "https://railspaapi.shohoz.com/v1.0/web"

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

    def update_auth_token(self, auth_token: str) -> None:
        """
        Update the authentication token.

        Args:
            auth_token (str): The new authentication token
        """
        global AUTH_TOKEN
        self.auth_token = auth_token
        AUTH_TOKEN = auth_token
        self.headers["Authorization"] = f"Bearer {auth_token}"

    async def login(self, mobile_number: str, password: str) -> str:
        """
        Login to the API and get an authentication token.

        Args:
            mobile_number (str): The mobile number for login
            password (str): The password for login

        Returns:
            str: The authentication token
        """
        data = {"mobile_number": mobile_number, "password": password}

        url = f"{self.BASE_URL}/auth/sign-in"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self.headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    auth_token = response_data["data"]["token"]
                    self.update_auth_token(auth_token)
                    print(f"Login successful for {mobile_number}")
                    return auth_token
                else:
                    response_text = await response.text()
                    raise Exception(f"Login Error: {response.status}, {response_text}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint path
            params (dict, optional): Query parameters
            data (dict, optional): Request body for POST requests

        Returns:
            dict: JSON response from the API
        """
        url = f"{self.BASE_URL}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            request_kwargs = {"headers": self.headers, "params": params}

            if data and method.upper() in ["POST", "PUT", "PATCH"]:
                request_kwargs["json"] = data

            async with session.request(method, url, **request_kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    raise Exception(f"API Error: {response.status}, {response_text}")

    async def get_seat_layout(self, trip_id: str, trip_route_id: str) -> Dict[str, Any]:
        """
        Fetch seat layout information for a specific trip.

        Args:
            trip_id (str): The ID of the trip
            trip_route_id (str): The ID of the trip route

        Returns:
            dict: JSON response containing seat layout information
        """
        params = {"trip_id": trip_id, "trip_route_id": trip_route_id}

        return await self._make_request("GET", "bookings/seat-layout", params=params)

    async def search_trips(
        self, from_station: str, to_station: str, journey_date: str
    ) -> Dict[str, Any]:
        """
        Search for available trips between stations on a specific date.

        Args:
            from_station (str): Origin station code
            to_station (str): Destination station code
            journey_date (str): Date in YYYY-MM-DD format

        Returns:
            dict: JSON response containing available trips
        """
        params = {
            "from_station": from_station,
            "to_station": to_station,
            "journey_date": journey_date,
        }

        return await self._make_request("GET", "search", params=params)

    async def search_trips_v2(
        self, from_city: str, to_city: str, date_of_journey: str, seat_class: str
    ) -> Dict[str, Any]:
        """
        Search for available trips between cities on a specific date using the v2 API.

        Args:
            from_city (str): Origin city name (e.g., 'Dhaka')
            to_city (str): Destination city name (e.g., 'Rajshahi')
            date_of_journey (str): Date in DD-MMM-YYYY format (e.g., '25-Mar-2025')
            seat_class (str): Class of seat (e.g., 'SNIGDHA')

        Returns:
            dict: JSON response containing available trips
        """
        params = {
            "from_city": from_city,
            "to_city": to_city,
            "date_of_journey": date_of_journey,
            "seat_class": seat_class,
        }

        return await self._make_request(
            "GET", "bookings/search-trips-v2", params=params
        )

    async def reserve_seat(self, ticket_id: int, route_id: int) -> Dict[str, Any]:
        """
        Reserve a seat for a specific ticket and route.

        Args:
            ticket_id (int): The ID of the ticket to reserve
            route_id (int): The ID of the route

        Returns:
            dict: JSON response containing reservation information
        """
        data = {"ticket_id": ticket_id, "route_id": route_id}

        return await self._make_request("PATCH", "bookings/reserve-seat", data=data)

    async def get_passenger_details(
        self, trip_id: int, trip_route_id: int, ticket_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Get passenger details after reserving a seat.

        Args:
            trip_id (int): The ID of the trip
            trip_route_id (int): The ID of the trip route
            ticket_ids (List[int]): List of ticket IDs

        Returns:
            dict: JSON response containing passenger details
        """
        data = {
            "trip_id": trip_id,
            "trip_route_id": trip_route_id,
            "ticket_ids": ticket_ids,
        }

        return await self._make_request("POST", "bookings/passenger-details", data=data)

    async def verify_otp(
        self, trip_id: int, trip_route_id: int, ticket_ids: List[int], otp: str
    ) -> Dict[str, Any]:
        """
        Verify OTP for ticket booking.

        Args:
            trip_id (int): The ID of the trip
            trip_route_id (int): The ID of the trip route
            ticket_ids (List[int]): List of ticket IDs
            otp (str): OTP received via SMS

        Returns:
            dict: JSON response containing verification result
        """
        data = {
            "trip_id": trip_id,
            "trip_route_id": trip_route_id,
            "ticket_ids": ticket_ids,
            "otp": otp,
        }

        return await self._make_request("POST", "bookings/verify-otp", data=data)

    async def confirm_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Confirm the ticket booking.

        Args:
            booking_data (Dict[str, Any]): Complete booking data including passenger details

        Returns:
            dict: JSON response containing confirmation result
        """
        return await self._make_request("PATCH", "bookings/confirm", data=booking_data)

    # Additional methods can be added here for other API endpoints


def parse_trip_info(
    search_results: Dict[str, Any], seat_class: str = "SNIGDHA"
) -> List[Dict[str, Any]]:
    """
    Parse trip information from search results for a specific seat class.

    Args:
        search_results (Dict[str, Any]): The search results from search_trips_v2
        seat_class (str, optional): The seat class to filter by. Defaults to "SNIGDHA".

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing trip information
    """
    trips_info = []

    if not search_results.get("data") or not search_results["data"].get("trains"):
        print("No trains found in search results")
        return trips_info

    for train in search_results["data"]["trains"]:
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

                # Get boarding point information
                boarding_points = []
                for point in train["boarding_points"]:
                    boarding_points.append(
                        {
                            "id": point["trip_point_id"],
                            "name": point["location_name"],
                            "time": point["location_time"],
                            "date": point["location_date"],
                        }
                    )

                trips_info.append(
                    {
                        "train_name": train_name,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time,
                        "travel_time": travel_time,
                        "trip_id": trip_id,
                        "trip_route_id": trip_route_id,
                        "route_id": route_id,
                        "fare": fare,
                        "vat_amount": vat_amount,
                        "total_fare": total_fare,
                        "boarding_points": boarding_points,
                    }
                )

                break  # Found the matching seat class, move to next train

    return trips_info


def load_from_cache(filename):
    """
    Load data from a cache file if it exists.

    Args:
        filename (str): The filename to load from

    Returns:
        data: The loaded data or None if file doesn't exist or error occurs
    """
    if not os.path.exists(filename):
        return None

    try:
        with open(filename, "rb") as f:
            data = pickle.load(f)
        print(f"Loaded data from cache: {filename}")
        return data
    except (pickle.PickleError, EOFError, Exception) as e:
        print(f"Error loading cache {filename}: {e}")
        return None


def save_to_cache(filename, data):
    """
    Save data to a cache file.

    Args:
        filename (str): The filename to save to
        data: The data to save
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        with open(filename, "wb") as f:
            pickle.dump(data, f)
        print(f"Saved data to cache: {filename}")
    except Exception as e:
        print(f"Error saving to cache {filename}: {e}")


# Example usage
async def main(trip_number: int = None):
    # Create API client
    client = RailwayAPIClient()

    try:
        # Login if no auth token is provided
        if AUTH_TOKEN is None:
            print(f"Logging in with mobile number: {MOBILE_NUMBER}")
            auth_token = await client.login(MOBILE_NUMBER, PASSWORD)
            print(f"Authentication token obtained: {auth_token[:20]}...")
            with open("auth_token.txt", "w") as f:
                f.write(auth_token)
        else:
            client.update_auth_token(AUTH_TOKEN)
            print("Using provided authentication token")

        # Format journey date if using auto format
        formatted_journey_date = format_journey_date(JOURNEY_DATE)

        # Setup cache directory
        os.makedirs(CACHE_DIR, exist_ok=True)

        # Cache filenames for search results and seat layout
        search_cache_filename = f"{CACHE_DIR}/search_{FROM_CITY}_{TO_CITY}_{formatted_journey_date}_{SEAT_CLASS}.pkl"

        # Try to load search results from cache
        search_results = None
        if USE_SEARCH_CACHE:
            search_results = load_from_cache(search_cache_filename)

        # If cache miss or cache disabled, fetch fresh data
        if search_results is None:
            # Search for trips using the v2 API with configured parameters
            print(
                f"Searching for trips from {FROM_CITY} to {TO_CITY} on {formatted_journey_date} ({SEAT_CLASS} class)..."
            )
            search_results = await client.search_trips_v2(
                from_city=FROM_CITY,
                to_city=TO_CITY,
                date_of_journey=formatted_journey_date,
                seat_class=SEAT_CLASS,
            )

            # Save to cache if enabled
            if USE_SEARCH_CACHE:
                save_to_cache(search_cache_filename, search_results)

        # Parse trip information for the configured seat class
        trips_info = parse_trip_info(search_results, SEAT_CLASS)

        if not trips_info:
            print(f"No {SEAT_CLASS} class trips found for {formatted_journey_date}")
            return 90

        print(f"\nAvailable {SEAT_CLASS} class trips:")
        for i, trip in enumerate(trips_info):
            print(f"\n{i + 1}. {trip['train_name']}")
            print(
                f"   Departure: {trip['departure_time']} - Arrival: {trip['arrival_time']} (Duration: {trip['travel_time']})"
            )
            print(
                f"   Fare: {trip['fare']} + VAT {trip['vat_amount']} = {trip['total_fare']}"
            )
            print(f"   Trip ID: {trip['trip_id']}, Route ID: {trip['trip_route_id']}")
            print("   Boarding Points:")
            for point in trip["boarding_points"]:
                print(
                    f"     - {point['name']} at {point['time']} on {point['date']} (ID: {point['id']})"
                )

        # Filter by preferred train if specified
        if PREFERRED_TRAIN:
            filtered_trips = [
                trip
                for trip in trips_info
                if PREFERRED_TRAIN.lower() in trip["train_name"].lower()
            ]
            if filtered_trips:
                trips_info = filtered_trips
                print(f"\nFiltered to show only {PREFERRED_TRAIN} trains.")
            else:
                print(
                    f"\nWarning: Preferred train '{PREFERRED_TRAIN}' not found. Showing all available trains."
                )

        # Let user select a trip
        selected_index = 0
        if len(trips_info) > 1 and not AUTO_SELECT_TRAIN:
            try:
                selected_index = trip_number - 1
                if selected_index < 0 or selected_index >= len(trips_info):
                    print("Invalid selection, using the first trip")
                    selected_index = 0
            except ValueError:
                print("Invalid input, using the first trip")
                selected_index = 0
        else:
            if AUTO_SELECT_TRAIN:
                print("\nAutomatically selecting the first available train.")

        selected_trip = trips_info[selected_index]
        print(f"\nSelected trip: {selected_trip['train_name']}")

        # Use the selected trip information for booking
        trip_id = selected_trip["trip_id"]
        trip_route_id = selected_trip["trip_route_id"]
        boarding_point_id = selected_trip["boarding_points"][0]["id"]

        # Cache filename for seat layout
        seat_layout_cache_filename = f"{CACHE_DIR}/seat_layout_{trip_id}_{trip_route_id}_{formatted_journey_date}.pkl"

        # Try to load seat layout from cache
        seat_layout = None
        if USE_SEARCH_CACHE:
            seat_layout = load_from_cache(seat_layout_cache_filename)

        # Fetch seat layout if not in cache
        if seat_layout is None:
            # Fetch seat layout for the selected trip
            print("\nFetching seat layout...")
            seat_layout = await client.get_seat_layout(str(trip_id), str(trip_route_id))

            # Save to cache if enabled
            if USE_SEARCH_CACHE:
                save_to_cache(seat_layout_cache_filename, seat_layout)

        # Also save as JSON for debugging
        with open(f"{CACHE_DIR}/seat_layout_{trip_id}_{trip_route_id}.json", "w") as f:
            json.dump(seat_layout, f, indent=2)

        # Find an available seat
        ticket_ids = []

        # seat_no = None
        seat_numbers = []
        for l in seat_layout["data"]["seatLayout"]:
            for row in l["layout"]:
                for seat in row:
                    # print(f"Seat: {seat['seat_number']}, Availability: {seat['seat_availability']}")
                    if seat["seat_availability"] == 1:
                        ticket_ids.append(seat["ticket_id"])
                        seat_numbers.append(seat["seat_number"])

                    if len(ticket_ids) == NUM_SEATS_TO_BOOK:
                        break
                if len(ticket_ids) == NUM_SEATS_TO_BOOK:
                    break
            if len(ticket_ids) == NUM_SEATS_TO_BOOK:
                break

        if not ticket_ids:
            print("No available seats found")
            return 90

        # print(f"Found available seat: {seat_no}")
        print(f"Ticket IDs: {ticket_ids}")
        print(f"Seat Numbers: {seat_numbers}")

        # Reserve the seat
        print("\nReserving seat...")
        reservation_responses = await asyncio.gather(
            *[client.reserve_seat(ticket_id, trip_route_id) for ticket_id in ticket_ids]
        )

        print("Reservation Responses:")
        for reservation_response in reservation_responses:
            print(json.dumps(reservation_response, indent=2))

        # Get passenger details
        print("\nGetting passenger details...")
        passenger_details = await client.get_passenger_details(
            trip_id, trip_route_id, ticket_ids
        )
        print("Passenger Details:")
        print(json.dumps(passenger_details, indent=2))

        # Verify OTP
        print("\nAn OTP should have been sent to your phone.")
        otp = input("Please enter the OTP: ")

        print("\nVerifying OTP...")
        verification_response = await client.verify_otp(
            trip_id, trip_route_id, ticket_ids, otp
        )
        print("Verification Response:")
        print(json.dumps(verification_response, indent=2))

        # Get journey date in the required format (DD-MMM-YYYY)
        journey_date = selected_trip["boarding_points"][0]["date"]

        # Create booking data dynamically based on the number of tickets
        booking_data = create_booking_data(
            trip_id=trip_id,
            trip_route_id=trip_route_id,
            ticket_ids=ticket_ids,
            boarding_point_id=boarding_point_id,
            journey_date=journey_date,
            otp=otp,
        )

        # Confirm booking
        print("\nConfirming booking...")
        print("Booking Data:")
        print(json.dumps(booking_data, indent=2))

        confirmation_response = await client.confirm_booking(booking_data)
        print("Confirmation Response:")
        print(json.dumps(confirmation_response, indent=2))

        # Save booking information
        save_booking_info(booking_data, confirmation_response)

        print("\nTicket booking completed successfully!")
        print(f"Journey: {FROM_CITY} to {TO_CITY}")
        print(f"Date: {journey_date}")
        print(f"Train: {selected_trip['train_name']}")
        print(f"Passengers: {', '.join(booking_data['pname'])}")
        print(f"Contact: {PASSENGER_MOBILE}")

        return 0

    except Exception as e:
        traceback.print_exc()
        print(f"Error: {e}")
        return 90


def call_func(trip_number: int, refresh_cache: bool = False):
    """
    Call the main function with retry logic.

    Args:
        trip_number (int): The trip number to book
        refresh_cache (bool): Whether to refresh the cache
    """
    # Temporarily override cache setting if refresh is requested
    global USE_SEARCH_CACHE
    original_cache_setting = USE_SEARCH_CACHE

    if refresh_cache:
        print("Cache refresh requested. Fetching fresh data from the API.")
        USE_SEARCH_CACHE = False

    try:
        for i in range(MAX_RETRY_ATTEMPTS):
            if asyncio.run(main(int(trip_number))) == 90:
                print(f"Attempt {i + 1} failed. Retrying...")
                continue
            else:
                print(f"Ticket booked successfully on {i + 1} attempt")
                break
        else:
            print(f"Failed to book ticket after {MAX_RETRY_ATTEMPTS} attempts")
    finally:
        # Restore original cache setting
        USE_SEARCH_CACHE = original_cache_setting


def book_ticket():
    """Main entry point for the script with command line argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(description="Book Bangladesh Railway tickets")
    parser.add_argument(
        "--trip", "-t", type=int, default=1, help="Trip number to book (default: 1)"
    )
    parser.add_argument(
        "--refresh",
        "-r",
        action="store_true",
        help="Refresh cache and fetch fresh data",
    )

    args = parser.parse_args()

    print(
        f"Starting booking process for trip #{args.trip}"
        + (f" with {args.threads} threads" if args.threads > 1 else "")
        + (", forcing cache refresh" if args.refresh else "")
    )

    # Single thread mode
    call_func(args.trip, args.refresh)


# Run the example if this script is executed directly
if __name__ == "__main__":
    book_ticket()
