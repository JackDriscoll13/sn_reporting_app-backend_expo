import pandas as pd
import re


# Config Table:
# Version 5 
def create_table(DMA, avgdf, dailydf, KAZD = False):  
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

    # Set this color mask function - I'm still fairly uncertain on the specificiities of how it works
    # Basically it uses the boolean mask to apply the background color

    def color_mask(val):
        if val == True:
            clr = "#AFE1AF"
        elif val == False:
            clr = "#F69697"
        else:
            clr = 'white'
        return f'background-color: {clr}'

    # Initialize styler, hide index
    dailystyle = dailytbl.style
    dailystyle.hide(axis='index')


    #dailystyle = dailystyle.set_table_attributes('style="border-collapse: collapse; border: 0; width: 70%;"')
    # Apply Mask, hide set dark line above 2nd child
    dailystyle = dailystyle.apply(
        lambda x: mask.map(color_mask), axis=None)
    dailystyle = dailystyle.set_table_styles(

       [{"selector": "td, th", "props": [("border-left", "none"), ("border-right","none"), ("border-top","none"), ("border-bottom","none")]},
        {'selector': 'tr:nth-child(2)', 'props': 'border-top: 1px solid black;'},
        {'selector': 'tr:nth-child(9)', 'props': 'border-bottom: 1px solid black;'},
        {'selector':'th', 'props': [('text-align', 'center'),('background-color', '#0A2F6E'),('color', 'white'), ('font-size', '10pt')]},
        {'selector':'th:first-child', 'props': 'text-align: left'},
        {'selector': 'tr:nth-child(1)','props':"font-weight: bold"},
        dict(selector='th', props=[('text-align', 'center')])])

    # Specify columns to be formatted with decimals
    if KAZD == False: 
        newcols = ['Spec News', 'ABC', 'CBS', 'CW',
                'FOX', 'NBC', 'CNN', 'Fox News', 'MSNBC']
        fontsize = '10pt'
        leftcolwidth = '150px'
        othercolwidth = '100px'

    elif KAZD == True:
        newcols = ['SN 1 + SN KAZD', 'SN 1 Dallas', 'SN KAZD', 'ABC', 'CBS', 'CW','FOX', 'NBC', 'CNN', 'Fox News', 'MSNBC']
        fontsize = '10pt'
        leftcolwidth = '180px'
        othercolwidth = '90px'

    # Set formats for decimal places, set width of columns
    dailystyle = dailystyle.format(
        formatter="{:.2f}", na_rep='MISS', subset=newcols)

    # I'm not sure this line is doing anything. Pretty convinced its doing jack shit
    dailystyle = dailystyle.set_properties(subset = newcols , **{'width': othercolwidth,'text-align': 'center'})
    dailystyle = dailystyle.set_properties(subset = 'Daypart' , **{'width': leftcolwidth,'text-align': 'left'})
    dailystyle = dailystyle.set_properties(**{'font-size': fontsize})

    return dailystyle