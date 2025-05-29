from models import ApiResponse


class ForbiddenException(Exception):
    """Exception raised for forbidden access."""

    pass


class RailwayTripException(Exception):
    """Railway trip exception."""

    pass


class UnauthorizedException(RailwayTripException):
    """Exception raised for unauthorized access."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Unauthorized access: {response.error_message}")


class OrderLimitExceededForTheDayException(RailwayTripException):
    """Exception raised for order limit exceeded for the day."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Order limit exceeded for the day: {response.error_message}")

    def __str__(self):
        return f"Order limit exceeded for the day: {self.response.error_message}"


class SeatAlreadyReservedException(RailwayTripException):
    """Exception raised for seat already reserved."""

    def __init__(self):
        super().__init__("Seat already reserved by another process")


class MultipleOrderAttemptException(RailwayTripException):
    """Exception raised for multiple order attempt."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Multiple order attempt: {response.error_message}")

    def __str__(self):
        return f"Multiple order attempt: {self.response.error_message}"


class OtpExpiredException(RailwayTripException):
    """Exception raised for OTP expired."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"OTP expired: {response.error_message}")


class OtpVerificationFailedException(RailwayTripException):
    """Exception raised for OTP verification failed."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"OTP verification failed: {response.error_message}")


class Max4SeatsPerOrderException(RailwayTripException):
    """Exception raised for max 4 seats per order."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Max 4 seats exception: {response.error_message}")


class ReservationFailedException(RailwayTripException):
    """Exception raised for reservation failed."""

    response: ApiResponse

    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Reservation failed: {response.error_message}")

