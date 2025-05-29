from typing import List, Dict
from abstractions import PassengerService
from models import Passenger


class RailwayPassengerService(PassengerService):
    """Railway passenger service implementation."""

    def validate_passengers(self, passengers: List[Passenger]) -> bool:
        """
        Validate passenger information.

        Args:
            passengers (List[Passenger]): List of passengers to validate

        Returns:
            bool: True if all passengers are valid

        Raises:
            ValueError: If validation fails
        """
        if not passengers:
            raise ValueError("No passengers provided")

        for i, passenger in enumerate(passengers):
            # Validate required fields
            if not passenger.name or not passenger.name.strip():
                raise ValueError(f"Passenger {i + 1}: Name is required")

            if not passenger.email or "@" not in passenger.email:
                raise ValueError(f"Passenger {i + 1}: Valid email is required")

            if not passenger.mobile or len(passenger.mobile.strip()) < 10:
                raise ValueError(f"Passenger {i + 1}: Valid mobile number is required")

            if passenger.gender not in ["male", "female"]:
                raise ValueError(f"Passenger {i + 1}: Gender must be 'male' or 'female'")

            if passenger.passenger_type not in ["Adult", "Child"]:
                raise ValueError(f"Passenger {i + 1}: Type must be 'Adult' or 'Child'")

        return True

    def prepare_passenger_data(
        self, 
        passengers: List[Passenger], 
        num_tickets: int
    ) -> Dict[str, List[str]]:
        """
        Prepare passenger data for booking API.

        Args:
            passengers (List[Passenger]): List of passengers
            num_tickets (int): Number of tickets being booked

        Returns:
            Dict[str, List[str]]: Prepared passenger data for API
        """
        # Validate passengers first
        self.validate_passengers(passengers)

        # Ensure we have enough passenger information
        # If more tickets than passengers, duplicate the first passenger
        # If more passengers than tickets, take only the first N passengers
        adjusted_passengers = self._adjust_passenger_count(passengers, num_tickets)

        # Prepare data in the format expected by the API
        passenger_data = {
            "pname": [p.name for p in adjusted_passengers],
            "gender": [p.gender for p in adjusted_passengers],
            "passengerType": [p.passenger_type for p in adjusted_passengers],
            "pemail": adjusted_passengers[0].email,  # Use first passenger's email for all
            "pmobile": adjusted_passengers[0].mobile,  # Use first passenger's mobile for all
        }

        return passenger_data

    def _adjust_passenger_count(
        self, 
        passengers: List[Passenger], 
        needed_count: int
    ) -> List[Passenger]:
        """
        Adjust passenger list to match the number of tickets.

        Args:
            passengers (List[Passenger]): Original passenger list
            needed_count (int): Required number of passengers

        Returns:
            List[Passenger]: Adjusted passenger list
        """
        if len(passengers) == needed_count:
            return passengers
        elif len(passengers) > needed_count:
            # Take first N passengers
            return passengers[:needed_count]
        else:
            # Duplicate passengers to reach needed count
            adjusted = passengers.copy()
            while len(adjusted) < needed_count:
                # Add passengers cyclically
                adjusted.append(passengers[len(adjusted) % len(passengers)])
            return adjusted

    def create_passengers_from_config(
        self,
        names: List[str],
        email: str,
        mobile: str,
        genders: List[str],
        types: List[str],
    ) -> List[Passenger]:
        """
        Create passenger objects from configuration data.

        Args:
            names (List[str]): Passenger names
            email (str): Common email for all passengers
            mobile (str): Common mobile for all passengers
            genders (List[str]): Passenger genders
            types (List[str]): Passenger types

        Returns:
            List[Passenger]: List of passenger objects
        """
        passengers = []
        
        # Use the minimum length among all lists to avoid index errors
        count = min(len(names), len(genders), len(types))
        
        for i in range(count):
            passengers.append(
                Passenger(
                    name=names[i],
                    email=email,
                    mobile=mobile,
                    gender=genders[i],
                    passenger_type=types[i],
                )
            )

        return passengers

    def get_passenger_summary(self, passengers: List[Passenger]) -> str:
        """
        Get a summary string of passengers.

        Args:
            passengers (List[Passenger]): List of passengers

        Returns:
            str: Summary string
        """
        if not passengers:
            return "No passengers"

        summary_parts = []
        for i, passenger in enumerate(passengers, 1):
            summary_parts.append(
                f"{i}. {passenger.name} ({passenger.gender}, {passenger.passenger_type})"
            )

        return "\n".join(summary_parts) 