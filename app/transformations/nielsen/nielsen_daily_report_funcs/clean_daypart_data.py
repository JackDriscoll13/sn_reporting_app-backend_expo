import warnings
import pandas as pd
import numpy as np

from .data_cleaning_utils import  map_order, map_geography, rename_full_day

def clean_daypart_data(path, stationReferenceDict, order_mapping_dict, geography_mapping_dict):
    # Read in file
    try:
        with warnings.catch_warnings(): # Supress openpyxl default style warning
            warnings.simplefilter("ignore")
            daypartsdf = pd.read_excel(path,sheet_name='Live+Same Day, TV Households',header = 8,skipfooter=8).ffill()
    except Exception as e:
        print(e)
        print('There was an issue locating the spectrum dayparts file, this file is critical for the report to generate. ')
        
    # Check for NA values: 
    if ' ' in daypartsdf['RTG % (X.X)'].unique() or daypartsdf['RTG % (X.X)'].isnull().values.any():
        print(f'WARNING!! WARNING!!! Missing RTG found in Dayparts File! \nPath:\n{path}') 
    daypartsdf['RTG % (X.X)'] = daypartsdf['RTG % (X.X)'].fillna(0)
    daypartsdf['RTG % (X.X)'] = daypartsdf['RTG % (X.X)'].replace(' ', 0)

    # Strip white space
    daypartsdf = daypartsdf.map(lambda x: x.strip() if isinstance(x, str) else x)

    # TEMPORRARY UNTIL SOURCE IS FIXED - Remove s1df and s1mk from all markets, re add them back where they're regions are
    dallasdf = daypartsdf[(daypartsdf['Viewing Source'] == 'S1DF ') & (
        daypartsdf['Geography / Metrics'] == 'Dallas-Ft. Worth')]
    milwakdf = daypartsdf[(daypartsdf['Viewing Source'] == 'S1MK ')
                        & (daypartsdf['Geography / Metrics'] == 'Milwaukee')]
    daypartsdf = daypartsdf[(daypartsdf['Viewing Source'] != 'S1DF ')
                        & (daypartsdf['Viewing Source'] != 'S1MK ')]
    daypartsdf = pd.concat([daypartsdf, dallasdf, milwakdf]).reset_index()

    # Drop any instance where there is 
    dropped_dmas = ['Greensboro', 'Raleigh', 'Columbus', 'Milwaukee', 'Austin', 'San Antonio']
    daypartsdf = daypartsdf[~daypartsdf['Geography / Metrics'].isin(dropped_dmas)] 

    # Map to station to network, and geography to dma
    daypartsdf['Station'] = daypartsdf['Viewing Source'].apply(lambda x: stationReferenceDict[x])
    daypartsdf['DMA'] = daypartsdf['Geography / Metrics'].apply(lambda x: map_geography(x, geography_mapping_dict))

    # Clean up time column (rename full day), and drop unneccesary columns
    daypartsdf['Time'] = daypartsdf['Time'].apply(lambda x: rename_full_day(x))
    daypartsdf = daypartsdf.drop(['Affil.','Custom Range','Daypart','Demo','Geography / Metrics', 'Indicator ','Indicator','Metrics'], axis = 1,errors='ignore').rename(columns={'RTG % (X.X)':'RTG'})

    # Reorder columns
    reportdf = pd.DataFrame(data=None, columns=['Spec News','ABC', 'CNN','Fox News','MSNBC','CBS','CW','FOX','KAZD','NBC','DMA'])

    # Pivot table for each dma, each station
    for i in daypartsdf['DMA'].unique():
        dmaonly = daypartsdf[daypartsdf['DMA']== i]
        dmaonly = dmaonly.pivot_table(index='Time',columns='Station',values='RTG', aggfunc = 'sum')
        dmaonly['DMA'] = i
        with warnings.catch_warnings(): # Supress a warning!
            warnings.simplefilter(action='ignore', category=FutureWarning) # Supress a warning
            reportdf = pd.concat([reportdf,dmaonly],join = 'outer')
    reportdf = reportdf.reset_index().rename(columns={'index':'Daypart'})

    # map order
    reportdf['Order'] = reportdf['Daypart'].apply(lambda x: map_order(x, order_mapping_dict))

    return reportdf