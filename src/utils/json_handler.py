import json
import logging
import os
from typing import Any, Optional

from src.utils.error_handler import handle_generic_exception
from src.utils.logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


class JSONHandler:
    """Service to manage JSON data storage and retrieval with validation."""

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the JSONHandler with a specific storage directory.

        :param storage_dir: Directory where JSON files will be stored.
        """
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../storage"
        )
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except OSError as e:
            logger.error(
                f"Failed to create storage directory at {self.storage_dir}: {e}"
            )
            raise

    def _get_file_path(self, filename: str) -> str:
        """Helper to get the full path for a file in the storage directory."""
        return os.path.join(self.storage_dir, filename)

    def _is_valid_json(self, json_string: str) -> bool:
        """
        Check if a string contains valid JSON.

        :param json_string: JSON string to validate.
        :return: True if the string contains valid JSON, False otherwise.
        """
        try:
            json.loads(json_string)
            logger.info("JSON string is valid.")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON string: {e.msg}")
            return False

    def load_json(self, filename: str) -> Optional[Any]:
        """
        Load data from a specified JSON file with validation.

        :param filename: The name of the JSON file to load data from.
        :return: Parsed JSON data if available and valid, otherwise None.
        """
        file_path = self._get_file_path(filename)
        if not os.path.exists(file_path):
            logger.info(f"File '{filename}' does not exist.")
            return None

        try:
            with open(file_path, "r") as file:
                json_string = file.read()
                # Validate JSON string before parsing
                if not self._is_valid_json(json_string):
                    logger.warning(f"The file '{filename}' contains invalid JSON.")
                    return None
                data = json.loads(json_string)
                logger.info(f"Loaded JSON data from '{filename}'.")
                return data
        except Exception as e:
            handle_generic_exception(e, f"Unexpected error while loading '{filename}'")
        return None

    def save_json(self, filename: str, data: Any) -> None:
        """
        Save data to a specified JSON file with validation.

        :param filename: The name of the JSON file to save data to.
        :param data: The data to be saved, must be JSON-serializable.
        """
        try:
            # Convert data to JSON string for validation
            json_string = json.dumps(data)
            if not self._is_valid_json(json_string):
                logger.error("Data provided is not a valid JSON format.")
                raise ValueError("Data provided is not a valid JSON format.")

            file_path = self._get_file_path(filename)
            with open(file_path, "w") as file:
                file.write(json_string)
            logger.info(f"Data successfully saved to '{filename}'.")
        except (TypeError, ValueError) as e:
            logger.error(f"Data provided to '{filename}' is not JSON serializable: {e}")
            raise ValueError(f"Data provided is not JSON serializable: {e}")
        except OSError as e:
            logger.error(
                f"Failed to write JSON file '{filename}' at '{file_path}': {e}"
            )
            raise
        except Exception as e:
            handle_generic_exception(e, f"Failed to save data to '{filename}'")

    def delete_json(self, filename: str) -> None:
        """
        Delete a specified JSON file.

        :param filename: The name of the JSON file to delete.
        """
        file_path = self._get_file_path(filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"JSON file '{filename}' deleted successfully.")
            else:
                logger.warning(
                    f"File '{filename}' does not exist and cannot be deleted."
                )
        except Exception as e:
            handle_generic_exception(e, f"Failed to delete '{filename}'")
