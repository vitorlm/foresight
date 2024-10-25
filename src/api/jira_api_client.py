# Configure the logging for the module
import logging

import requests
from requests.auth import HTTPBasicAuth

from config import API_TOKEN, EMAIL, JIRA_URL
from src.utils.error_handler import handle_request_exception
from src.utils.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


class JiraApiClient:
    """Generic JIRA API Client to handle basic API operations."""

    def __init__(self, base_url=f"{JIRA_URL}/rest/api/3/"):
        """Initialize the Jira API client."""
        self.base_url = base_url
        self.auth = HTTPBasicAuth(EMAIL, API_TOKEN)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get(self, endpoint, params=None):
        """Make a GET request to the Jira API."""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                auth=self.auth,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            handle_request_exception(e, f"Error during GET request to {endpoint}")
            return None

    def post(self, endpoint, payload):
        """Make a POST request to the Jira API."""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self.headers,
                auth=self.auth,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            handle_request_exception(e, f"Error during POST request to {endpoint}")
            return None

    def put(self, endpoint, payload):
        """Make a PUT request to the Jira API."""
        try:
            response = requests.put(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self.headers,
                auth=self.auth,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            handle_request_exception(e, f"Error during PUT request to {endpoint}")
            return None
