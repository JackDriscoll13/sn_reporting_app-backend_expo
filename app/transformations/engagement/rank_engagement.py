import pandas as pd
from datetime import datetime
from .engagement_utils import add_sorting_column


def pivot_rank_market(df:pd.DataFrame):
    """
    Create a pivot table for market level engagement MoM.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """
    
    # Clean and Pivot
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_market_subs = pd.pivot_table(df, values=['subs',], index=['state', 'clean_prg_name_all'], columns = ['network'], aggfunc="sum", margins=False)
    pt_market_adjeng = pd.pivot_table(df, values=['adjeng'], index=['state', 'clean_prg_name_all'], columns = ['network'], aggfunc="sum", margins=False)

    # Get totals 
    subs_totals = pd.DataFrame(pt_market_subs.sum()).T.set_index(pd.MultiIndex.from_tuples([('Total', 'Total')], names=['state', 'clean_prg_name_all']))
    pt_market_subs = pd.concat([pt_market_subs, subs_totals])
    adjeng_totals = pd.DataFrame(pt_market_adjeng.sum()).T.set_index(pd.MultiIndex.from_tuples([('Total', 'Total')], names=['state', 'clean_prg_name_all']))
    pt_market_adjeng = pd.concat([pt_market_adjeng, adjeng_totals])

    # Divide eaby each other
    # Drop the top level of the column index
    pt_market_subs.columns = pt_market_subs.columns.droplevel(0)
    pt_market_adjeng.columns = pt_market_adjeng.columns.droplevel(0)
    # Divide the two pivot tables to get the engagement penetration 
    pt_market = pt_market_adjeng / pt_market_subs * 100
    pt_market.reset_index(inplace=True)
    pt_market = add_sorting_column(pt_market, 'state', 'clean_prg_name_all')
    return pt_market

def pivot_rank_state(df:pd.DataFrame):
    """
    Create a pivot table for state level engagement MoM.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """

    # Create the state pivot table
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_state_subs = pd.pivot_table(df, values=['subs',], index=['state'], columns = ['network'], aggfunc="sum", margins=False)
    pt_state_adjeng = pd.pivot_table(df, values=['adjeng'], index=['state'], columns = ['network'], aggfunc="sum", margins=False)

    #Calculate the total for each column (of each pivot table)
    subs_totals = pd.DataFrame(pt_state_subs.sum(), columns=['Total']).T
    pt_state_subs = pd.concat([pt_state_subs, subs_totals])

    adjeng_totals = pd.DataFrame(pt_state_adjeng.sum(), columns=['Total']).T
    pt_state_adjeng = pd.concat([pt_state_adjeng, adjeng_totals])

    # Drop the top level of the column index
    pt_state_subs.columns = pt_state_subs.columns.droplevel(0)
    pt_state_adjeng.columns = pt_state_adjeng.columns.droplevel(0)
    # Divide the two pivot tables to get the engagement over time by market
    pt_state = pt_state_adjeng / pt_state_subs * 100
    pt_state = pt_state.reset_index()
    # Add the sorting column
    pt_state = pt_state.rename(columns={'index': 'state'})
    pt_state = add_sorting_column(pt_state, 'state', 'state')
    return pt_state


def concat_rank_state_market(state_df:pd.DataFrame, market_df:pd.DataFrame):
    """
    Concatenate the state and market pivot tables to create a single pivot table for the MoM engagement data.

    Parameters:
    state_df (pd.DataFrame): The state level pivot table.
    market_df (pd.DataFrame): The market level pivot table.
    """    
    state_df.columns.name = None
    market_df.columns.name = None

    # Concatenate the two pivot tables(for sorting purposes)
    state_totals_clean = state_df.loc[state_df['state'] == 'Total'].iloc[:, 1:].reset_index(drop=True).drop(columns='sorting_column').round(2)
    market_totals_clean = market_df.loc[market_df['clean_prg_name_all'] == 'Total'].iloc[:, 1:].reset_index(drop=True).drop(columns='sorting_column').round(2)

    if state_totals_clean.equals(market_totals_clean):
        print('Totals are the same.')
    else:
        print('Totals are not the same.')


    # Clean up before concat, having to reset index again here
    state_df = state_df.rename(columns={'state':'Market / Region'})
    state_df = state_df.set_index('Market / Region')
    market_df.rename(columns={'clean_prg_name_all':'Market / Region'}, inplace=True)
    market_df = market_df.set_index('Market / Region').drop('Total')


    final_df = pd.concat([state_df, market_df])
    final_df = final_df.sort_values(by='sorting_column')

    # Adding the rank to the end of the function
    ranks = final_df[['ABC', 'CBS', 'CNN', 'FOX', 'FOX NEWS CHANNEL', 'MSNBC', 'NBC', 'SPECNEWS']].rank(axis=1, ascending=False,)
    final_df['SN_Rank'] = ranks['SPECNEWS']
    return final_df


#### FOR THE SECOND RANK TAB, RANK OVERTIME
def filter_pivot_rank_col(df:pd.DataFrame, date_filter: datetime): 
    ## Filter, pivot, calculate(divide) rank and sort
    # All the date formates we will need here
    month_filter = date_filter.month
    year_filter = date_filter.year
    date_str = date_filter.strftime("%Y-%m")
    # Filter one month and year pair
    six_months_col = df.loc[(df['year'] == year_filter) & (df['month'] == month_filter)]
    # Pivot the data so we have networks as the index
    col_subs = pd.pivot_table(six_months_col, values=['subs'], index=['network'], columns = ['month'], aggfunc="sum", margins=False)
    col_adjeng = pd.pivot_table(six_months_col, values=['adjeng'], index=['network'], columns = ['month'], aggfunc="sum", margins=False)

    # Divide by each other
    # Drop the top level of the column index
    col_subs.columns = col_subs.columns.droplevel(0)
    col_adjeng.columns = col_adjeng.columns.droplevel(0)
    # Divide to get engagement penetration
    col_eng_penn = col_adjeng / col_subs * 100
    # Rank
    col_eng_penn['Rank'] = col_eng_penn.rank(axis=0, ascending=False)
    # Sort and set index
    col_eng_penn = col_eng_penn.rename(index={'FOX NEWS CHANNEL': 'FNC'})
    col_eng_penn = col_eng_penn.sort_values(by='Rank')
    # col_eng_penn = col_eng_penn.reset_index().set_index('Rank', append=False,)
    # Rename, add the date string before the column 
    col_eng_penn = col_eng_penn.rename(columns={month_filter: 'adjeng'})
    new_columns = ([f'{date_str}_{col}' for col in col_eng_penn.columns])
    col_eng_penn.columns = new_columns
    # As a final setp we replace all FOX NEWS CHANNEL with  FNC
    
    return col_eng_penn


def add_rankcahnge_column(curr_df: pd.DataFrame, prev_df: pd.DataFrame, curr_date: datetime, prev_date: datetime):
    """ Add Rank change column to the current each sub df"""
    prev_date_str = prev_date.strftime("%Y-%m")
    curr_date_str = curr_date.strftime("%Y-%m")

    # Add rank change column 
    rank_change = prev_df[f'{prev_date_str}_Rank'] - curr_df[f'{curr_date_str}_Rank'] 
    curr_df[f'{curr_date_str}_rankchange'] = rank_change

    # Set the index and rename the columns
    # curr_df = curr_df.reset_index().set_index(f'{curr_date_str}_Rank', append=False).rename_axis('Rank')
    # curr_df = curr_df.rename(columns={'network': f'{curr_date_str}_network'})

    return curr_df

def reindex_rank_df(df: pd.DataFrame, date: datetime):
    """ Reindex the rank df to have the date string in the columns and the rank as the index."""
    date_str = date.strftime("%Y-%m")
    # Reset the index, set rank as index with new name. add the date to the netowrk column
    df = df.reset_index().set_index(f'{date_str}_Rank', append=False).rename_axis('Rank')
    df = df.rename(columns={'network': f'{date_str}_network'})
    
    return df