import datetime
import logging

from atlassian_doc_builder import ADFDoc, ADFParagraph, ADFText

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

    def get_issuetype_metadata(self, project_key, issue_type_id):
        """
        Fetch metadata for a specific issue type in a project.

        :param project_key: The key of the Jira project.
        :param issue_type_id: The ID of the issue type.
        :return: Metadata of the specified issue type.
        """
        try:
            cache_file = f"issuetype_metadata_{project_key}_{issue_type_id}.json"
            cached_data = self.cache_manager.load_from_cache(
                cache_file, expiration_minutes=60
            )
            if cached_data:
                logger.info(
                    f"Loaded metadata from cache for issue type '{issue_type_id}' "
                    f"in project '{project_key}'."
                )
                return cached_data

            endpoint = f"issue/createmeta/{project_key}/issuetypes/{issue_type_id}"
            logger.info(
                f"Fetching metadata for issue type '{issue_type_id}' in project '{project_key}'"
            )
            response = self.client.get(endpoint)

            if response:
                logger.info(
                    f"Retrieved metadata for issue type '{issue_type_id}' "
                    f"in project '{project_key}'"
                )
                self.cache_manager.save_to_cache(cache_file, response)
                return response
            else:
                logger.warning(
                    f"No metadata found for issue type '{issue_type_id}' in project '{project_key}'"
                )
                return None

        except Exception as e:
            handle_generic_exception(
                e,
                f"Failed to fetch metadata for issue type '{issue_type_id}' "
                f"in project '{project_key}'",
            )
            return None

    def fetch_issuetypes(self, project_key):
        """
        Fetch issue types available for a specific project.

        :param project_key: The key of the Jira project.
        :return: List of issue types for the specified project.
        """
        try:
            cache_file = f"issuetypes_{project_key}.json"
            cached_data = self.cache_manager.load_from_cache(
                cache_file, expiration_minutes=60
            )
            if cached_data:
                logger.info(
                    f"Loaded issue types from cache for project '{project_key}'."
                )
                return cached_data

            endpoint = f"issue/createmeta/{project_key}/issuetypes"
            logger.info(f"Fetching create metadata for project '{project_key}'")
            response = self.client.get(endpoint)

            if response:
                logger.info(f"Retrieved issue metadata for project '{project_key}'")
                self.cache_manager.save_to_cache(cache_file, response)
                return response
            else:
                logger.warning(f"No metadata found for project '{project_key}'")
                return None

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to fetch issue metadata for project '{project_key}'"
            )
            return None

    def create_issue(self, project_key, issue_data):
        """
        Create multiple Jira issues based on the provided data.

        :param project_key: The project key.
        :param issue_data: Dictionary with 'summary', 'description', etc.
        :return: Response from Jira API.
        """
        try:
            response = self.client.post(
                "issue",
                issue_data,
            )

            if response:
                logger.info(
                    f"Issue created in project '{project_key}' with key: {response['key']}"
                )
                return response
            else:
                logger.warning(
                    f"Issue creation returned no response for project '{project_key}'"
                )
                return None

        except Exception as e:
            handle_generic_exception(e, "Failed to create a single issue")
            return None

    def create_bulk_issues(self, project_key, issues_data):
        """
        Create a single Jira issue based on the metadata.

        :param project_key: The project key.
        :param issuetype: The issue type name.
        :param issues_data: A JSON serializable Python object with a list of dictionaries,
                            each representing an issue to be created.
        """
        try:
            response = self.client.post(
                "issue/bulk",
                issues_data,
            )

            if response:
                logger.info(f"Issues created in project '{project_key}'")
                return response
            else:
                logger.warning(
                    f"Issues creation returned no response for project '{project_key}'"
                )
                return None

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to create issues in bulk for project '{project_key}'"
            )
            return None

    def get_project(self, project_key):
        """
        Fetch data for a specific Jira project.

        :param project_key: The key or ID of the Jira project.
        :return: Project data as a dictionary.
        """
        try:
            # Cache filename based on project key
            cache_file = f"project_data_{project_key}.json"
            cached_data = self.cache_manager.load_from_cache(
                cache_file, expiration_minutes=60
            )

            if cached_data:
                logger.info(
                    f"Loaded project data from cache for project '{project_key}'."
                )
                return cached_data

            # API endpoint to fetch project data
            endpoint = f"project/{project_key}"
            logger.info(f"Fetching data for project '{project_key}' from Jira API")

            # Call the Jira API to get project data
            project_data = self.client.get(endpoint)

            # Cache the result if fetched successfully
            if project_data:
                logger.info(
                    f"Successfully fetched project data for project '{project_key}'"
                )
                self.cache_manager.save_to_cache(cache_file, project_data)
                return project_data
            else:
                logger.warning(f"No data returned for project '{project_key}'")
                return None

        except Exception as e:
            handle_generic_exception(
                e, f"Failed to fetch project data for project '{project_key}'"
            )
            return None

    def build_payload_from_metadata(
        self, project_key, issuetype_id, issue_data, metadata
    ):
        """
        Build a payload for creating a Jira issue based on the issue type metadata.

        :param project_key: The project key where the issue will be created.
        :param issuetype_id: The ID of the issue type.
        :param issue_data: A dictionary containing the issue details.
        :return: A dictionary representing the payload.
        """

        if "project_key" in issue_data:
            project_data = self.get_project(issue_data["project_key"])
            if not project_data:
                raise ValueError(f"Project '{issue_data['project_key']}' not found.")
            issue_data["project"] = project_data.get("id")
            del issue_data["project_key"]

        payload_fields = {}
        required_fields = {
            field["key"]: field for field in metadata["fields"] if field["required"]
        }

        # Define type handling functions
        def handle_string(field, value):
            return value

        def handle_adf_string(value):
            """
            Converts a string to ADF format.
            """
            doc = ADFDoc()  # Inicializa um documento ADF
            paragraph = ADFParagraph()  # Cria um parágrafo ADF
            paragraph.add(ADFText(value))  # Adiciona o texto ao parágrafo usando `add`
            doc.add(paragraph)  # Adiciona o parágrafo ao documento
            return doc.validate()  # Valida e retorna o documento ADF formatado

        def handle_array(field, value):
            allowed_values = {}
            for v in field.get("allowedValues", []):
                allowed_values[v["name"]] = v["id"]

            if allowed_values:
                # Validate each item in array
                invalid_items = [item for item in value if item not in allowed_values]
                if invalid_items:
                    raise ValueError(
                        f"Invalid values '{invalid_items}' for field '{field['key']}'."
                    )
                return [{"id": allowed_values[item]} for item in value]
            return value

        def handle_attachment(field, value):
            return [{"id": v} for v in value]

        def handle_boolean(field, value):
            if not isinstance(value, bool):
                raise ValueError(
                    f"Expected boolean for '{field['key']}', got {type(value).__name__}."
                )
            return value

        def handle_component(field, value):
            return [{"id": v} for v in value]

        def handle_date(field, value):
            if not isinstance(value, str) or len(value.split("-")) != 3:
                raise ValueError(
                    f"Expected date format 'YYYY-MM-DD' for '{field['key']}'."
                )
            return value

        def handle_issuetype(field, value):
            return {"id": issuetype_id}

        def handle_number(field, value):
            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"Expected number for '{field['key']}', got {type(value).__name__}."
                )
            return value

        def handle_option(field, value):
            allowed_values = {
                v["value"]: v["id"] for v in field.get("allowedValues", [])
            }
            if value not in allowed_values:
                raise ValueError(f"Invalid value '{value}' for field '{field['key']}'.")
            return {"id": allowed_values[value]}

        def handle_priority(field, value):
            allowed_values = {
                v["name"]: v["id"] for v in field.get("allowedValues", [])
            }
            if value not in allowed_values:
                raise ValueError(
                    f"Invalid value '{value}' for priority field '{field['key']}'."
                )
            return {"id": allowed_values[value]}

        def handle_project(field, value):
            return {"id": value}

        def handle_user(field, value):
            return {"accountId": value}

        def handle_version(field, value):
            return [{"id": v} for v in value]

        def handle_issuelink(field, value):
            return {"key": value}

        # Map of field types to handler functions
        field_handlers = {
            "string": handle_string,
            "array": handle_array,
            "attachment": handle_attachment,
            "boolean": handle_boolean,
            "component": handle_component,
            "date": handle_date,
            "datetime": handle_date,
            "issuetype": handle_issuetype,
            "number": handle_number,
            "option": handle_option,
            "priority": handle_priority,
            "project": handle_project,
            "user": handle_user,
            "version": handle_version,
            "issuelink": handle_issuelink,
            "parent": handle_issuelink,
        }

        # Process each field in `issue_data`
        for field_key, field_value in issue_data.items():
            field_metadata = next(
                (f for f in metadata["fields"] if f["key"] == field_key), None
            )

            if not field_metadata:
                raise ValueError(
                    f"Field '{field_key}' is not valid for this issue type."
                )

            field_type = field_metadata["schema"]["type"]
            field_id = field_metadata["fieldId"]

            # Specific handling for ADF fields
            if field_key in ["description", "environment"] and field_type == "string":
                payload_fields[field_id] = handle_adf_string(field_value)
            else:
                handler = field_handlers.get(field_type)
                if handler:
                    payload_fields[field_id] = handler(field_metadata, field_value)
                else:
                    raise ValueError(
                        f"No handler for field type '{field_type}' on field '{field_key}'."
                    )

        # Ensure all required fields are provided or have default values
        missing_fields = [
            key
            for key, field in required_fields.items()
            if key not in issue_data and not field.get("hasDefaultValue", False)
        ]
        if missing_fields:
            raise ValueError(
                f"Missing required fields without default values: {', '.join(missing_fields)}"
            )

        return {"fields": payload_fields, "update": {}}
