import datetime
import logging

from src.api.factory import JiraApiFactory
from src.services.cache_manager import CacheManager
from src.utils.error_handler import handle_generic_exception
from src.utils.logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


class JiraIssueService:
    """Service to handle operations related to Jira issues of any type."""

    def __init__(self):
        """Initialize the service with a Jira API client and a cache manager."""
        factory = JiraApiFactory()
        self.client = factory.get_client("generic")
        self.cache_manager = CacheManager()

    def fetch_issues(
        self, jql_query, fields="*", max_results=100, expand_changelog=False
    ):
        """
        Fetch issues from Jira using a JQL query.

        :param jql_query: The JQL query to execute.
        :param fields: Fields to include in the response.
        :param max_results: Maximum number of results to fetch.
        :param expand_changelog: Whether to include changelog data.
        :return: List of issues.
        """
        try:
            if expand_changelog:
                fields += ",changelog"

            # Generate a cache key based on the query parameters
            cache_file = f"issues_cache_{hash(jql_query)}.json"
            cached_data = self.cache_manager.load_from_cache(
                cache_file, expiration_minutes=60
            )
            if cached_data:
                logger.info(f"Loaded issues from cache for JQL: {jql_query}")
                return cached_data

            # Fetch from Jira API if no valid cache is found
            logger.info(f"Fetching issues with JQL: {jql_query}")
            issues = self.client.get(
                "search",
                params={"jql": jql_query, "fields": fields, "maxResults": max_results},
            )

            # Cache the result if fetched successfully
            if issues:
                self.cache_manager.save_to_cache(cache_file, issues)

            return issues

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to fetch issues with JQL '{jql_query}'"
            )
            return []

    def update_issue_fields(self, issue_key, fields):
        """
        Update fields of a Jira issue.

        :param issue_key: The key of the issue to update.
        :param fields: Dictionary of fields to update.
        :return: Response from the Jira API.
        """
        try:
            payload = {"fields": fields}
            logger.info(f"Updating issue {issue_key} with fields: {fields}")
            return self.client.put(f"issue/{issue_key}", payload)
        except Exception as e:
            handle_generic_exception(e, f"Failed to update issue {issue_key}")
            return None

    def fetch_completed_epics(self, team_name, time_period_days):
        """
        Fetch completed epics for a specific team within a given time period.

        :param team_name: The name of the team to filter epics.
        :param time_period_days: Number of days in the past to search.
        :return: List of completed epics.
        """
        try:
            cache_file = f"completed_epics_{team_name}_{time_period_days}.json"
            cached_data = self.cache_manager.load_from_cache(
                cache_file, expiration_minutes=60
            )
            if cached_data:
                logger.info(
                    f"Loaded completed epics from cache for team '{team_name}'."
                )
                return cached_data

            time_period_ago = datetime.datetime.now() - datetime.timedelta(
                days=time_period_days
            )
            jql_query = (
                f"project = 'Cropwise Core Services' AND type = Epic "
                f"AND 'Squad[Dropdown]' = '{team_name}' "
                f"AND statusCategory = Done AND resolved >= {time_period_ago.strftime('%Y-%m-%d')}"
            )
            logger.info(
                (
                    f"Fetching completed epics for team '{team_name}' "
                    f"within the last {time_period_days} days."
                )
            )
            epics = self.fetch_issues(jql_query)

            if epics:
                self.cache_manager.save_to_cache(cache_file, epics)

            return epics

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to fetch completed epics for team '{team_name}'"
            )
            return []

    def fetch_open_issues_by_type(self, team_name, issue_type="Epic", fix_version=None):
        """
        Fetch open issues of a specified type for a team, optionally filtered by fix version.

        :param team_name: The name of the team to filter issues.
        :param issue_type: Type of issue to filter (e.g., Epic, Story, Task).
        :param fix_version: Fix version to filter issues (optional).
        :return: List of open issues.
        """
        try:
            cache_file = f"open_issues_{team_name}_{issue_type}_{fix_version}.json"
            cached_data = self.cache_manager.load_from_cache(
                cache_file, expiration_minutes=60
            )
            if cached_data:
                logger.info(
                    f"Loaded open {issue_type}s from cache for team '{team_name}'."
                )
                return cached_data

            jql_query = (
                f"project = 'Cropwise Core Services' AND type = '{issue_type}' "
                f"AND 'Squad[Dropdown]' = '{team_name}' AND statusCategory != Done"
            )
            if fix_version:
                jql_query += f" AND fixVersion = '{fix_version}'"

            logger.info(
                f"Fetching open {issue_type}s for team '{team_name}', fix version '{fix_version}'."
            )
            open_issues = self.fetch_issues(jql_query)

            if open_issues:
                self.cache_manager.save_to_cache(cache_file, open_issues)

            return open_issues

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to fetch open issues for team '{team_name}'"
            )
            return []

    def update_epic_dates(self, issue_key, start_date=None, end_date=None):
        """
        Update the start and end dates for an epic.

        :param issue_key: The key of the epic to update.
        :param start_date: The start date to be set (can be None).
        :param end_date: The end date to be set (can be None).
        :return: Response from the Jira API.
        """
        try:
            fields = {
                "customfield_10015": start_date.isoformat() if start_date else None,
                "customfield_10233": end_date.isoformat() if end_date else None,
            }
            logger.info(
                f"Updating epic {issue_key} with start date: {start_date} and end date: {end_date}"
            )
            return self.update_issue_fields(issue_key, fields)
        except Exception as e:
            handle_generic_exception(
                e, f"Failed to update dates for epic '{issue_key}'"
            )
            return None

    def fill_missing_dates_for_completed_epics(self, team_name):
        """
        Fetch completed epics with missing start or end dates and update them using changelog data.

        :param team_name: The name of the team to filter epics.
        :param time_period_days: Number of days in the past to search.
        """
        try:
            # JQL to find completed epics with missing start or end dates
            jql_query = (
                f"project = 'Cropwise Core Services' AND type = Epic AND status = Done "
                f"AND 'Squad[Dropdown]' = '{team_name}' AND ("
                f"'Start date' is EMPTY OR 'End date' is EMPTY)"
            )
            logger.info(
                f"Fetching completed epics with missing dates for team '{team_name}'."
            )
            epics = self.fetch_issues(
                jql_query, fields="key,summary,changelog", expand_changelog=True
            )

            if not epics:
                logger.info("No completed epics with missing dates found.")
                return

            for epic in epics:
                issue_key = epic["key"]
                changelog = epic.get("changelog", {}).get("histories", [])
                start_date = None
                end_date = None

                # Iterate over changelog histories to find appropriate dates
                for history in changelog:
                    for item in history.get("items", []):
                        # Find "7 PI Started" creation (start date)
                        if item.get("toString") == "7 PI Started" and not start_date:
                            start_date = datetime.datetime.strptime(
                                history["created"], "%Y-%m-%dT%H:%M:%S.%f%z"
                            ).date()

                        # Find transition from "7 PI Started" to "Done" (end date)
                        if (
                            item.get("fromString") == "7 PI Started"
                            and item.get("toString") == "Done"
                            and not end_date
                        ):
                            end_date = datetime.datetime.strptime(
                                history["created"], "%Y-%m-%dT%H:%M:%S.%f%z"
                            ).date()

                        # Stop if both dates are found
                        if start_date and end_date:
                            break

                if start_date or end_date:
                    logger.info(
                        (
                            f"Updating epic '{issue_key}' with found dates: "
                            f"Start - {start_date}, End - {end_date}"
                        )
                    )
                    self.update_epic_dates(
                        issue_key, start_date=start_date, end_date=end_date
                    )

        except Exception as e:
            handle_generic_exception(
                e, "Failed to fill missing dates for completed epics"
            )
