import pandas as pd
from .engagement_utils import add_sorting_column

def pivot_HEV_market(df:pd.DataFrame):
    """
    Create a pivot table for market level engagement MoM.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """
    
    # Clean and Pivot
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_market_subs = pd.pivot_table(df, values=['subs',], index=['state', 'clean_prg_name_all'], columns = ['stn_grp'], aggfunc="sum", margins=False)
    pt_market_HEV = pd.pivot_table(df, values=['HEV'], index=['state', 'clean_prg_name_all'], columns = ['stn_grp'], aggfunc="sum", margins=False)

    # Get totals 
    subs_totals = pd.DataFrame(pt_market_subs.sum()).T.set_index(pd.MultiIndex.from_tuples([('Total', 'Total')], names=['state', 'clean_prg_name_all']))
    pt_market_subs = pd.concat([pt_market_subs, subs_totals])
    HEV_totals = pd.DataFrame(pt_market_HEV.sum()).T.set_index(pd.MultiIndex.from_tuples([('Total', 'Total')], names=['state', 'clean_prg_name_all']))
    pt_market_HEV = pd.concat([pt_market_HEV, HEV_totals])

    # Divide eaby each other
    # Drop the top level of the column index
    pt_market_subs.columns = pt_market_subs.columns.droplevel(0)
    pt_market_HEV.columns = pt_market_HEV.columns.droplevel(0)
    # Divide the two pivot tables to get the engagement penetration 
    pt_market = pt_market_HEV / pt_market_subs * 100
    pt_market.reset_index(inplace=True)
    pt_market = add_sorting_column(pt_market, 'state', 'clean_prg_name_all')
    return pt_market

def pivot_HEV_state(df:pd.DataFrame):
    """
    Create a pivot table for state level engagement MoM.

    Parameters:
    df (pd.DataFrame): The input DataFrame with raw engagement data. This has already been filtered to the desired date range. 
    """

    # Create the state pivot table
    df.loc[:, 'subs'] = df['subs'].replace('', 0)  
    pt_state_subs = pd.pivot_table(df, values=['subs',], index=['state'], columns = ['stn_grp'], aggfunc="sum", margins=False)
    pt_state_HEV = pd.pivot_table(df, values=['HEV'], index=['state'], columns = ['stn_grp'], aggfunc="sum", margins=False)

    #Calculate the total for each column (of each pivot table)
    subs_totals = pd.DataFrame(pt_state_subs.sum(), columns=['Total']).T
    pt_state_subs = pd.concat([pt_state_subs, subs_totals])

    HEV_totals = pd.DataFrame(pt_state_HEV.sum(), columns=['Total']).T
    pt_state_HEV = pd.concat([pt_state_HEV, HEV_totals])

    # Drop the top level of the column index
    pt_state_subs.columns = pt_state_subs.columns.droplevel(0)
    pt_state_HEV.columns = pt_state_HEV.columns.droplevel(0)
    # Divide the two pivot tables to get the engagement over time by market
    pt_state = pt_state_HEV / pt_state_subs * 100
    pt_state = pt_state.reset_index()
    # Add the sorting column
    pt_state = pt_state.rename(columns={'index': 'state'})
    pt_state = add_sorting_column(pt_state, 'state', 'state')
    return pt_state


def concat_HEV_state_market(state_df:pd.DataFrame, market_df:pd.DataFrame):
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

def join_re_order_HEV_columns(hev_combined_current:pd.DataFrame, hev_combined_prev:pd.DataFrame, hev_change:pd.DataFrame,
                              curr_period_start:str, curr_period_end:str, prev_period_start:str, prev_period_end:str):
    """
    Join the current, previous, and change pivot tables together and reorder the columns.

    Parameters:
    hev_combined_current (pd.DataFrame): The current pivot table.
    hev_combined_prev (pd.DataFrame): The previous pivot table.
    hev_change (pd.DataFrame): The change pivot table.
    """
    # Assign specific column names in preperation for the join
    hev_combined_current.columns = [f"{col}_curr" for col in hev_combined_current.columns]
    hev_combined_current = hev_combined_current.rename(columns={'sorting_column_curr': 'sorting_column'})
    hev_combined_prev.columns = [f"{col}_prev" for col in hev_combined_prev.columns]
    hev_combined_prev = hev_combined_prev.drop(columns='sorting_column_prev')
    hev_change.columns = [f"{col}_hevchange" for col in hev_change.columns]

    # Join the three dataframes, reorder by sorting column
    hev_combined_final = hev_combined_current.join(hev_combined_prev, how='outer').join(hev_change, how='outer')
    hev_combined_final = hev_combined_final.sort_values(by='sorting_column')

    col_order = ['SN_curr', 'SN_prev', 'SN_hevchange', 'Big 4_curr', 'Big 4_prev', 'Big 4_hevchange', 'Cable News_curr', 'Cable News_prev', 'Cable News_hevchange', 'sorting_column']
    hev_combined_final = hev_combined_final[col_order]

    # Replace the column names with the specified period month
    def replace_patterns(col_name, replacements):
        for old, new in replacements.items():
            col_name = col_name.replace(old, new)
        return col_name

    replacements = {
        "curr": f"{curr_period_start} - {curr_period_end}",
        "prev": f"{prev_period_start} - {prev_period_end}", 
    }

    col_order_final = [replace_patterns(col, replacements) for col in col_order]
    hev_combined_final.columns = col_order_final
    return hev_combined_final

