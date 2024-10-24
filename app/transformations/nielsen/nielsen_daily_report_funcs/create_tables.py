import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.table import Table


# Config Table:
# Version 5 
def create_table(DMA, avgdf, dailydf, KAZD = False, tablepath = None):  
    # This function has been updated on 2/15 to Sum KAZD into Spec News
    # Correct column orders
    dailydf = dailydf[['Daypart', 'Spec News', 'KAZD', 'ABC', 'CBS', 'CW',
                       'FOX', 'NBC', 'CNN', 'Fox News', 'MSNBC', 'DMA', 'Order']]
    avgdf = avgdf[['Daypart', 'Spec News', 'KAZD', 'ABC', 'CBS', 'CW', 'FOX',
                   'NBC', 'CNN', 'Fox News', 'MSNBC', 'DMA', 'Order']]


    # Change times, removing preceeding 0s and spaces before am/pm, using rexex to do so!
    dailydf['Daypart'] = dailydf['Daypart'].apply(lambda x: re.sub('0(?=[1-9]:)| (?=[ap])','', x))
    avgdf['Daypart'] = avgdf['Daypart'].apply(lambda x: re.sub('0(?=[1-9]:)| (?=[ap])','', x))
    
    # Round Decimals to two places 
    dailydf = dailydf.round(decimals=2)
    avgdf = avgdf.round(decimals=2)

    # Set average and non average tables
    if KAZD == True: 
        # Avg Table
        avgtbl = avgdf[avgdf['DMA'] == DMA].sort_values('Order').drop(columns=['DMA', 'Order'])
        avgtbl['SN 1 + SN KAZD'] = avgtbl['Spec News'] + avgtbl['KAZD']
        avgtbl = avgtbl.rename(columns = {'Spec News': 'SN 1 Dallas', 'KAZD': 'SN KAZD'})
        avgtbl = avgtbl[['Daypart', 'SN 1 + SN KAZD', 'SN 1 Dallas', 'SN KAZD', 'ABC', 'CBS', 'CW','FOX', 'NBC', 'CNN', 'Fox News', 'MSNBC']]
        # Daily tbl
        dailytbl = dailydf[dailydf['DMA'] == DMA].sort_values('Order').drop(columns=['DMA', 'Order'])
        dailytbl['SN 1 + SN KAZD'] = dailytbl['Spec News'] + dailytbl['KAZD']
        dailytbl = dailytbl.rename(columns = {'Spec News': 'SN 1 Dallas', 'KAZD': 'SN KAZD'})
        dailytbl = dailytbl[['Daypart', 'SN 1 + SN KAZD', 'SN 1 Dallas', 'SN KAZD', 'ABC', 'CBS', 'CW','FOX', 'NBC', 'CNN', 'Fox News', 'MSNBC']]

    elif KAZD == False: 
        avgtbl = avgdf[avgdf['DMA'] == DMA].sort_values(
            'Order').drop(columns=['KAZD', 'DMA', 'Order'])
        dailytbl = dailydf[dailydf['DMA'] == DMA].sort_values(
            'Order').drop(columns=['KAZD', 'DMA', 'Order'])
    
    
    # Set mask
    mask = dailytbl > avgtbl
    # Set mask time/daypart column (index)
    mask['Daypart'] = dailydf['Daypart']

    # Prepare data for display
    data = dailytbl.values
    col_labels = dailytbl.columns.tolist()
    row_labels = dailytbl['Daypart'].tolist()
    cell_text = [row[1:].tolist() for row in data]  # Exclude 'Daypart' column from data
    row_labels = [row[0] for row in data]  # 'Daypart' values

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(12, 0.6 * len(cell_text)))  # Adjust height based on the number of rows
    ax.axis('off')  # Hide axes


    #####
    ##### TABLE STYLING
    #####

    # Create a table
    table = ax.table(cellText=cell_text, colLabels=col_labels[1:], rowLabels=row_labels,
                     loc='center', cellLoc='center')

    # Add "Daypart" label to top-left cell
    table.add_cell(0, -1, width=0.15, height=0.04, text='Daypart')
    daypart_cell = table[0, -1]
    daypart_cell.set_text_props(weight='bold', color='white')
    daypart_cell.set_facecolor('#0A2F6E')
    daypart_cell.set_text_props(ha='left')

    # Adjust the table style
    table.auto_set_font_size(False)
    if KAZD == True:
        table.set_fontsize(6.5)
    else:
        table.set_fontsize(9)
    table.scale(1, 1.5)

    # Apply conditional formatting
    n_rows = len(cell_text)
    n_cols = len(col_labels) - 1  # Exclude 'Daypart'

    # Apply the benchmark mask to the table 
    for i in range(n_rows):
        for j in range(n_cols):
            cell = table[i + 1, j]  # +1 because row 0 is header
            if mask.iloc[i, j + 1]:  # +1 to skip 'Daypart' column in mask
                cell.set_facecolor('#AFE1AF')  # Light green
            else:
                cell.set_facecolor('#F69697')  # Light red

    # Set header style
    for key, cell in table.get_celld().items():
        if key[0] == 0 or key[1] == -1:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#0A2F6E')
        # Adjust alignment for the first column
        if key[1] == -1:
            cell._loc = 'left'


    # Save the table as an image
    plt.savefig(tablepath, bbox_inches='tight', dpi=400)
    plt.close(fig)

    return tablepath
