import pandas as pd
from .engagement_utils import add_sorting_column

# Assuming that the data has already been filtered, the following pivot functions will be used to create the pivot tables

def pivot_MoM_market(df:pd.DataFrame):
    """
    Create a pivot table for market level engagement MoM.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """
    
    # Clean and Pivot
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_market_subs = pd.pivot_table(df, values=['subs',], index=['state', 'clean_prg_name_all'], columns = ['stn_grp'], aggfunc="sum", margins=False)
    pt_market_adjeng = pd.pivot_table(df, values=['adjeng'], index=['state', 'clean_prg_name_all'], columns = ['stn_grp'], aggfunc="sum", margins=False)

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

def pivot_MoM_state(df:pd.DataFrame):
    """
    Create a pivot table for state level engagement MoM.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """

    # Create the state pivot table
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_state_subs = pd.pivot_table(df, values=['subs',], index=['state'], columns = ['stn_grp'], aggfunc="sum", margins=False)
    pt_state_adjeng = pd.pivot_table(df, values=['adjeng'], index=['state'], columns = ['stn_grp'], aggfunc="sum", margins=False)

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

def concat_MoM_state_market(state_df:pd.DataFrame, market_df:pd.DataFrame):
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
    return final_df

def join_rename_MoM_columns(mom_combined_current:pd.DataFrame, mom_combined_prev:pd.DataFrame, mom_combined_prev_12:pd.DataFrame,
                            current_month_str:str, prev_month_str:str, year_ago_str:str):
    """
    """
    # Assign specific column names in preperation for the join
    mom_combined_current.columns = [f"{col}_curr" for col in mom_combined_current.columns]
    mom_combined_current = mom_combined_current.drop(columns='sorting_column_curr')
    mom_combined_prev.columns = [f"{col}_prev" for col in mom_combined_prev.columns]
    mom_combined_prev = mom_combined_prev.drop(columns='sorting_column_prev')
    mom_combined_prev_12.columns = [f"{col}_prev_12" for col in mom_combined_prev_12.columns]
    mom_combined_prev_12 = mom_combined_prev_12.rename(columns={'sorting_column_prev_12': 'sorting_column'})


    # Join the data frames, sort by the sorting column
    mom_combined_final = mom_combined_current.join(mom_combined_prev, how='outer').join(mom_combined_prev_12, how='outer')
    mom_combined_final = mom_combined_final.sort_values(by='sorting_column')

    # Re-order the columns, replace them with the correct month
    col_order = ['SN_curr', 'SN_prev', 'SN_prev_12', 'Cable News_curr', 'Cable News_prev', 'Cable News_prev_12', 'Big 4_curr', 'Big 4_prev', 'Big 4_prev_12', 'sorting_column']
    mom_combined_final = mom_combined_final[col_order]
    # Function to replace multiple patterns
    def replace_patterns(col_name, replacements):
        for old, new in replacements.items():
            col_name = col_name.replace(old, new)
        return col_name

    replacements = {
        "prev_12": f'{year_ago_str} - {prev_month_str}',
        "curr": current_month_str,
        "prev": prev_month_str, 
    }

    col_order_final = [replace_patterns(col, replacements) for col in col_order]
    mom_combined_final.columns = col_order_final
    return mom_combined_final
