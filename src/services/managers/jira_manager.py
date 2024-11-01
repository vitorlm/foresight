import datetime
import logging

from src.services.jira_issue_service import JiraIssueService
from src.utils.error_handler import handle_generic_exception
from src.utils.json_handler import JSONHandler
from src.utils.logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


class JiraManager:

    def __init__(self):
        self.json_handler = JSONHandler()
        self.jira_issue_service = JiraIssueService()
        self.metadata_cache = {}

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

    def create_issue(self, json_filename: str):
        """
        Create an issue in Jira by first fetching issue type metadata and building the payload.

        :param project_data: Dictionary containing project key, issue type, and other issue details.
        :return: Response from Jira API.
        """
        try:
            issue_data = self.json_handler.load_json(json_filename)
            if not issue_data:
                raise ValueError(f"Failed to load JSON data from '{json_filename}'")

            project_key = issue_data.get("project_key")
            issuetype_name = issue_data.get("issuetype")

            # Step 1: Fetch available issue types for the specified project
            issue_types_data = self.jira_issue_service.fetch_issuetypes(project_key)
            issue_types = issue_types_data.get("issueTypes", [])

            if not issue_types:
                raise ValueError(f"No issue types found for project '{project_key}'")

            # Step 3: Get the ID for the specified issue type
            issuetype_id = next(
                (it["id"] for it in issue_types if it.get("name") == issuetype_name),
                None,
            )

            if not issuetype_id:
                raise ValueError(
                    f"Issue type '{issuetype_name}' not found for project '{project_key}'"
                )

            # Step 3: Fetch metadata for the specified issue type
            metadata = self.jira_issue_service.get_issuetype_metadata(
                project_key, issuetype_id
            )

            if not metadata:
                raise ValueError(
                    f"Metadata for issue type '{issuetype_name}' not found in "
                    f"project '{project_key}'"
                )

            # Step 4: Build the payload from metadata
            payload = self.jira_issue_service.build_payload_from_metadata(
                project_key, issuetype_id, issue_data
            )

            # Step 5: Create the issue
            response = self.jira_issue_service.create_issue(project_key, payload)

            if response:
                logger.info(f"Issue created with key: {response.get('key')}")
                return response
            else:
                logger.warning(f"Failed to create issue in project '{project_key}'")
                return None

        except Exception as e:
            handle_generic_exception(e, "Failed to create issue with metadata")
            return None

    def create_bulk_issues(self, json_filename: str):
        """
        Create multiple sub-tasks in Jira by fetching metadata and preparing payload for each task.

        :param json_filename: Path to the JSON file containing the list of sub-task details.
        :return: Response from Jira API.
        """
        try:
            issues_data = self.json_handler.load_json(json_filename)
            if not issues_data:
                raise ValueError(f"Failed to load JSON data from '{json_filename}'")

            project_key = issues_data.get("project_key")
            issues_list = issues_data.get("issues", [])
            if not project_key or not issues_list:
                raise ValueError(
                    f"Missing project key or issues data in '{json_filename}'"
                )

            issue_types_data = self.jira_issue_service.fetch_issuetypes(project_key)
            issue_types = issue_types_data.get("issueTypes", [])
            if not issue_types:
                raise ValueError(f"No issue types found for project '{project_key}'")

            payload = []
            for issue_data in issues_list:
                transformed_issue = {
                    "project_key": project_key,
                    "issuetype": issues_data.get("issuetype", ""),
                    "components": issue_data.get("components", []),
                    "summary": issue_data.get("summary", ""),
                    "description": issue_data.get("description", ""),
                    "parent": issues_data.get("parent", ""),
                    "customfield_10265": issues_data.get("squad", {}),
                }

                issuetype_name = transformed_issue.get("issuetype")

                # Find the ID for the sub-task issue type
                issuetype_id = next(
                    (
                        it["id"]
                        for it in issue_types
                        if it.get("name") == issuetype_name
                    ),
                    None,
                )

                if not issuetype_id:
                    raise ValueError(
                        f"Issue type '{issuetype_name}' not found for project '{project_key}'"
                    )

                # Check if metadata is already cached
                cache_key = f"{project_key}_{issuetype_id}"
                if cache_key in self.metadata_cache:
                    metadata = self.metadata_cache[cache_key]
                else:
                    # Fetch metadata for the issue type
                    metadata = self.jira_issue_service.get_issuetype_metadata(
                        project_key, issuetype_id
                    )
                    if not metadata:
                        raise ValueError(
                            f"Metadata for issue type '{issuetype_name}' not found in "
                            f"project '{project_key}'"
                        )
                    # Cache the fetched metadata
                    self.metadata_cache[cache_key] = metadata

                # Build the payload from metadata and add to list
                payload_content = self.jira_issue_service.build_payload_from_metadata(
                    project_key, issuetype_id, transformed_issue, metadata
                )
                payload.append(payload_content)

            # Step 3: Use create_bulk_issues to create all sub-tasks in bulk
            response = self.jira_issue_service.create_bulk_issues(
                project_key, {"issueUpdates": payload}
            )

            if response:
                logger.info(f"Bulk sub-tasks created in project '{project_key}'")
                return response
            else:
                logger.warning(
                    f"Bulk sub-task creation returned no response for project '{project_key}'"
                )
                return None

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to create bulk sub-tasks in project '{project_key}'"
            )
            return None
