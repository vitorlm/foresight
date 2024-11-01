import argparse
import logging

from src.services.managers.jira_manager import JiraManager
from src.utils.logging_config import configure_logging

# Configure logging for the CLI
configure_logging()
logger = logging.getLogger(__name__)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description=(
            "CLI for managing various Jira operations, "
            "including updating epic dates and running simulations."
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

    # Sub-command to bulk create issues from JSON
    create_parser = subparsers.add_parser(
        "create", help="Create a task from a JSON file."
    )
    create_parser.add_argument(
        "--json-path",
        type=str,
        required=True,
        help="Path to the JSON file containing task data.",
    )

    # Sub-command to bulk create issues from JSON
    bulk_create_parser = subparsers.add_parser(
        "bulk-create", help="Bulk create tasks and subtasks from a JSON file."
    )
    bulk_create_parser.add_argument(
        "--json-path",
        type=str,
        required=True,
        help="Path to the JSON file containing task data.",
    )

    # Parse arguments
    args = parser.parse_args()

    jira_manager = JiraManager()

    # Execute the appropriate function based on the provided sub-command
    if args.command == "update-dates":
        logger.info(
            f"Starting to update dates for completed epics for team '{args.team_name}'"
        )
        jira_manager.fill_missing_dates_for_completed_epics(team_name=args.team_name)
        logger.info(
            f"Finished updating dates for completed epics for team '{args.team_name}'"
        )
    elif args.command == "create":
        logger.info(f"Starting bulk creation from JSON file '{args.json_path}'")
        created_issue = jira_manager.create_issue(args.json_path)
        logger.info(f"Finished bulk creation. Created issues: {created_issue}")
    elif args.command == "bulk-create":
        logger.info(f"Starting bulk creation from JSON file '{args.json_path}'")
        created_issues = jira_manager.create_bulk_issues(args.json_path)
        logger.info(f"Finished bulk creation. Created issues: {created_issues}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
