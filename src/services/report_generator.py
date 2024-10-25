import json
import logging
import os

import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Service to generate reports from provided data."""

    def __init__(self, output_dir="../data/reports/"):
        """
        Initialize the ReportGenerator with a directory for output.

        :param output_dir: Directory where reports will be saved.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_json_report(self, data, file_name):
        """
        Generate a JSON report from the given data.

        :param data: Data to be written to the JSON report.
        :param file_name: Name of the JSON file to be created.
        """
        try:
            file_path = os.path.join(self.output_dir, file_name)
            with open(file_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
            logger.info(f"JSON report generated successfully at: {file_path}")
        except Exception as e:
            logger.error(f"Failed to generate JSON report {file_name}: {e}")

    def generate_csv_report(self, data, file_name):
        """
        Generate a CSV report from the given data.

        :param data: Data to be written to the CSV report
                     (must be in a list of dictionaries or DataFrame).
        :param file_name: Name of the CSV file to be created.
        """
        try:
            file_path = os.path.join(self.output_dir, file_name)
            if isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            elif isinstance(data, list) and all(
                isinstance(item, dict) for item in data
            ):
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            else:
                raise ValueError(
                    "Data must be a list of dictionaries or a pandas DataFrame."
                )
            logger.info(f"CSV report generated successfully at: {file_path}")
        except ValueError as e:
            logger.error(f"Invalid data format for CSV report {file_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to generate CSV report {file_name}: {e}")
