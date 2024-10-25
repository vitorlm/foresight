import datetime
import logging
from dataclasses import dataclass, fields
from typing import Any, Dict, Optional

import pandas as pd
from workalendar.america import Brazil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Excel column name to Epic attribute mapping, defined outside of the class
excel_mapping = {
    "Key": "key",
    "Summary": "summary",
    "Status": "status",
    "Components": "components",
    "Fix versions": "fix_versions",
    "Planned Start Date": "planned_start_date",
    "Planned End Date": "planned_end_date",
    "Start date": "start_date",
    "Due date": "due_date",
    "End date": "end_date",
    "Status of Start": "status_of_start",
    "Delay in Start": "delay_in_start",
    "Current Status": "current_status",
    "Delay vs Planned": "delay_vs_planned",
    "Updated Status": "updated_status",
    "Delay vs Due Date": "delay_vs_due_date",
    "Days in Progress": "days_in_progress",
    "Remaining Work Days": "remaining_work_days",
    "First Fix Version": "first_fix_version",
    "Cycle": "cycle",
    "Planned (Days)": "planned_days",
    "Executed (Days)": "executed_days",
    "Devs Planned": "devs_planned",
    "Devs Used": "devs_used",
    "Worst Estimate": "worst_estimate",
    "Best Estimate": "best_estimate",
    "Assignee": "assignee",
    "Labels": "labels",
}


@dataclass
class Epic:
    # Mandatory fields
    key: str
    summary: str
    status: str

    # Optional fields with default values
    components: Optional[str] = None
    fix_versions: Optional[str] = None
    planned_start_date: Optional[pd.Timestamp] = None
    planned_end_date: Optional[pd.Timestamp] = None
    start_date: Optional[pd.Timestamp] = None
    due_date: Optional[pd.Timestamp] = None
    end_date: Optional[pd.Timestamp] = None
    status_of_start: Optional[str] = None
    delay_in_start: Optional[str] = None
    current_status: Optional[str] = None
    delay_vs_planned: Optional[str] = None
    updated_status: Optional[str] = None
    delay_vs_due_date: Optional[str] = None
    days_in_progress: Optional[int] = None
    remaining_work_days: Optional[int] = None
    first_fix_version: Optional[str] = None
    cycle: Optional[str] = None
    planned_days: Optional[int] = None
    executed_days: Optional[int] = None
    devs_planned: Optional[int] = None
    devs_used: Optional[int] = None
    worst_estimate: Optional[str] = None
    best_estimate: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[str] = None

    def matches(self, key: str, summary: str) -> bool:
        """Check if this Epic matches the given key and summary."""
        return self.key == key and self.summary == summary

    def update_from_excel(
        self, excel_data: Dict[str, Any], excel_mapping: Dict[str, str]
    ) -> None:
        """Update Epic attributes from Excel data."""
        try:
            for excel_column, value in excel_data.items():
                # Treat "-" as empty by setting value to None if it's "-"
                if value == "-":
                    value = None

                # Get the attribute name that corresponds to the excel column
                attr_name = excel_mapping.get(excel_column)
                if attr_name:
                    # Check for specific data handling based on attribute type
                    if attr_name.endswith("_date"):
                        # Convert date columns
                        setattr(self, attr_name, pd.to_datetime(value, errors="coerce"))
                    elif attr_name in [
                        "planned_days",
                        "executed_days",
                        "devs_planned",
                        "devs_used",
                        "days_in_progress",
                        "remaining_work_days",
                    ]:
                        # Convert numeric values, setting None for non-numeric or empty values
                        setattr(
                            self,
                            attr_name,
                            (
                                int(value)
                                if pd.notna(value) and value is not None
                                else None
                            ),
                        )
                    else:
                        # Set other attributes directly
                        setattr(self, attr_name, value)

            logger.info(f"Epic {self.key} updated from Excel data successfully.")
        except Exception as e:
            logger.error(f"Failed to update Epic {self.key} from Excel data: {e}")

    def update_from_jira(self, jira_data: Dict[str, Any]) -> None:
        """Update Epic attributes from JIRA API data."""
        try:
            fields = jira_data.get("fields", {})
            if not self.matches(jira_data.get("key"), fields.get("summary")):
                logger.warning(
                    (
                        f"JIRA data does not match this Epic. Expected key: {self.key}, "
                        f"summary: {self.summary}"
                    )
                )
                return

            self.status = fields.get("status", {}).get("name", self.status)
            self.current_status = fields.get("status", {}).get(
                "name", self.current_status
            )
            self.assignee = fields.get("assignee", {}).get("displayName", self.assignee)
            self.labels = ", ".join(fields.get("labels", []))
            self.start_date = pd.to_datetime(
                fields.get("customfield_10015"), errors="coerce"
            )
            self.due_date = pd.to_datetime(fields.get("duedate"), errors="coerce")

            # Calculate days in progress
            self.days_in_progress = self._calculate_time_in_progress(
                jira_data.get("changelog", {})
            )

            logger.info(f"Epic {self.key} updated from JIRA data successfully.")
        except Exception as e:
            logger.error(f"Failed to update Epic {self.key} from JIRA data: {e}")

    def _calculate_time_in_progress(self, changelog: Dict[str, Any]) -> Optional[int]:
        """Calculate the time an Epic was in progress based on its changelog."""
        try:
            # Track the dates of "7 PI Started" and "Done" status changes
            status_changes = {"7 PI Started": None, "Done": None}

            # Iterate through each history record in the changelog
            for history in changelog.get("histories", []):
                for item in history.get("items", []):
                    # Check if the field is "status" and it is either "7 PI Started" or "Done"
                    if item["field"] == "status" and item["toString"] in status_changes:
                        # Set the status change date for either "7 PI Started" or "Done"
                        status_changes[item["toString"]] = datetime.datetime.strptime(
                            history["created"], "%Y-%m-%dT%H:%M:%S.%f%z"
                        ).date()

                # Stop iterating if both statuses have been set
                if status_changes["7 PI Started"] and status_changes["Done"]:
                    break

            # Calculate the working days between "7 PI Started" and "Done" if both dates are present
            if status_changes["7 PI Started"] and status_changes["Done"]:
                cal = Brazil()
                return cal.get_working_days_delta(
                    status_changes["7 PI Started"], status_changes["Done"]
                )

            # Return None if either status is missing
            return None
        except Exception as e:
            logger.error(
                f"Failed to calculate time in progress for Epic {self.key}: {e}"
            )
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Epic object to a dictionary that can be JSON serialized."""

        def serialize_value(value):
            if pd.isna(value):
                return None
            if isinstance(value, pd.Timestamp):
                return value.isoformat()
            return value

        return {
            field.name: serialize_value(getattr(self, field.name))
            for field in fields(self)
        }
