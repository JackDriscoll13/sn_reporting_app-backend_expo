from datetime import datetime

def validate_month_format(value: str) -> str:
    """
    Validates that a string is in the format 'Month Year' (e.g., 'January 2022').

    :param value: The string to validate
    :type value: str
    :return: The validated string
    :rtype: str
    :raises ValueError: If the string is not in the correct format
    """
    try:
        datetime.strptime(value, "%B %Y")
        return value
    except ValueError:
        raise ValueError(f"Invalid month format. Expected 'Month Year' (e.g., 'January 2022'), got '{value}'")