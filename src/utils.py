import json
import os


def save_data_to_file(data, filename):
    """
    Save data to a specified file in JSON format.
    """
    try:
        with open(filename, "w") as cache_file:
            json.dump(data, cache_file)
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while saving data: {e}")


def load_data_from_file(filename):
    """
    Load data from a specified file in JSON format.
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r") as cache_file:
                return json.load(cache_file)
        return None
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while loading data: {e}")
