from pydantic import BaseModel
from models.custom_types import FullMonthStr

class StartEndEngagement(BaseModel):
    """
    Represents a date range for engagement data.

    Attributes:
        start_month (FullMonthStr): The starting month of the engagement period in full month string format (e.g., "January 2023").
        end_month (FullMonthStr): The ending month of the engagement period in full month string format (e.g., "December 2023").
    """
    start_month: FullMonthStr
    end_month: FullMonthStr

class StartPrevEndEngagement(BaseModel):
    """
    Represents the selection of two time periods for MOM (Month over Month) analysis.

    Attributes:
        start_month (FullMonthStr): The start month of the engagement period in full month string format (e.g., "January 2023").
        previous_month (FullMonthStr): The previous month of the engagement period in full month string format (e.g., "December 2022").
        end_month (FullMonthStr): The end month of the engagement period in full month string format (e.g., "December 2023").
    """
    start_month: FullMonthStr
    previous_month: FullMonthStr
    end_month: FullMonthStr


class HevPeriods(BaseModel):
    """
    Represents the selection of two time periods for HEV (Household Engagement Value) analysis.

    Attributes:
        curr_period_end (FullMonthStr): The end month of the current period in full month string format (e.g., "December 2023").
        curr_period_start (FullMonthStr): The start month of the current period in full month string format (e.g., "January 2023").
        prev_period_end (FullMonthStr): The end month of the previous period in full month string format (e.g., "December 2022").
        prev_period_start (FullMonthStr): The start month of the previous period in full month string format (e.g., "January 2022").
    """
    curr_period_end: FullMonthStr
    curr_period_start: FullMonthStr
    prev_period_end: FullMonthStr
    prev_period_start: FullMonthStr