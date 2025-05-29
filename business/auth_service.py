from typing import Optional
from datetime import datetime
from abstractions import AuthenticationService
from models import AuthenticationToken
from infrastructure.api_client import RailwayApiClient
from config import BookingConfig
import logging

# Configure logging
logger = logging.getLogger("auth_service")

class RailwayAuthService(AuthenticationService):
    """Railway authentication service implementation."""

    def __init__(self, api_client: RailwayApiClient, config: BookingConfig):
        """
        Initialize the authentication service.

        Args:
            api_client (RailwayApiClient): API client for making requests
            config (BookingConfig): Configuration object
        """
        self.api_client = api_client
        self.config = config
        self._current_token: Optional[AuthenticationToken] = None

    async def login(self, mobile_number: str, password: str) -> AuthenticationToken:
        """
        Login and get authentication token.

        Args:
            mobile_number (str): Mobile number for login
            password (str): Password for login

        Returns:
            AuthenticationToken: Authentication token with metadata

        Raises:
            Exception: If login fails
        """
        response = await self.api_client.login(mobile_number, password)
        
        if not response.success:
            raise Exception(f"Login failed: {response.error_message}")

        token_data = response.data.get("data", {})
        token_string = token_data.get("token")
        
        if not token_string:
            raise Exception("No token received from login response")

        # Create authentication token object
        auth_token = AuthenticationToken(
            token=token_string,
            created_at=datetime.now(),
            mobile_number=mobile_number
        )

        # Update API client with new token
        self.api_client.update_auth_token(token_string)
        self._current_token = auth_token

        # Save token to config file
        self.config.save_auth_token(token_string)

        logger.debug(f"Login successful for {mobile_number}")
        logger.debug(f"Authentication token obtained: {token_string[:20]}...")
        
        return auth_token

    def get_current_token(self) -> Optional[str]:
        """
        Get current authentication token.

        Returns:
            Optional[str]: Current token or None if not authenticated
        """
        if self._current_token:
            return self._current_token.token

        # Try to get token from config
        token = self.config.auth_token
        if token:
            self._current_token = AuthenticationToken(
                token=token,
                created_at=datetime.now()  # We don't know the actual creation time
            )
            return token

        return None

    def set_token(self, token: str) -> None:
        """
        Set authentication token.

        Args:
            token (str): Authentication token to set
        """
        self._current_token = AuthenticationToken(
            token=token,
            created_at=datetime.now()
        )
        self.api_client.update_auth_token(token)
        self.config.save_auth_token(token)

    async def ensure_authenticated(self) -> bool:
        """
        Ensure user is authenticated, login if necessary.

        Returns:
            bool: True if authenticated successfully

        Raises:
            Exception: If authentication fails
        """
        current_token = self.get_current_token()

        if current_token:
            logger.debug("Using existing authentication token")
            return True

        # Need to login
        logger.debug(f"Logging in with mobile number: {self.config.mobile_number}")
        await self.login(self.config.mobile_number, self.config.password)
        return True

    def is_token_valid(self) -> bool:
        """
        Check if current token is valid (basic check).

        Returns:
            bool: True if token appears valid
        """
        if not self._current_token:
            return False

                    # Basic validation - token should be a non-empty string
        return bool(self._current_token.token and len(self._current_token.token) > 0)

    def clear_token(self) -> None:
        """Clear current authentication token."""
        self._current_token = None
        # Remove authorization header from API client
        if "Authorization" in self.api_client.headers:
            del self.api_client.headers["Authorization"]
 