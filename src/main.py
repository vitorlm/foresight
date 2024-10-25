import argparse
import logging

from src.services.jira_issue_service import JiraIssueService
from src.utils.logging_config import configure_logging

# Configure logging for the CLI
configure_logging()
logger = logging.getLogger(__name__)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description=(
            "CLI for managing various Jira operations, ",
            "including updating epic dates and running simulations.",
        )
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    # Sub-command to update missing dates for completed epics
    update_dates_parser = subparsers.add_parser(
        "update-dates",
        help="Update the start and end dates for completed epics with missing values.",
    )
    update_dates_parser.add_argument(
        "--team-name",
        type=str,
        required=True,
        help="Name of the team (Squad) to filter epics.",
    )

    # Parse arguments
    args = parser.parse_args()

    # Instantiate the JiraIssueService
    jira_service = JiraIssueService()

    # Execute the appropriate function based on the provided sub-command
    if args.command == "update-dates":
        logger.info(
            f"Starting to update dates for completed epics for team '{args.team_name}'"
        )
        jira_service.fill_missing_dates_for_completed_epics(team_name=args.team_name)
        logger.info(
            f"Finished updating dates for completed epics for team '{args.team_name}'"
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
