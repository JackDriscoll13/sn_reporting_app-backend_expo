# Note: Since rank overtime is such a diverse feature, I have moved all of the
# relevant transformations to this file.

from dateutil.relativedelta import relativedelta
from datetime import datetime
import pandas as pd



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


# Main function to calcualte the rank overtime
def calculate_rank_overtime(engagement_df: pd.DataFrame, start_month_date: datetime, curr_month_date: datetime):

    # Grab the 4 months in the prev 7 months (the 4 not already defined)
    seven_months_ago = start_month_date 
    six_months_ago = start_month_date + relativedelta(months=1)
    five_months_ago = start_month_date + relativedelta(months=2)
    four_months_ago = start_month_date + relativedelta(months=3)
    three_months_ago = start_month_date + relativedelta(months=4)
    one_months_ago = start_month_date + relativedelta(months=5)
   
    # Filter pivot, rank and sort the data:

    seven_months_df = filter_pivot_rank_col(engagement_df, seven_months_ago)
    seven_months_df[f'{seven_months_ago.strftime("%Y-%m")}_rankchange'] = None
    
    # Six months
    six_months_df = filter_pivot_rank_col(engagement_df, six_months_ago)
    six_months_df = add_rankcahnge_column(six_months_df, seven_months_df, six_months_ago, seven_months_ago)
    # Five months 
    five_months_df = filter_pivot_rank_col(engagement_df, five_months_ago)
    five_months_df = add_rankcahnge_column(five_months_df, six_months_df, five_months_ago, six_months_ago)
    # Four months
    four_months_df = filter_pivot_rank_col(engagement_df, four_months_ago)
    four_months_df = add_rankcahnge_column(four_months_df, five_months_df, four_months_ago, five_months_ago)
    # Three months 
    three_months_df = filter_pivot_rank_col(engagement_df, three_months_ago)
    three_months_df = add_rankcahnge_column(three_months_df, four_months_df, three_months_ago, four_months_ago)
    # Previous month 
    one_months_df = filter_pivot_rank_col(engagement_df, one_months_ago)
    one_months_df = add_rankcahnge_column(one_months_df, three_months_df, one_months_ago, three_months_ago)
    # Current month 
    curr_month_df = filter_pivot_rank_col(engagement_df, curr_month_date)
    curr_month_df = add_rankcahnge_column(curr_month_df, one_months_df, curr_month_date, one_months_ago)

    # Now we set the index to rank and concat
    seven_months_df = reindex_rank_df(seven_months_df, seven_months_ago)
    six_months_df = reindex_rank_df(six_months_df, six_months_ago)
    five_months_df = reindex_rank_df(five_months_df, five_months_ago)
    four_months_df = reindex_rank_df(four_months_df, four_months_ago)
    three_months_df = reindex_rank_df(three_months_df, three_months_ago)
    one_months_df = reindex_rank_df(one_months_df, one_months_ago)
    curr_month_df = reindex_rank_df(curr_month_df, curr_month_date)

    result_df = pd.concat([seven_months_df, six_months_df, five_months_df, four_months_df, three_months_df, one_months_df, curr_month_df], axis=1).round(3).reset_index()
    return result_df