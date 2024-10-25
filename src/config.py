import os

from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()

# Configuration Variables
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")
