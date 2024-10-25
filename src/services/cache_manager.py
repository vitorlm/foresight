import datetime
import json
import logging
import os

from src.utils.error_handler import handle_generic_exception
from src.utils.logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


class CacheManager:
    """Service to manage caching of data using JSON files."""

    def __init__(self, cache_dir=None):
        """
        Initialize the CacheManager with a specific cache directory.

        :param cache_dir: Directory where cache files will be stored.
        """
        # Use the root-level "cache" directory by default
        if cache_dir is None:
            cache_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "../../cache"
            )

        self.cache_dir = cache_dir
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create cache directory at {self.cache_dir}: {e}")
            raise

    def load_from_cache(self, file_name, expiration_minutes=None):
        """
        Load data from a specified cache file.

        :param file_name: The name of the cache file to load data from.
        :param expiration_minutes: Expiration time in minutes. If None, cache is always valid.
        :return: The loaded data if successful, otherwise None.
        """
        try:
            file_path = os.path.join(self.cache_dir, file_name)
            if not os.path.exists(file_path):
                logger.info(f"Cache file '{file_name}' does not exist.")
                return None

            with open(file_path, "r") as file:
                cache_data = json.load(file)
                # Verify if the cache has expired
                if expiration_minutes is not None:
                    cached_time_str = cache_data.get("_cached_at")
                    if cached_time_str:
                        cached_time = datetime.datetime.fromisoformat(cached_time_str)
                        if (
                            datetime.datetime.now() - cached_time
                        ).total_seconds() > expiration_minutes * 60:
                            logger.info(f"Cache file '{file_name}' has expired.")
                            return None

                logger.info(f"Loaded data from cache file: {file_name}")
                return cache_data.get("data")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from cache file '{file_name}': {e}")
            return None
        except Exception as e:
            handle_generic_exception(
                e, f"Unexpected error while loading cache file '{file_name}'"
            )
            return None

    def save_to_cache(self, file_name, data):
        """
        Save data to a specified cache file.

        :param file_name: The name of the cache file to save data to.
        :param data: The data to be saved.
        """
        try:
            file_path = os.path.join(self.cache_dir, file_name)
            cache_data = {
                "data": data,
                "_cached_at": datetime.datetime.now().isoformat(),
            }
            with open(file_path, "w") as file:
                json.dump(cache_data, file, indent=4)
            logger.info(f"Data successfully saved to cache file: {file_name}")

        except OSError as e:
            logger.error(
                f"Failed to write cache file '{file_name}' at '{file_path}': {e}"
            )
            raise
        except Exception as e:
            handle_generic_exception(
                e, f"Failed to save data to cache file '{file_name}'"
            )

    def invalidate_cache(self, file_name):
        """
        Invalidate a specified cache file by deleting it.

        :param file_name: The name of the cache file to invalidate.
        """
        try:
            file_path = os.path.join(self.cache_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cache file '{file_name}' invalidated successfully.")
            else:
                logger.warning(
                    f"Cache file '{file_name}' does not exist to invalidate."
                )

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to invalidate cache file '{file_name}'"
            )
