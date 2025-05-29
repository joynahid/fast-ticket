import pickle
import os
from typing import Any, Optional
from abstractions import CacheService
import logging

# Configure logging
logger = logging.getLogger("cache_service")


class FileCacheService(CacheService):
    """File-based cache service implementation."""

    def __init__(self, cache_dir: str):
        """
        Initialize the cache service.

        Args:
            cache_dir (str): Directory for storing cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache key.

        Args:
            key (str): Cache key

        Returns:
            str: File path for the cache key
        """
        # Replace invalid filename characters
        safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.pkl")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key (str): Cache key

        Returns:
            Optional[Any]: Cached value or None if not found
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)
            logger.debug(f"Loaded data from cache: {key}")
            return data
        except (pickle.PickleError, EOFError, Exception) as e:
            logger.error(f"Error loading cache {key}: {e}")
            # Remove corrupted cache file
            try:
                os.remove(cache_path)
            except:
                pass
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key (str): Cache key
            value (Any): Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(value, f)
            logger.debug(f"Saved data to cache: {key}")
        except Exception as e:
            logger.error(f"Error saving to cache {key}: {e}")

    def clear(self, key: str) -> None:
        """
        Clear specific cache key.

        Args:
            key (str): Cache key to clear
        """
        cache_path = self._get_cache_path(key)
        
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.debug(f"Cleared cache: {key}")
        except Exception as e:
            logger.error(f"Error clearing cache {key}: {e}")

    def clear_all(self) -> None:
        """Clear all cache files."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".pkl"):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
            logger.debug("Cleared all cache files")
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")

    def generate_search_key(
        self, from_city: str, to_city: str, date: str, seat_class: str
    ) -> str:
        """
        Generate a cache key for search results.

        Args:
            from_city (str): Origin city
            to_city (str): Destination city
            date (str): Journey date
            seat_class (str): Seat class

        Returns:
            str: Cache key
        """
        return f"search_{from_city}_{to_city}_{date}_{seat_class}"

    def generate_seat_layout_key(self, trip_id: int, trip_route_id: int) -> str:
        """
        Generate a cache key for seat layout.

        Args:
            trip_id (int): Trip ID
            trip_route_id (int): Trip route ID

        Returns:
            str: Cache key
        """
        return f"seat_layout_{trip_id}_{trip_route_id}" 