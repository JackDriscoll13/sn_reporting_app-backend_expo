import pandas as pd
import datetime
from .engagement_utils import get_YTD_divisors, divide_by_divisor, add_sorting_column


def pivot_ytd_engagement(df:pd.DataFrame, index_row:str, current_month_date:datetime.date, first_of_year_date:datetime.date) -> pd.DataFrame:
    """
    Calculate the full Year-To-Date (YTD) engagement table. Creates a raw pivot table for YTD engagement data.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data.
    index_row (str): The name of the column to be used as the index in the output DataFrame. Should be either 'state', 'region', or 'clean_prg_name_all'.
    current_month_date (datetime.date): The date representing the current month.
    first_of_year_date (datetime.date): The date representing the first day of the year.

    Returns:
    pd.DataFrame: A DataFrame sorted by the index_row with the YTD engagement metrics. The DataFrame is pivoted by state and market.

    Used to: 
    - Create pivot tables for YTD engagement data. For both the state level and market level (used in by market tab)
    - Create pivot table for the regional level data (used in the by region tab)

    """

    # Step 1: Clean and pivot the data TODO: add HEV to the pivot
    df.loc[:, 'subs'] = df['subs'].replace('', 0)                                                                      
    if index_row != 'state' and index_row != 'region':                                                                   
        pt = pd.pivot_table(df, values=['subs', 'adjeng', 'hev'], index=['state', index_row], columns = ['tiername'], aggfunc="sum", margins=False).reset_index()
    else: 
        pt = pd.pivot_table(df, values=['subs', 'adjeng', 'hev'], index=[index_row], columns = ['tiername'], aggfunc="sum", margins=False).reset_index() 

    # Step 2: Create and apply the divisors
    # Create the divisor dictionary from the launch dates
    state_launch_dates =  df.groupby(index_row)['launch_date'].first()
    state_launch_dates_dict = state_launch_dates.to_dict()
    divisors = get_YTD_divisors(state_launch_dates_dict, first_of_year_date, current_month_date)
    # Apply the divisors to the YTD table
    pt_ytd = pt.apply(lambda row: divide_by_divisor(row, divisors=divisors, row_name=index_row), axis=1)

    # Step 3: Add the sorting column
    if index_row == 'region':
        sort_index_row = 'region'
    else:
        sort_index_row = 'state'
    pt_ytd = add_sorting_column(pt_ytd, sort_index_row=sort_index_row, index_level=index_row)

    # Step 4: Do some cross column calculations to get total viewers here and percent engaged (can probs refactor 5 and 6 into reusable functions)
    pt_ytd['service_subs'] = pt_ytd[('subs', 'Bulk')] + pt_ytd[('subs', 'FALSE')] + pt_ytd[('subs', 'Non-Bulk')]
    pt_ytd['engaged_viewers'] = pt_ytd[('adjeng', 'Bulk')] + pt_ytd[('adjeng', 'FALSE')] + pt_ytd[('adjeng', 'Non-Bulk')]
    pt_ytd['highly_engaged_viewers'] = pt_ytd[('hev', 'Bulk')] + pt_ytd[('hev', 'FALSE')] + pt_ytd[('hev', 'Non-Bulk')]
    # We calculate percent engaged without the FALSE tier
    pt_ytd['percent_engaged'] = (pt_ytd[('adjeng', 'Bulk')] + pt_ytd[('adjeng', 'Non-Bulk')]) / (pt_ytd[('subs', 'Bulk')] + pt_ytd[('subs', 'Non-Bulk')]) 
    pt_ytd['percent_highly_engaged'] = (pt_ytd[('hev', 'Bulk')] + pt_ytd[('hev', 'Non-Bulk')]) / (pt_ytd[('subs', 'Bulk')] + pt_ytd[('subs', 'Non-Bulk')])

    # Step 5: Calculate Totals
    # Calculate totals, set the default totals value to the sum of each column
    totals = pd.Series(pt_ytd.sum(), index=pt_ytd.columns)

    # Manually overwrite columns that need to be custom calculated(percentages), add name
    totals['percent_engaged'] = (totals[('adjeng', 'Bulk')] + totals[('adjeng', 'Non-Bulk')]) / (totals[('subs', 'Bulk')] + totals[('subs', 'Non-Bulk')]) 
    totals['percent_highly_engaged'] = pt_ytd['percent_highly_engaged'].mean() #TODO add HEV here
    totals[index_row] = 'SN Total'

    pt_ytd.loc['Totals'] = totals #NOTE: Totals  have a sorting column that is the sum of the sorting columns. So they will always be at the bottom. -+

    # We can format the data here, but we will do that in the front end
    pt_ytd['percent_engaged'] = pt_ytd['percent_engaged'].apply(lambda x: x *100)
    pt_ytd['percent_highly_engaged'] = pt_ytd['percent_highly_engaged'].apply(lambda x: x *100)
    
    # Step 7: Segment the dataframe, return the Dataframe 
    print(pt_ytd.columns)
    final_df = pt_ytd[[(index_row,''),
            ('service_subs',''),
            ('engaged_viewers',''),
            ('percent_engaged',''),
            ('highly_engaged_viewers',''),
            ('percent_highly_engaged',''),
            ('sorting_column','')]]
    final_df.columns = final_df.columns.droplevel(1)
    final_df.set_index(index_row)

    return final_df


def concatenate_ytd_state_market(ytd_state:pd.DataFrame, ytd_market:pd.DataFrame) -> pd.DataFrame:
    """
    Concatenate the state and market YTD tables to create the full YTD table.

    Parameters:
    ytd_state (pd.DataFrame): The YTD engagement pivot table for the state level.
    ytd_market (pd.DataFrame): The YTD engagement pivot table for the market level.

    Returns:
    pd.DataFrame: The concatenated DataFrame with the YTD engagement metrics for the regional level.
    """

    # Our first step is to make the column names the same for the index(Region/Market) column
    ytd_state.rename(columns={'state':'Market / Region'}, inplace=True)
    ytd_market.rename(columns={'clean_prg_name_all':'Market / Region'}, inplace=True)
    
    # Next we ensure that the totals are the same for both dataframes, this is a data accuracy method
    # Then we drop the totals from one of the dataframes
    if ytd_market.loc['Totals'][['service_subs', 'engaged_viewers', 'percent_engaged']].astype(float).round(2).equals(ytd_state.loc['Totals'][['service_subs', 'engaged_viewers', 'percent_engaged']].astype(float).round(2)):
        print("Totals are the same")
    else: 
        print("Totals are NOT the same")
    ytd_market = ytd_market.drop('Totals')

    # Now we concat and sort
    ytd_combined = pd.concat([ytd_state, ytd_market])
    ytd_combined = ytd_combined.sort_values(by='sorting_column')

    return ytd_combined


