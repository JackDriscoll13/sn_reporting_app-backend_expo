import pandas as pd 
from .engagement_utils import add_sorting_column

def pivot_concat_periodicity_history(df:pd.DataFrame):
    """
    Create a pivot table for market level periodicity history.

    Parameters:
    df (pd.DataFrame): The input DataFrame with periodicity data.
    """ 
    df['fiscalmonth'] = df['fiscalmonth'].astype(int)
    # Pivot the dataframe for the market level
    market_pivot = pd.pivot_table(df, values=['periodicity'], index=['state','clean_prg_name_all'], columns=['fiscalmonth'], margins=False)
    market_pivot.columns = market_pivot.columns.droplevel(0)
    market_pivot = market_pivot.reset_index()
    # Add sorting column
    market_pivot = add_sorting_column(market_pivot, 'state', 'clean_prg_name_all')

    # Pivot the dataframe for the state level
    state_pivot = pd.pivot_table(df, values=['periodicity'], index=['state'], columns=['fiscalmonth'], aggfunc="mean", margins=False)
    state_pivot.columns = state_pivot.columns.droplevel(0)
    state_pivot = state_pivot.reset_index()
    state_pivot = add_sorting_column(state_pivot, 'state', 'state')
    # Clean up before concat

    state_pivot.rename(columns={'state':'Market / Region'}, inplace=True)
    state_pivot = state_pivot.set_index('Market / Region')
    market_pivot.rename(columns={'clean_prg_name_all':'Market / Region'}, inplace=True)
    market_pivot = market_pivot.set_index('Market / Region')

    # Concat and sort
    final_pivot = pd.concat([market_pivot, state_pivot]).sort_values(by=['sorting_column'])
  

    return final_pivot
