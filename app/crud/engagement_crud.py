from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
import time

def timeit(func):
    """
    A decorator to measure the execution time of a function.
    
    :param func: The function to be timed
    :return: Wrapper function
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds to execute.")
        return result
    return wrapper


# Engagement Data Range Query (for engagement header)
def get_engagement_data_range(db: Session) -> Dict[str, str]: 
    """
    Get the range of dates that the engagement data spans.
    """
    result = db.execute(
        text(
            "SELECT MIN(DATE(CONCAT(year, '-', month, '-01'))), "
            "MAX(DATE(CONCAT(year, '-', month, '-01'))) "
            "FROM main.engagement_raw"
        )
    )
    oldest_month, most_current_month = result.fetchone()
    return {
        "oldest_month": oldest_month,
        "most_current_month": most_current_month
    }

def get_engagement_data_one_month(db: Session, month: int, year: int) -> pd.DataFrame:
    """
    Fetch engagement data for a specific month.
    """
    query = f"""
        SELECT
            e.month, 
            e.year, 
            e.tiername,
            e.network,
            e.specnewsmarket, 
            e.adjeng, 
            e.subs, 
            r.region, 
            r.state, 
            r.clean_prg_name_all,
            s.stn_grp,
            launch_date
        FROM (
            SELECT * 
            FROM main.engagement_raw
            WHERE year = {year} 
                AND month = {month}
        ) e
        JOIN main.market_region_mapping r
            ON e.specnewsmarket = r.specnewsmarket
        JOIN main.network_stn_grp s 
            ON e.network = s.network
        WHERE TO_DATE(e.year || '-' || LPAD(e.month::text, 2, '0'), 'YYYY-MM') >= launch_date
            AND s.stn_grp IN ('Big 4', 'Cable News', 'SN')
            AND tiername != 'FALSE'
    """
    df = pd.read_sql_query(
        text(query),
        db.connection()
    )

    return df
 


# Main Engagement Query
@timeit
def get_engagement_data(
    db: Session,
    start_month: str,
    end_month: str,
    networks: Optional[List[str]] = None,
    include_false_tier: bool = False
) -> pd.DataFrame:
    """
    Fetch engagement data from the database based on specified parameters.

    :param db: Database session
    :param start_month: Start date in 'YYYY-MM' format
    :param end_month: End date in 'YYYY-MM' format
    :param networks: List of networks to include (default is ['Big 4', 'Cable News', 'SN'])
    :param include_false_tier: Whether to include 'FALSE' tier data
    :return: DataFrame with engagement data
    """
    networks = networks or ['Big 4', 'Cable News', 'SN']
    networks_str = ', '.join(f"'{network}'" for network in networks)

    tier_condition = "" if include_false_tier else "AND e.tiername != 'FALSE'"

    query = f"""
    SELECT
        e.year,
        e.month,
        e.tiername,
        e.network,
        e.specnewsmarket, 
        e.adjeng, 
        e.subs, 
        r.region, 
        r.state, 
        r.clean_prg_name_all,
        s.stn_grp,
        r.launch_date
    FROM main.engagement_raw e
    JOIN main.market_region_mapping r ON e.specnewsmarket = r.specnewsmarket
    JOIN main.network_stn_grp s ON e.network = s.network
    WHERE TO_CHAR(TO_DATE(e.year || '-' || LPAD(e.month::text, 2, '0'), 'YYYY-MM'), 'YYYY-MM') 
        BETWEEN :start_month AND :end_month
    AND s.stn_grp IN ({networks_str})
    {tier_condition}
    AND TO_DATE(e.year || '-' || LPAD(e.month::text, 2, '0'), 'YYYY-MM') >= r.launch_date
    ORDER BY e.year, e.month, e.network, e.specnewsmarket
    """

    df = pd.read_sql_query(
        text(query),
        db.connection(),
        params={"start_month": start_month, "end_month": end_month}
    )

    return df


# Periodicity Query
def get_periodicity_data(
    db: Session,
    fiscal_month: Optional[int] = None,
    networks: Optional[List[str]] = None,
    multiple_months: bool = False,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None
) -> pd.DataFrame:
    """ 
    Fetch periodicity data from the database for a specific fiscal month.

    :param db: Database session
    :param fiscal_month: Fiscal month in YYYYMM format (e.g., 202401 for January 2024)
    :param networks: List of networks to include (default is None, which includes all networks)
    :return: DataFrame with periodicity data
    """
    networks_condition = ""
    if networks:
        networks_str = ', '.join(f"'{network}'" for network in networks)
        networks_condition = f"AND network IN ({networks_str})"

    query = f"""
    SELECT 
        fiscalmonth,
        network,
        specnewsmarket,
        periodicity
    FROM main.periodicity
    WHERE fiscalmonth = :fiscal_month
    {networks_condition}
    ORDER BY network, specnewsmarket
    """

    if multiple_months:
        query = f"""
        SELECT 
            fiscalmonth,
            network,
            specnewsmarket,
            periodicity
        FROM main.periodicity
        WHERE fiscalmonth BETWEEN :start_month AND :end_month
        {networks_condition}
        ORDER BY network, specnewsmarket
        """
        params = {"start_month": start_month, "end_month": end_month}
    else:
        params = {"fiscal_month": fiscal_month}         

    df = pd.read_sql_query(
        text(query),
        db.connection(),
        params=params
    )

    # Replace 'FOX NEWS' with 'FOX NEWS CHANNEL' for consistency
    df['network'] = df['network'].replace('FOX NEWS', 'FOX NEWS CHANNEL')

    return df

def get_periodicity_history( 
    db: Session,
    start_month: str,
    end_month: str,
    networks: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Fetch periodicity history data from the database for a specific fiscal month.
    """
    query = f"""
    SELECT 
        p.fiscalmonth,
        p.network,
        p.specnewsmarket,
        p.periodicity,
        r.region,
        r.state,
        r.clean_prg_name_all
    FROM main.periodicity p
    JOIN main.market_region_mapping r ON p.specnewsmarket = r.specnewsmarket
    WHERE p.fiscalmonth BETWEEN :start_month AND :end_month
    ORDER BY network, specnewsmarket
    """

    df = pd.read_sql_query(
        text(query),
        db.connection(),
        params={"start_month": start_month, "end_month": end_month}
    )

    return df
    
    



@timeit
def get_engagement_data_fast(
    db: Session,
    start_month: str,
    end_month: str,
    networks: Optional[List[str]] = None,
    include_false_tier: bool = False
) -> pd.DataFrame:
    """
    Fetch engagement data from the database based on specified parameters. 

    :param db: Database session
    :param start_month: Start date in 'YYYY-MM' format
    :param end_month: End date in 'YYYY-MM' format
    :param networks: List of networks to include (default is ['Big 4', 'Cable News', 'SN'])
    :param include_false_tier: Whether to include 'FALSE' tier data
    :return: DataFrame with engagement data
    """
    networks = networks or ['Big 4', 'Cable News', 'SN']
    networks_str = ', '.join(f"'{network}'" for network in networks)

    tier_condition = "" if include_false_tier else "AND e.tiername != 'FALSE'"

    query = f"""
    SELECT
        e.year,
        e.month,
        e.tiername,
        e.network,
        e.specnewsmarket, 
        e.adjeng, 
        e.subs, 
        r.region, 
        r.state, 
        r.clean_prg_name_all,
        s.stn_grp,
        r.launch_date
    FROM main.engagement_raw e
    JOIN main.market_region_mapping r ON e.specnewsmarket = r.specnewsmarket
    JOIN main.network_stn_grp s ON e.network = s.network
    WHERE e.year || '-' || LPAD(e.month::text, 2, '0') BETWEEN :start_month AND :end_month
    AND s.stn_grp IN ({networks_str})
    {tier_condition}
    AND e.year || '-' || LPAD(e.month::text, 2, '0') >= TO_CHAR(r.launch_date, 'YYYY-MM')
    ORDER BY e.year, e.month, e.network, e.specnewsmarket
    """

    df = pd.read_sql_query(
        text(query),
        db.connection(),
        params={"start_month": start_month, "end_month": end_month}
    )

    return df

