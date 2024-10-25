import logging

from src.api.jira_api_client import JiraApiClient
from src.utils.logging_config import configure_logging

# Configure logging for the factory module
configure_logging()
logger = logging.getLogger(__name__)


class JiraApiFactory:
    """Factory for creating instances of Jira API Clients."""

    @staticmethod
    def get_client(client_type):
        """Return an appropriate Jira API client based on client type."""
        if client_type == "generic":
            logger.info("Creating a generic Jira API client.")
            return JiraApiClient()
        else:
            logger.error(f"Unknown client type requested: {client_type}")
            raise ValueError(f"Unknown client type: {client_type}")
