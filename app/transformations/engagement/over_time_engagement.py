
import pandas as pd
from .engagement_utils import add_sorting_column

def pivot_overtime_market(df:pd.DataFrame):
    """
    Create a pivot table for market level engagement over time. (Past 24 months)

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range
    and dropped market data (converted to NAN) in corresponding to thier launch dates. See query for more details. 
    """ 
    # Create the market Pivot table
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_market_subs = pd.pivot_table(df, values=['subs',], index=['state', 'clean_prg_name_all'], columns = ['year','month'], aggfunc="sum", margins=False)
    pt_market_adjeng = pd.pivot_table(df, values=['adjeng'], index=['state', 'clean_prg_name_all'], columns = ['year','month'], aggfunc="sum", margins=False)
    # Calculate the total for each column (of each pivot table)
    subs_totals = pd.DataFrame(pt_market_subs.sum()).T.set_index(pd.MultiIndex.from_tuples([('Total', 'Total')], names=['state', 'clean_prg_name_all']))
    pt_market_subs = pd.concat([pt_market_subs, subs_totals])
    adjeng_totals = pd.DataFrame(pt_market_adjeng.sum()).T.set_index(pd.MultiIndex.from_tuples([('Total', 'Total')], names=['state', 'clean_prg_name_all']))
    pt_market_adjeng = pd.concat([pt_market_adjeng, adjeng_totals])
    # Drop the top level of the column index
    pt_market_subs.columns = pt_market_subs.columns.droplevel(0)
    pt_market_adjeng.columns = pt_market_adjeng.columns.droplevel(0)
    # Divide the two pivot tables to get the engagement over time by market
    pt_market = pt_market_adjeng / pt_market_subs * 100
    pt_market = pt_market.reset_index()
    # Add the sorting column
    pt_market = add_sorting_column(pt_market, 'state', 'clean_prg_name_all')
    return pt_market


# While these look similiar, it is easier to keep them seperate as they are used in different contexts and have different requirements.
def pivot_overtime_state(df:pd.DataFrame):
    """
    Create a pivot table for state level engagement over time. (Past 24 months)

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """
    # Create the state pivot table
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_state_subs = pd.pivot_table(df, values=['subs',], index=['state'], columns = ['year','month'], aggfunc="sum", margins=False)
    pt_state_adjeng = pd.pivot_table(df, values=['adjeng'], index=['state'], columns = ['year','month'], aggfunc="sum", margins=False)

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

def concat_overtime_state_market(state_df:pd.DataFrame, market_df:pd.DataFrame):
    """
    Concatenate the state and market pivot tables to create a single pivot table for the YTD engagement data.

    Parameters:
    state_df (pd.DataFrame): The state level pivot table.
    market_df (pd.DataFrame): The market level pivot table.
    """    
    # Check if the totals are the same
    state_totals_clean = state_df.loc[state_df['state'] == 'Total'].iloc[:, 1:].reset_index(drop=True).drop(columns='sorting_column').round(2)
    market_totals_clean = market_df.loc[market_df['clean_prg_name_all'] == 'Total'].iloc[:, 1:].reset_index(drop=True).drop(columns='sorting_column').round(2)

    if state_totals_clean.equals(market_totals_clean):
        print('Totals are the same.')
    else:
        print('Totals are not the same.')

    # Clean up before concat
    state_df.rename(columns={'state':'Market / Region'}, inplace=True)
    state_df = state_df.set_index('Market / Region')
    market_df.rename(columns={'clean_prg_name_all':'Market / Region'}, inplace=True)
    market_df = market_df.set_index('Market / Region').drop('Total')

    # Concat and sort, rename sorting column to a single string ( this avoids confusion is the frontend)
    eng_overtime = pd.concat([state_df, market_df])
    eng_overtime.columns = ['_'.join(map(str, col)).strip() for col in eng_overtime.columns.values]
    eng_overtime = eng_overtime.sort_values(by='sorting_column_')
    print(eng_overtime.columns)
    return eng_overtime

