import logging
import os

import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelReader:
    """Service to read data from Excel files."""

    def __init__(self, file_path):
        """
        Initialize the ExcelReader with the path to the Excel file.

        :param file_path: Path to the Excel file.
        """
        if not os.path.exists(file_path):
            logger.error(f"Excel file not found at: {file_path}")
            raise FileNotFoundError(f"Excel file not found at: {file_path}")
        self.file_path = file_path

    def read_data(self, sheet_name=None):
        """
        Read data from the Excel file, optionally specifying a sheet name.

        :param sheet_name: The name of the sheet to read from. If None, the first sheet is used.
        :return: Data read from the Excel file as a pandas DataFrame.
        """
        try:
            data = pd.read_excel(self.file_path, sheet_name=sheet_name)
            logger.info(
                f"Data read successfully from Excel file: {self.file_path}, "
                f"Sheet: {sheet_name or 'first'}"
            )
            return data
        except ValueError as e:
            logger.error(
                f"Error while reading sheet '{sheet_name}' from Excel file {self.file_path}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error while reading Excel file {self.file_path}: {e}"
            )
            return None

    def read_data_as_dict(self, sheet_name=None, key_column=None):
        """
        Read data from the Excel file and return it as a dictionary.

        :param sheet_name: The name of the sheet to read from.
        :param key_column: The column to use as keys for the dictionary.
        :return: Data as a dictionary where keys are the values from `key_column`.
        """
        try:
            df = self.read_data(sheet_name)
            if df is None:
                return None
            if key_column and key_column in df.columns:
                data_dict = df.set_index(key_column).to_dict(orient="index")
                logger.info(
                    f"Data from Excel file {self.file_path} read as dictionary successfully."
                )
                return data_dict
            else:
                logger.warning(
                    f"Key column '{key_column}' not found in the Excel sheet."
                )
                return None
        except Exception as e:
            logger.error(f"Error while converting Excel data to dictionary: {e}")
            return None
