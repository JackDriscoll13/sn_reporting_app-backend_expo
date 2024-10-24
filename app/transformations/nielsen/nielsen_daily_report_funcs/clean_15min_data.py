# For cleaning the 15min and dayparts data
# This function used to include functionality for concatenating the buffalo file as well, but that has since been removed

import warnings
import pandas as pd
from .data_cleaning_utils import map_geography

def clean_15min_data(file, stationReferenceDict:dict, chartorderdict:dict, geography_mapping:dict) -> pd.DataFrame:
    """
    Cleans and maps the 15minfile. Used in both the benchmark and daily files.
    Returns a dataframe.
    """

    # Attempt to read in file. 
    try:
        with warnings.catch_warnings(): # Supress openpyxl default style warning
            warnings.simplefilter("ignore")
            min15df = pd.read_excel(file,sheet_name='Live+Same Day, TV Households',header = 8,skipfooter=8).ffill()
    except Exception as e:
        print(e)
        print('There was an issue loading the spectrum 15minute file, this file is critical for the report to generate.')
    
        
    # Check for nan values
    if ' ' in min15df['RTG % (X.X)'].unique() or min15df['RTG % (X.X)'].isnull().values.any():
        print(f'WARNING!! WARNING!!! Missing RTG found in 15min File!')  
    min15df['RTG % (X.X)'] = min15df['RTG % (X.X)'].fillna(0)
    min15df['RTG % (X.X)'] = min15df['RTG % (X.X)'].replace(' ', 0)

    # Strip White space
    min15df = min15df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # TEMPORRARY UNTIL SOURCE IS FIXED - Remove s1df and s1mk from all markets, re add them back where they're regions are
    dallasdf = min15df[(min15df['Viewing Source']== 'S1DF') & (min15df['Geography / Metrics']=='Dallas-Ft. Worth')]
    milwakdf = min15df[(min15df['Viewing Source']== 'S1MK') & (min15df['Geography / Metrics']=='Milwaukee')]
    min15df = min15df[(min15df['Viewing Source']!= 'S1DF') & (min15df['Viewing Source']!='S1MK')]
    min15df = pd.concat([min15df,dallasdf,milwakdf]).reset_index()
    
    # Drop the unavailbe markets for effenciency purposes
    dropped_dmas = ['Greensboro', 'Raleigh', 'Columbus', 'Milwaukee', 'Austin', 'San Antonio']
    min15df = min15df[~min15df['Geography / Metrics'].isin(dropped_dmas)] 

    # Add station column
    min15df['Station'] = min15df['Viewing Source'].apply(lambda x: stationReferenceDict[x])

    # Add DMA specific column 
    min15df['DMA'] = min15df['Geography / Metrics'].apply(lambda x: map_geography(x, geography_mapping))

    # New logic here, for the time column, we strip out any whitespace at all from the time column
    min15df['Time'] = min15df['Time'].astype(str).str.replace(r'\s+', '', regex=True)

    # Add order column
    min15df['Order'] = min15df['Time'].apply(lambda x: chartorderdict[x])

    # Drop unneccesary columns, rename RTG column
    min15df = min15df.drop(['Affil.','Custom Range','Daypart','Demo','Geography / Metrics','index','Indicator','Indicator ','Metrics'], axis = 1, errors='ignore').rename(columns={'RTG % (X.X)':'RTG'})

    return min15df