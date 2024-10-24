# Fast Api Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import time

# Dependencies
#from connect_db import connect_db
from dependencies import get_db

# Models
from app.models.engagement_schemas import StartEndEngagement, StartPrevEndEngagement, HevPeriods
from models.api_responses import StandardAPIResponse, EngagementAPIResponse, ErrorAPIResponse

# Crud Operations
from crud import engagement_crud as eng_crud

# Services, these are our pivot tables and mappings 
import transformations.engagement.engagement_utils as eng_utils
import transformations.engagement.ytd_engagement as ytd_transforms
import transformations.engagement.mom_engagement as mom_transforms
import transformations.engagement.over_time_engagement as over_time_transforms
import transformations.engagement.rank_engagement as rank_transforms
import transformations.engagement.special_rank_engagement as ovt_rank_transforms
import transformations.engagement.hev_engagement as hev_transforms
import transformations.engagement.quarterly_engagement as quarter_transforms
import transformations.engagement.yearly_engagement as yearly_transforms
import transformations.engagement.periodicity_engagement as periodicity_transforms




router = APIRouter()
# TODO: Add clean docstrings to all endpoints


@router.get("/data_range", response_model=StandardAPIResponse)
def get_engagement_data_range(db: Session = Depends(get_db)):
    """
    Get the range of engagement data. Simple endpoint to get the oldest and most current month of engagement data.
    """
    try: 
        result = eng_crud.get_engagement_data_range(db)
        oldest_month = result["oldest_month"]
        most_current_month = result["most_current_month"]
        # Construct the response, converting into abbreieated MMM YYYY format
        response = {
            "oldest_month": datetime.strptime(oldest_month.strftime("%Y-%m"), "%Y-%m").strftime("%b %Y"),
            "most_current_month": datetime.strptime(most_current_month.strftime("%Y-%m"), "%Y-%m").strftime("%b %Y"),
        }

        return StandardAPIResponse(success=True, message="Data retrieved successfully", data=response, metadata=None)
    except Exception as e:
        return ErrorAPIResponse(success=False, message="Failed to retrieve data", error_code="engagement_data_range_error", error_details={"error_message": str(e)})


# YTD Engagement Endpoint 
@router.post("/ytd", response_model=EngagementAPIResponse)
def get_engagement_ytd(date_range: StartEndEngagement, db: Session = Depends(get_db)):
    """
    Retrieve the the YTDengagement data for the over time feature in the engagement report. 

    Parameters:
    - date_range (StartEndEngagement): Contains start_month and end_month in the format "MMMM YYYY".
      Note: In this endpoint, start_month refers to the begininn of the calendar year, and end_month refers to the current month.
    - db (Session): Database session.

    Returns: 
    - Three DataFrames: 
        - YTD SN
        - YTD Cable
        - YTD Big 4
    """
    # Convert the start and end months to the format YYYY-MM
    start_month_str = datetime.strptime(date_range.start_month, "%B %Y").strftime("%Y-%m")
    end_month_str = datetime.strptime(date_range.end_month, "%B %Y").strftime("%Y-%m")

    # Query the database for the engagement data, previous period engagemnt and periodicity
    engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=start_month_str, end_month=end_month_str,
                                                   networks=None, include_false_tier=True)

    start_month_int = int(datetime.strptime(date_range.start_month, "%B %Y").strftime("%Y%m"))
    end_month_int = int(datetime.strptime(date_range.end_month, "%B %Y").strftime("%Y%m"))
    # Query the database for the HEV data
    periodicity_df:pd.DataFrame = eng_crud.get_periodicity_data(db=db, multiple_months=True, start_month=int(start_month_int), end_month=int(end_month_int))

    engagement_df['fiscalmonth'] = engagement_df['year'].astype(str) + engagement_df['month'].astype(str).str.zfill(2)
    engagement_df['fiscalmonth'] = engagement_df['fiscalmonth'].astype(int)
    merged_df = pd.merge(engagement_df, periodicity_df, 
                     on=['fiscalmonth', 'network', 'specnewsmarket'],
                     how='inner')

    print(merged_df.head())
    merged_df['hev'] = (merged_df['periodicity']/100) * merged_df['adjeng']

    # Get the current month and foy date
    curr_month_date = datetime.strptime(date_range.end_month, "%B %Y").date()
    foy_date = datetime.strptime(date_range.start_month, "%B %Y").date()


    # Filter by network group 
    df_ytd_sn = merged_df[merged_df['stn_grp'] == 'SN']
    df_ytd_cable = merged_df[merged_df['stn_grp'] == 'Cable News']
    df_ytd_big4 = merged_df[merged_df['stn_grp'] == 'Big 4']

    # TODO: Parallelize these transformations
    state_ytd_sn = ytd_transforms.pivot_ytd_engagement(df_ytd_sn, 'state', curr_month_date, foy_date)
    market_ytd_sn = ytd_transforms.pivot_ytd_engagement(df_ytd_sn, 'clean_prg_name_all', curr_month_date, foy_date)
    ytd_combined_sn = ytd_transforms.concatenate_ytd_state_market(state_ytd_sn, market_ytd_sn)

    state_ytd_cable = ytd_transforms.pivot_ytd_engagement(df_ytd_cable, 'state', curr_month_date, foy_date)
    market_ytd_cable = ytd_transforms.pivot_ytd_engagement(df_ytd_cable, 'clean_prg_name_all', curr_month_date, foy_date)
    ytd_combined_cable = ytd_transforms.concatenate_ytd_state_market(state_ytd_cable, market_ytd_cable)

    state_ytd_big4 = ytd_transforms.pivot_ytd_engagement(df_ytd_big4, 'state', curr_month_date, foy_date)
    market_ytd_big4 = ytd_transforms.pivot_ytd_engagement(df_ytd_big4, 'clean_prg_name_all', curr_month_date, foy_date)
    ytd_combined_big4 = ytd_transforms.concatenate_ytd_state_market(state_ytd_big4, market_ytd_big4)    


    print(ytd_combined_sn.head())
    # Convert to JSON
    try:
        ytd_sn_json = ytd_combined_sn.to_dict(orient="records")
        ytd_cable_json = ytd_combined_cable.to_dict(orient="records")
        ytd_big4_json = ytd_combined_big4.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



    return EngagementAPIResponse(success=True, message="Data retrieved successfully",
            data={"ytd_sn": ytd_sn_json, "ytd_cable": ytd_cable_json, "ytd_big4": ytd_big4_json}, 
            metadata={'data_columns': ytd_combined_sn.columns.to_list()})
    
    


# MOM Engagement Endpoint 
@router.post("/mom", response_model=EngagementAPIResponse)
def get_engagement_mom(start_prev_end: StartPrevEndEngagement, db: Session = Depends(get_db)):
    """
    Retrieve the the raw engagement data for the over time feature in the engagement report. 

    Parameters:
    - date_range (StartPrevEndEngagement): Contains start_month, end_month, and previous_month in the format "MMMM YYYY".
      Note: In this endpoint, start_month refers to 1 year before the current month, and end_month refers to the current month.
    - db (Session): Database session.

    Returns:
    - One DataFrame: 
        1. Current Period MoM 
    """
    # Grab the dates
    start_month_date = datetime.strptime(start_prev_end.start_month, "%B %Y")
    end_month_date = datetime.strptime(start_prev_end.end_month, "%B %Y")
    previous_month_date = datetime.strptime(start_prev_end.previous_month, "%B %Y")

    # Query the database
    start_month_str = start_month_date.strftime("%Y-%m")
    end_month_str = end_month_date.strftime("%Y-%m")
    engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=start_month_str, end_month=end_month_str,
                                                   networks=None, include_false_tier=False)
    
    # Filters and Transformations 
    prev_12_months_df = engagement_df[((engagement_df['year'] > start_month_date.year) | 
                            ((engagement_df['year'] == start_month_date.year) & (engagement_df['month'] >= start_month_date.month))) &
                            ((engagement_df['year'] < previous_month_date.year) | 
                            ((engagement_df['year'] == previous_month_date.year) & (engagement_df['month'] <= previous_month_date.month)))]

    # Previous Month DF
    prev_month_df = engagement_df[(engagement_df['year'] == previous_month_date.year) & (engagement_df['month'] == previous_month_date.month)]

    # Current Month DF 
    current_month_df = engagement_df[(engagement_df['year'] == end_month_date.year) & (engagement_df['month'] == end_month_date.month)]

    # Now we want to pivot and concat each of the dataframes
    mom_state_prev_12 = mom_transforms.pivot_MoM_state(prev_12_months_df)
    mom_market_prev_12 = mom_transforms.pivot_MoM_market(prev_12_months_df)
    mom_combined_prev_12 = mom_transforms.concat_MoM_state_market(mom_state_prev_12, mom_market_prev_12)

    mom_state_prev = mom_transforms.pivot_MoM_state(prev_month_df)
    mom_market_prev = mom_transforms.pivot_MoM_market(prev_month_df)
    mom_combined_prev = mom_transforms.concat_MoM_state_market(mom_state_prev, mom_market_prev)

    mom_state_current = mom_transforms.pivot_MoM_state(current_month_df)
    mom_market_current = mom_transforms.pivot_MoM_market(current_month_df)
    mom_combined_current = mom_transforms.concat_MoM_state_market(mom_state_current, mom_market_current)

    # Finally we want to join the dataframes and rename the columns
    mom_combined_final = mom_transforms.join_rename_MoM_columns(mom_combined_current, mom_combined_prev, mom_combined_prev_12,
                                                 start_prev_end.end_month, start_prev_end.previous_month, start_prev_end.start_month).round(3).reset_index()
    
     # Convert to JSON and return
    try:
        mom_combined_json = mom_combined_final.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return EngagementAPIResponse(success=True, message="Data retrieved successfully", data={"mom_data": mom_combined_json}, metadata={'mom_data_columns': mom_combined_final.columns.to_list()})

    #TODO: Make the transformations asyncronous
@router.post("/over_time", response_model=EngagementAPIResponse)
def get_engagement_over_time(date_range: StartEndEngagement, db: Session = Depends(get_db)):
    """
    Retrieve the the raw engagement data for the over time feature in the engagement report. 

    Parameters:
    - date_range (StartEndEngagement): Contains start_month and end_month in the format "MMMM YYYY".
      Note: In this endpoint, start_month refers to 2 years before the current month, and end_month refers to the current month.
    - db (Session): Database session.

    Returns:
    - Three DataFrames: 
      1. Over time SN data
      2. Over time Cable data
      3. Over time Big 4 data
    """
    # Convert the start and end months to the format YYYY-MM
    start_month_str = datetime.strptime(date_range.start_month, "%B %Y").strftime("%Y-%m")
    end_month_str = datetime.strptime(date_range.end_month, "%B %Y").strftime("%Y-%m")

    # Query the database for the engagement data, previous period engagemnt and periodicity
    engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=start_month_str, end_month=end_month_str,
                                                   networks=None, include_false_tier=False)
    
    # Filter by stn_grp
    df_overtime_sn = engagement_df[engagement_df['stn_grp'] == 'SN']
    df_overtime_cable = engagement_df[engagement_df['stn_grp'] == 'Cable News']
    df_overtime_big4 = engagement_df[engagement_df['stn_grp'] == 'Big 4']

    # The data for each, for now I'm returning the full dataframes with both state and market level data
    overtime_state_sn = over_time_transforms.pivot_overtime_state(df_overtime_sn)
    overtime_market_sn = over_time_transforms.pivot_overtime_market(df_overtime_sn)
    overtime_combined_sn = over_time_transforms.concat_overtime_state_market(overtime_state_sn, overtime_market_sn).round(3).reset_index()

    overtime_state_cable = over_time_transforms.pivot_overtime_state(df_overtime_cable)
    overtime_market_cable = over_time_transforms.pivot_overtime_market(df_overtime_cable)
    overtime_combined_cable = over_time_transforms.concat_overtime_state_market(overtime_state_cable, overtime_market_cable).round(3).reset_index()

    overtime_state_big4 = over_time_transforms.pivot_overtime_state(df_overtime_big4)
    overtime_market_big4 = over_time_transforms.pivot_overtime_market(df_overtime_big4)
    overtime_combined_big4 = over_time_transforms.concat_overtime_state_market(overtime_state_big4, overtime_market_big4).round(3).reset_index()

    # Convert to JSON 
    try:
        overtime_sn_json = overtime_combined_sn.to_dict(orient="records")
        overtime_cable_json = overtime_combined_cable.to_dict(orient="records")
        overtime_big4_json = overtime_combined_big4.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return EngagementAPIResponse(success=True, message="Data retrieved successfully", data={
        "overtime_sn_data": overtime_sn_json,
        "overtime_cable_data": overtime_cable_json,
        "overtime_big4_data": overtime_big4_json
    }, metadata={'data_columns': overtime_combined_sn.columns.to_list()})


# Engagement Rank 
# TODO: Make the database calls and transformations asyncronous
@router.post("/rank", response_model=EngagementAPIResponse)
def get_engagement_rank(date_range: StartEndEngagement, db: Session = Depends(get_db)):
    """
    Retrieve engagement rank data for a specified time range.

    Parameters:
    - date_range (StartEndEngagement): Contains start_month and end_month in the format "MMMM YYYY".
      Note: In this endpoint, start_month refers to 7 months before the current month, and end_month refers to the current month.
    - db (Session): Database session.

    Returns:
    - Two DataFrames: 
      1. Current period rank.
      2. Pivoted rank over time for tab 2 in the rank feature.
    """
    ### DATAFRAME 1 -> Current period rank with competitors ##############
    curr_month_date = datetime.strptime(date_range.end_month, "%B %Y")
    curr_engagement_df = eng_crud.get_engagement_data_one_month(db=db, month=curr_month_date.month, year=curr_month_date.year)

    # Pivot the data
    state_df = rank_transforms.pivot_rank_state(curr_engagement_df)
    market_df = rank_transforms.pivot_rank_market(curr_engagement_df)
    combined_df = rank_transforms.concat_rank_state_market(state_df, market_df).round(3).reset_index()
    ###### END OF DATAFRAME 1 ##########
    ### DATAFRAME 2 -> Pivoted rank over time for tab 2 in the rank feature ##########
    # Convert the start and end months to the format YYYY-MM
    start_month_str = datetime.strptime(date_range.start_month, "%B %Y").strftime("%Y-%m")
    end_month_str = datetime.strptime(date_range.end_month, "%B %Y").strftime("%Y-%m")

    # Query the database for the engagement data, previous period engagemnt and periodicity
    engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=start_month_str, end_month=end_month_str,
                                                   networks=None, include_false_tier=False)
    # Generate the rank overtime dataframe
    start_month_date = datetime.strptime(date_range.start_month, "%B %Y")
    result_df = ovt_rank_transforms.calculate_rank_overtime(engagement_df, start_month_date, curr_month_date)
    ###### END OF DATAFRAME 2 ##########
    try:
        result_json = result_df.to_dict(orient="records")
        combined_json = combined_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    
    return EngagementAPIResponse(success=True, message="Data retrieved successfully", data={"rank_current_period": combined_json, "rank_over_time": result_json}, metadata={'Testing': 'Testing'})



# HEV 
# TODO: Make the database calls  and transforms asyncrounous
@router.post("/hev", response_model=EngagementAPIResponse)
def get_engagement_hev(hev_periods: HevPeriods, db: Session = Depends(get_db)):
    """
    Get the HEV data for a given time range.
    """
    ################### PREVIOUS PERIOD ###################
    # Convert the start and end months to the format YYYY-MM
    prev_period_start_str = datetime.strptime(hev_periods.prev_period_start, "%B %Y").strftime("%Y-%m")
    prev_period_end_str = datetime.strptime(hev_periods.prev_period_end, "%B %Y").strftime("%Y-%m")
    prev_period_int = int(datetime.strptime(hev_periods.prev_period_end, "%B %Y").strftime("%Y%m"))

    # Query the database for the engagement data, previous period engagemnt and periodicity
    prev_engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=prev_period_start_str, end_month=prev_period_end_str,
                                                   networks=None, include_false_tier=False)
    prev_periodicity_df:pd.DataFrame = eng_crud.get_periodicity_data(db=db, fiscal_month=prev_period_int, networks=None)

    # For previous periodicity, we want to include all networks
    prev_periodicity_df['network'] = prev_periodicity_df['network'].replace('FOX NEWS', 'FOX NEWS CHANNEL')
    prev_periodicity_df = prev_periodicity_df.drop(columns=['fiscalmonth' ])

    # We join the two dataframes on the specnewsmarket column, create the HEV_PREV column
    df_prev = pd.merge(prev_engagement_df, prev_periodicity_df, on=['specnewsmarket','network'], how='left')
    df_prev['HEV'] = (df_prev['periodicity']/100) * df_prev['adjeng']

    # Apply Transformations
    pt_hev_prev_market = hev_transforms.pivot_HEV_market(df_prev)
    pt_hev_prev_state = hev_transforms.pivot_HEV_state(df_prev)
    pt_hev_prev = hev_transforms.concat_HEV_state_market(pt_hev_prev_state, pt_hev_prev_market)

    ################### CURRENT PERIOD #########################
    curr_period_start_str = datetime.strptime(hev_periods.curr_period_start, "%B %Y").strftime("%Y-%m")
    curr_period_end_str = datetime.strptime(hev_periods.curr_period_start, "%B %Y").strftime("%Y-%m")
    curr_period_int = int(datetime.strptime(hev_periods.curr_period_start, "%B %Y").strftime("%Y%m"))

    # Query the database for the engagement data, current period
    curr_engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=curr_period_start_str, end_month=curr_period_end_str,
                                                   networks=None, include_false_tier=False)
    curr_periodicity_df:pd.DataFrame = eng_crud.get_periodicity_data(db=db, fiscal_month=curr_period_int, networks=None)
    
    # Clean up the dataframes
    # For the current periodicity, we only want to include SPECNEWS
    curr_periodicity_df['network'] = curr_periodicity_df['network'].replace('FOX NEWS', 'FOX NEWS CHANNEL')
    curr_periodicity_df = curr_periodicity_df.loc[curr_periodicity_df['network'] == 'SPECNEWS']
    curr_periodicity_df = curr_periodicity_df.drop(columns=['fiscalmonth', 'network'])
    
    # We join the two dataframes on the specnewsmarket column, create the HEV_CURR column,
    df_curr = pd.merge(curr_engagement_df, curr_periodicity_df, on='specnewsmarket', how='left')
    df_curr['HEV'] = (df_curr['periodicity']/100) * df_curr['adjeng']

    # Apply Transformations
    pt_hev_curr_market = hev_transforms.pivot_HEV_market(df_curr)
    pt_hev_curr_state = hev_transforms.pivot_HEV_state(df_curr)
    pt_hev_curr = hev_transforms.concat_HEV_state_market(pt_hev_curr_state, pt_hev_curr_market)

    #################### COMBINE PERIODS ######################
    # Calculate the change in HEV between periods
    pt_hev_change = pt_hev_curr[['Big 4', 'Cable News', 'SN']] - pt_hev_prev[['Big 4', 'Cable News', 'SN']]

    # Combine the dataframes and use the dates to create column names
    hev_combined_final = hev_transforms.join_re_order_HEV_columns(pt_hev_curr, pt_hev_prev, pt_hev_change,
                                                   hev_periods.curr_period_start, hev_periods.curr_period_end,
                                                   hev_periods.prev_period_start, hev_periods.prev_period_end).round(3).reset_index()
    # JSON CONVERT
    try:
        hev_combined_json = hev_combined_final.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return EngagementAPIResponse(success=True, message="HEV data retrieved successfully.", data={'hev_data': hev_combined_json}, metadata={'columns': hev_combined_final.columns.to_list()})
    


# Quarterly Engagement Data:
# TODO: Add more robust time loggin, add yearly to this endpoint as well
# TODO: Rename this endpoiint to remove the engagement_ prefix and add yearly when we integrate yearly
# TODO: Parallelize the pivoting of the data to make it faster
@router.post("/engagement_quarterly", response_model=EngagementAPIResponse)
def get_engagement_quarterly(date_range: StartEndEngagement, db: Session = Depends(get_db)):
    """
    Get the quarterly engagement data for a given time range.
    """
    # Convert the start and end months to the format YYYY-MM
    start_month_str = datetime.strptime(date_range.start_month, "%B %Y").strftime("%Y-%m")
    end_month_str = datetime.strptime(date_range.end_month, "%B %Y").strftime("%Y-%m")

    # Query the database for the engagement data, add the type for editor support
    engagement_df:pd.DataFrame = eng_crud.get_engagement_data(db=db, start_month=start_month_str, end_month=end_month_str,
                                                   networks=None, include_false_tier=False)
    df_year = engagement_df.copy()


    # Filter the data
    df_yearly_sn = df_year[df_year['stn_grp'] == 'SN']
    df_yearly_cable = df_year[df_year['stn_grp'] == 'Cable News']
    df_yearly_big4 = df_year[df_year['stn_grp'] == 'Big 4']

    # Pivot the data
    yearly_state_sn = yearly_transforms.pivot_yearly_state(df_yearly_sn)
    yearly_market_sn = yearly_transforms.pivot_yearly_market(df_yearly_sn)
    yearly_combined_sn = yearly_transforms.concat_yearly_state_market(yearly_state_sn, yearly_market_sn).round(3).reset_index()

    yearly_state_cable = yearly_transforms.pivot_yearly_state(df_yearly_cable)
    yearly_market_cable = yearly_transforms.pivot_yearly_market(df_yearly_cable)
    yearly_combined_cable = yearly_transforms.concat_yearly_state_market(yearly_state_cable, yearly_market_cable).round(3).reset_index()

    yearly_state_big4 = yearly_transforms.pivot_yearly_state(df_yearly_big4)
    yearly_market_big4 = yearly_transforms.pivot_yearly_market(df_yearly_big4)
    yearly_combined_big4 = yearly_transforms.concat_yearly_state_market(yearly_state_big4, yearly_market_big4).round(3).reset_index()
    
    yearly_network_totals = yearly_transforms.concat_network_totals(yearly_combined_sn, yearly_combined_big4,yearly_combined_cable).round(3).reset_index(drop=True)




    # Add the quarter column,, make a copy for good practice
    engagement_df['quarter'] = engagement_df.apply(eng_utils.map_quarter, axis=1)
    df_quarter = engagement_df.copy()

    
    start_time = time.time()
    # Filter out each network group
    df_quarter_sn = df_quarter[df_quarter['stn_grp'] == 'SN']
    df_quarter_cable = df_quarter[df_quarter['stn_grp'] == 'Cable News']
    df_quarter_big4 = df_quarter[df_quarter['stn_grp'] == 'Big 4']

    print(df_quarter_sn.head())
    # Pivot the data TODO: refactor this to be asyncronous/parallelized
    # We pivot by both state and market level and then we conatenate the two
    quarter_state_sn = quarter_transforms.pivot_quarter_state(df_quarter_sn)
    quarter_market_sn = quarter_transforms.pivot_quarter_market(df_quarter_sn)
    quarter_combined_sn = quarter_transforms.concat_quarter_state_market(quarter_state_sn, quarter_market_sn).round(3).reset_index()

    quarter_state_cable = quarter_transforms.pivot_quarter_state(df_quarter_cable)
    quarter_market_cable = quarter_transforms.pivot_quarter_market(df_quarter_cable)
    quarter_combined_cable = quarter_transforms.concat_quarter_state_market(quarter_state_cable, quarter_market_cable).round(3).reset_index()

    quarter_state_big4 = quarter_transforms.pivot_quarter_state(df_quarter_big4)
    quarter_market_big4 = quarter_transforms.pivot_quarter_market(df_quarter_big4)
    quarter_combined_big4 = quarter_transforms.concat_quarter_state_market(quarter_state_big4, quarter_market_big4).round(3).reset_index()

    # Combine the totals for each network
    quarter_network_totals = quarter_transforms.concat_network_totals(quarter_combined_sn, quarter_combined_big4,quarter_combined_cable).round(3).reset_index(drop=True)

    # Grab the columns for the metadata? Unsure if this is really neccesary but is good practice to return metade
    bymarket_table_columns_quarterly = quarter_combined_sn.columns.to_list()
    network_totals_columns_quarterly = quarter_network_totals.columns.to_list()
    bymarket_table_columns_yearly = yearly_combined_sn.columns.to_list()
    network_totals_columns_yearly = yearly_network_totals.columns.to_list()


    # Convert to JSON, note this to_dict function returns a list of dictionaries, where each dictionary is a row in the dataframe
    try:
        # Yearly Dataframes
        yearly_sn_json = yearly_combined_sn.to_dict(orient="records")
        yearly_cable_json = yearly_combined_cable.to_dict(orient="records")
        yearly_big4_json = yearly_combined_big4.to_dict(orient="records")
        yearly_network_totals_json = yearly_network_totals.to_dict(orient="records")

        # Quarterly Dataframes
        quarter_sn_json = quarter_combined_sn.to_dict(orient="records")
        quarter_cable_json = quarter_combined_cable.to_dict(orient="records")
        quarter_big4_json = quarter_combined_big4.to_dict(orient="records")
        quarter_network_totals_json = quarter_network_totals.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    end_time = time.time()
    print(f"The non crud prortion of engagement_quarterly endpoint took {end_time - start_time:.4f} seconds to execute.")
    return EngagementAPIResponse(success=True, message="Data retrieved successfully", data={
        "yearly_sn": yearly_sn_json,
        "yearly_cable": yearly_cable_json,
        "yearly_big4": yearly_big4_json,
        "yearly_network_totals": yearly_network_totals_json,
        "quarter_sn": quarter_sn_json,
        "quarter_cable": quarter_cable_json,
        "quarter_big4": quarter_big4_json,
        "quarter_network_totals": quarter_network_totals_json
    }, metadata={
        "by_market_table_columns_quarterly": bymarket_table_columns_quarterly, 
        "network_totals_columns_quarterly": network_totals_columns_quarterly,
        "by_market_table_columns_yearly": bymarket_table_columns_yearly, 
        "network_totals_columns_yearly": network_totals_columns_yearly
    })


@router.post("/periodicity_history", response_model=EngagementAPIResponse)
def get_periodicity_history(date_range: StartEndEngagement, db: Session = Depends(get_db)):
    """
    Get the periodicity histogram data for a given time range.
    """
    # Convert the start and end months to the format YYYY-MM
    start_month_int = int(datetime.strptime(date_range.start_month, "%B %Y").strftime("%Y%m"))
    end_month_int = int(datetime.strptime(date_range.end_month, "%B %Y").strftime("%Y%m"))

    # Query the database for the periodicity data
    periodicity_df:pd.DataFrame = eng_crud.get_periodicity_history(db=db, start_month=start_month_int, end_month=end_month_int )

    periodicity_df['fiscalmonth'] = periodicity_df['fiscalmonth'].astype(float)
    # Apply transformations
    periodicity_df_sn = periodicity_df[periodicity_df['network'] == 'SPECNEWS']
    periodicity_df_sn = periodicity_transforms.pivot_concat_periodicity_history(periodicity_df_sn).reset_index().round(3)
    print(periodicity_df_sn.head())
    periodicity_df_big4 = periodicity_df[periodicity_df['network'].isin(['ABC', 'FOX', 'NBC', 'CBS'])]
    periodicity_df_big4 = periodicity_transforms.pivot_concat_periodicity_history(periodicity_df_big4).reset_index().round(3)

    periodicity_df_cable = periodicity_df[periodicity_df['network'].isin(['CNN', 'MSNBC','FOX NEWS'])]
    periodicity_df_cable = periodicity_transforms.pivot_concat_periodicity_history(periodicity_df_cable).reset_index().round(3)
    # Cast all column names to strings for periodicity dataframes

    # Convert to JSON
    try:
        periodicity_json_sn = periodicity_df_sn.to_dict(orient="records")
        periodicity_json_big4 = periodicity_df_big4.to_dict(orient="records")
        periodicity_json_cable = periodicity_df_cable.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return EngagementAPIResponse(success=True, message="Data retrieved successfully", data={"periodicity_history_sn": periodicity_json_sn, "periodicity_history_big4": periodicity_json_big4, "periodicity_history_cable": periodicity_json_cable}, metadata={'periodicity_columns': periodicity_df_sn.columns.to_list()})