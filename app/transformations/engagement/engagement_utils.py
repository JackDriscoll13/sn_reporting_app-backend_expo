# Utility functions for the engagement module and processes.

import pandas as pd
import datetime
import warnings
#### YTD Utils ####

def get_YTD_divisors(state_launch_dates_dict:dict, foy_date:datetime.date, curr_month_date:datetime.date) -> dict: 
    """ A utility function for calculating the divisor for each state in the YTD table.
    Returns a dictionary with the state as the key and the divisor as the value. 
    The divisor is usually the number of months in the year, except in the case where the state launched after the first of the year.
    For example, the divisor for march would be 3, but if the state launched in february, the divisor would be 2. We have to account for this in the YTD calculations.
    These values will be applied to the YTD table to calculate the YTD metrics."""
    divisors = {}
    for state in state_launch_dates_dict: 
        if (state_launch_dates_dict[state] != None) and state_launch_dates_dict[state] > foy_date: 
            months_active = state_launch_dates_dict[state].month
        else: 
            months_active = curr_month_date.month
        divisors[state] = months_active
    return divisors


# Apply the divisors to the YTD table
def divide_by_divisor(row, divisors: dict, row_name:str = 'region'):
    """A utility function for applying the divisors to the YTD table.
    Takes the row and the divisors dictionary as parameters and returns the row with the values divided by the divisor.
    Ignores the region and market columns and applies the divisior to the rest of the columns (numeric columns only.)"""
    state = row[row_name].iloc[0]
    divisor = divisors[state]
    # print(f'State: {state}\nDivisor: {divisor}')
    for col in row.index:
        # print(col)
        if col != (row_name,'') and col != ('region','') and col != ('state',''):
            row[col] /= divisor
            # Apply rounding
            row[col] = round(row[col], 2) / 1000
    return row

# Add a aorting column for the YTD table
# I'm overthinking it. We will almost always be sorting by state on a multi-index with state as the first level and market as the second level.
# I give myself the option of passing region but I doubt I will use it ever.
def add_sorting_column(df:pd.DataFrame, sort_index_row:str = 'state', index_level:str ='clean_prg_name_all'): 
    """Add a sorting column to a dataframe."""

    # Suppress all PerformanceWarnings in this function
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
        state_sorting_dict = {region: i+1 for i, region in enumerate(sorted(df[sort_index_row].unique()))}

        # Create a new column that maps each region to its corresponding integer
        df['grouper_int'] = df[sort_index_row].map(state_sorting_dict)

        # For the market level 
        if index_level != 'state' and index_level != 'region':
            # Step 3: Create a new column that assigns a decimal to each row within each group
            df['grouper_decimal'] = df.groupby(sort_index_row).cumcount() + 1
            df['grouper_decimal'] = df['grouper_decimal'] / 10

            # Step 4: Add the integer and decimal columns together to get your sorting column
            df['sorting_column'] = df['grouper_int'] + df['grouper_decimal']

            # Step 5: Drop the unnecessary columns
            df.loc[df[sort_index_row] == 'Total', 'sorting_column'] = 1000
        # Suppress the specific warning

            df.drop(columns=[sort_index_row,'grouper_int', 'grouper_decimal'], inplace=True)
        else:
            # If no market level, just use the integer
            df['sorting_column'] = df['grouper_int']
            df.drop(columns=['grouper_int'], inplace=True)
            df.loc[df[sort_index_row] == 'Total', 'sorting_column'] = 1000
        
    return df

def map_quarter(row:pd.Series):
    """
    Utility function to map a given row to a quarter based of the month and year 

    Parameters:
    row (pd.Series): The row to map to a quarter. This should contain a 'month' and 'year' column.

    Returns:
    str: The quarter that the row belongs to.
    """
    month = row['month']
    year = row['year']
    quarter = ""
    if month >= 1 and month <= 3:
        quarter = f"Q1 {year}"
    elif month >= 4 and month <= 6:
        quarter = f"Q2 {year}"
    elif month >= 7 and month <= 9:
        quarter = f"Q3 {year}"
    else:
        quarter = f"Q4 {year}"
    return quarter

