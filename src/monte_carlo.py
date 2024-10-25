import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from workalendar.america import Brazil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def monte_carlo_simulation(
    epics: List[Dict[str, Any]],
    planning_cycle: str,
    cycle_start_date: str,
    cycle_end_date: str,
    total_developers: int,
    days_out_of_team: int,
    num_simulations=10000,
):
    try:
        # Convert the list of dictionaries to a DataFrame for easier processing
        df = pd.DataFrame(epics)

        if df.empty:
            logger.error(
                "The input data is empty. Please provide a valid list of epic data."
            )
            return

        # Filter the data for the planning cycle
        if "first_fix_version" not in df.columns:
            logger.error(
                "The input data does not contain the 'first_fix_version' field."
            )
            return

        planning_df = df[df["first_fix_version"] == planning_cycle]

        if planning_df.empty:
            logger.error(f"No data found for the planning cycle '{planning_cycle}'.")
            return

        # Calculate number of epics in the planning cycle
        num_items = len(planning_df)

        # Prepare historical data
        historical_df = df[
            df["executed_days"].notna()
            & df["devs_used"].notna()
            & df["devs_planned"].notna()
        ]

        # Use historical data to derive statistics for executed days
        if not historical_df.empty:
            # Mean and standard deviation of executed days
            historical_mean = historical_df["executed_days"].mean()
            historical_std = (
                historical_df["executed_days"].std() or 1
            )  # Avoid division by zero

            # Compute adjustment factor: how often `devs_used` differs from `devs_planned`
            historical_df["devs_adjustment_factor"] = (
                historical_df["devs_used"] / historical_df["devs_planned"]
            )
            adjustment_mean = historical_df["devs_adjustment_factor"].mean()
            adjustment_std = historical_df["devs_adjustment_factor"].std() or 0
        else:
            historical_mean = 0
            historical_std = 0
            adjustment_mean = 1
            adjustment_std = 0

        # Use both estimates and historical data for expected times
        expected_times = []
        for _, row in planning_df.iterrows():
            best = row["best_estimate"]
            worst = row["worst_estimate"]
            planned = row["planned_days"]
            devs_planned = row.get("devs_planned", np.nan)

            # Ensure that if devs_planned is NaN or invalid, we use a sensible default
            devs_planned = (
                1 if pd.isna(devs_planned) or devs_planned <= 0 else devs_planned
            )

            # Apply adjustment factor to `devs_planned`
            # We simulate an adjusted `devs_planned` based on historical variability
            adjusted_devs_planned = devs_planned * (
                adjustment_mean + np.random.normal(0, adjustment_std)
            )

            # Ensure historical data is valid for executed days adjustment
            if (
                pd.isna(historical_mean)
                or pd.isna(historical_std)
                or historical_std == 0
            ):
                historical_mean = 0
                historical_std = 0

            # PERT estimation with adjustment using historical mean/std
            if pd.notna(best) and pd.notna(worst) and pd.notna(planned):
                pert_estimate = (best + 4 * planned + worst) / 6
                if (
                    historical_std > 0
                ):  # Only adjust if we have a meaningful std deviation
                    pert_estimate += np.random.normal(historical_mean, historical_std)
                pert_estimate /= max(
                    adjusted_devs_planned, 1
                )  # Adjust estimate based on adjusted devs
                expected_times.append(pert_estimate)

            elif pd.notna(planned):
                # Use historical mean/std to adjust planned days if no estimates available
                estimate = planned
                if (
                    historical_std > 0
                ):  # Only adjust if we have a meaningful std deviation
                    estimate += np.random.normal(historical_mean, historical_std)
                estimate /= max(
                    adjusted_devs_planned, 1
                )  # Adjust estimate based on adjusted devs
                expected_times.append(estimate)

        # Remove any NaN values that may have been added unexpectedly
        expected_times = [time for time in expected_times if pd.notna(time)]

        # Combine the adjusted expected times
        if len(expected_times) == 0:
            logger.error(
                "No valid estimates available for the planning cycle after processing."
            )
            return

        # Calendar settings to get available working days
        try:
            cal = Brazil()  # Updated to use the Brazil calendar
            cycle_start_date = pd.Timestamp(cycle_start_date)
            cycle_end_date = pd.Timestamp(cycle_end_date)

            # Calculate the total number of workdays available
            available_workdays = cal.get_working_days_delta(
                cycle_start_date, cycle_end_date
            )

        except Exception as e:
            logger.error(
                f"Error calculating working days between {cycle_start_date} and "
                f"{cycle_end_date}: {e}"
            )
            return

        # Correct Developer Capacity Handling
        if total_developers <= 0:
            logger.error("Total developers must be greater than zero.")
            return

        if days_out_of_team < 0:
            logger.error("Days out of the team cannot be negative.")
            return

        # Calculate total developer capacity
        total_developer_capacity = (
            available_workdays * total_developers - days_out_of_team
        )

        logger.info(
            f"Available workdays: {available_workdays}, Total developers: {total_developers}, "
            f"Days out of team: {days_out_of_team}"
        )
        logger.info(
            f"Total developer capacity (in developer-days): {total_developer_capacity}"
        )

        # Monte Carlo Simulation
        try:
            results = []
            for _ in range(num_simulations):
                sampled_times = np.random.choice(expected_times, num_items)
                total_days = sum(sampled_times)
                results.append(total_days)

            # Convert results to numpy array for analysis
            results = np.array(results)

            # Calculate the probability of completing within the available developer capacity
            probability_on_time = np.mean(results <= total_developer_capacity)

            # Calculate how far we are likely to be if we miss the deadline
            # (average overdue developer-days)
            overdue_days = (
                results[results > total_developer_capacity] - total_developer_capacity
            )
            avg_overdue_days = np.mean(overdue_days) if len(overdue_days) > 0 else 0

            # Calculate P50, P85, P95
            p50 = np.percentile(results, 50)
            p85 = np.percentile(results, 85)
            p95 = np.percentile(results, 95)

            # Print the results
            logger.info(
                (
                    f"P50: {p50:.2f} developer-days, "
                    f"P85: {p85:.2f} developer-days, "
                    f"P95: {p95:.2f} developer-days"
                )
            )
            logger.info(
                f"Probability of completing on time: {probability_on_time * 100:.2f}%"
            )
            if avg_overdue_days > 0:
                logger.info(
                    (
                        f"Average overdue developer-days if missed: "
                        f"{avg_overdue_days:.2f} developer-days"
                    )
                )
            else:
                logger.info("All simulations completed within the deadline.")

        except Exception as e:
            logger.error(f"Error during Monte Carlo simulation: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
