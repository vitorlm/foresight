from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd


@dataclass
class Epic:
    """
    Represents an Epic in a project management system. An Epic is a larger body of
    work that can be broken down into smaller tasks or stories,
    often representing a business feature or project goal.

    Attributes:
        key (str): Unique identifier for the Epic, e.g., "CWS-XXXXX".
        summary (str): A brief description of the Epic's purpose or content.
        status (str): The current status of the Epic.
        components (Optional[List[str]]): List of components associated with the Epic.
        fix_versions (Optional[List[str]]): Versions associated with this Epic.
        planned_start_date (Optional[pd.Timestamp]): The planned start date of the Epic.
        planned_end_date (Optional[pd.Timestamp]): The planned end date of the Epic.
        start_date (Optional[pd.Timestamp]): The actual start date of the Epic.
        due_date (Optional[pd.Timestamp]): The due date assigned for the Epic's completion.
        end_date (Optional[pd.Timestamp]): The actual end date when the Epic was completed.
        status_of_start (Optional[str]): Status of whether the Epic started on time or was delayed.
        delay_in_start (Optional[int]): The number of days delayed in starting the Epic.
        current_status (Optional[str]): The current status of the Epic.
        delay_vs_planned (Optional[int]): The number of working days overdue beyond the planned
        end date.
        updated_status (Optional[str]): The latest status of the Epic.
        delay_vs_due_date (Optional[int]): The number of working days delayed compared
        to the due date.
        days_in_progress (Optional[int]): The number of working days the Epic has been in progress.
        remaining_work_days (Optional[int]): The estimated number of working days remaining
        to complete the Epic.
        first_fix_version (Optional[str]): The first fix version associated with this Epic.
        cycle (Optional[str]): The cycle to which this Epic belongs.
        planned_days (Optional[int]): The number of days originally planned for completion.
        executed_days (Optional[int]): The actual number of days taken to complete the work.
        devs_planned (Optional[int]): The number of developers initially planned for the work.
        devs_used (Optional[int]): The number of developers actually assigned.
        worst_estimate (Optional[str]): The worst-case estimate for completion.
        best_estimate (Optional[str]): The best-case estimate for completion.
        assignee (Optional[str]): The current assignee of the Epic.
        labels (Optional[List[str]]): Labels or tags associated with the Epic.
    """

    # Mandatory fields
    key: str
    summary: str
    status: str

    # Optional fields with default values
    components: Optional[List[str]] = field(default_factory=list)
    fix_versions: Optional[List[str]] = field(default_factory=list)
    planned_start_date: Optional[pd.Timestamp] = None
    planned_end_date: Optional[pd.Timestamp] = None
    start_date: Optional[pd.Timestamp] = None
    due_date: Optional[pd.Timestamp] = None
    end_date: Optional[pd.Timestamp] = None
    status_of_start: Optional[str] = None
    delay_in_start: Optional[int] = None
    current_status: Optional[str] = None
    delay_vs_planned: Optional[int] = None
    updated_status: Optional[str] = None
    delay_vs_due_date: Optional[int] = None
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
    labels: Optional[List[str]] = field(default_factory=list)

    def __init__(self, key: str, summary: str, status: str, **kwargs):
        """
        Initializes an Epic with mandatory fields and optional fields.

        Args:
            key (str): Unique identifier for the Epic.
            summary (str): A brief description of the Epic.
            status (str): The current status of the Epic.
            **kwargs: Optional attributes for the Epic, passed as keyword arguments.
        """
        self.key = key
        self.summary = summary
        self.status = status

        # Initialize optional fields with keyword arguments
        for field_name, value in kwargs.items():
            if hasattr(self, field_name):
                setattr(self, field_name, value)

    @classmethod
    def from_dict(cls, data: dict) -> "Epic":
        """
        Creates an instance of Epic from a dictionary.

        Args:
            data (dict): A dictionary containing Epic attributes.

        Returns:
            Epic: An Epic instance populated with the provided data.
        """
        mandatory_fields = {
            k: data[k] for k in ["key", "summary", "status"] if k in data
        }
        optional_fields = {k: v for k, v in data.items() if k not in mandatory_fields}

        # Handle specific field types like lists or timestamp conversion
        if "components" in optional_fields and isinstance(
            optional_fields["components"], str
        ):
            optional_fields["components"] = optional_fields["components"].split(";")
        if "fix_versions" in optional_fields and isinstance(
            optional_fields["fix_versions"], str
        ):
            optional_fields["fix_versions"] = optional_fields["fix_versions"].split(";")
        if "labels" in optional_fields and isinstance(optional_fields["labels"], str):
            optional_fields["labels"] = optional_fields["labels"].split(";")
        for date_field in [
            "planned_start_date",
            "planned_end_date",
            "start_date",
            "due_date",
            "end_date",
        ]:
            if date_field in optional_fields and isinstance(
                optional_fields[date_field], str
            ):
                optional_fields[date_field] = pd.to_datetime(
                    optional_fields[date_field]
                )

        return cls(**mandatory_fields, **optional_fields)

    def update_attributes(self, data: dict):
        """
        Updates the attributes of the Epic instance based on a given dictionary of data.

        Args:
            data (dict): A dictionary containing key-value pairs to update the Epic attributes.
        """
        for key, value in data.items():
            if hasattr(self, key) and value is not None:
                if key in ["components", "fix_versions", "labels"] and isinstance(
                    value, str
                ):
                    value = value.split(";")
                setattr(self, key, value)

    def serialize(self) -> dict:
        """
        Serializes the Epic instance into a dictionary for JSON representation.

        Returns:
            dict: A dictionary representation of the Epic instance, properly formatted for JSON.
        """

        def convert_value(value):
            if isinstance(value, pd.Timestamp):
                return value.isoformat() if pd.notnull(value) else None
            if isinstance(value, list):
                return ";".join(value)
            return value

        return {k: convert_value(v) for k, v in self.__dict__.items()}
