from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger("utils")


def format_journey_date(date_str: str) -> str:
    """
    Format the journey date string according to the required format (DD-MMM-YYYY).

    Args:
        date_str (str): Date string or special format like "auto" or "auto+N"

    Returns:
        str: Formatted date string
    """
    if date_str.lower().startswith("auto"):
        # Parse days offset if specified (e.g., "auto+7")
        days_offset = 0
        if "+" in date_str:
            try:
                days_offset = int(date_str.split("+")[1])
            except ValueError:
                logger.warning(f"Invalid auto date format: {date_str}. Using today + 0 days.")

        # Calculate the target date
        target_date = datetime.now() + timedelta(days=days_offset)
        return target_date.strftime("%d-%b-%Y")

    return date_str 