import pandas as pd 
import seaborn as sb
import matplotlib.pyplot as plt 
import calendar


# Functions for creating charts, scroll down to see dallas 

# Version 6
# Function for configuring chart:
def create_chart(dailydata, avgdata, snNamesDict):
    
    source = avgdata['Viewing Source'].unique()[0]
    # Isloate data to specific source (uneeded now)
    dailydataspec = dailydata
    avgdataspec = avgdata

    # Apply the order
    dailydataspec = dailydataspec.sort_values('Order')
    avgdataspec = avgdataspec.sort_values('Order')

    # aAply the moving avg column as a method of data smoothing, this is what we will chart
    dailydataspec['Movingavg'] = dailydataspec['RTG'].rolling(5,center=True,min_periods=2).mean()
    avgdataspec['Movingavg'] = avgdataspec['RTG'].rolling(5,center=True,min_periods=2).mean()

    # Edit the x axis to be only the last 7 characters, the time
    avgdataspec['Timeinterval'] = avgdataspec['Time'].apply(lambda x: x[-7:])
    dailydataspec['Timeinterval'] = dailydataspec['Time'].apply(lambda x: x[-7:])

    # grab the month name and the year
    month_num = int(str(avgdataspec['Dates'].unique()[0])[0:2])
    month_name = calendar.month_name[month_num]

    year_num = str(avgdataspec['Dates'].unique()[0])[6:10]

    # grab the max y value
    allrtgdata = pd.concat([dailydataspec['Movingavg'],(avgdataspec['Movingavg'])])
    ymaxme = allrtgdata.max()
    limity = ymaxme * 1.2

    sb.reset_defaults()
    sb.set(rc={'figure.figsize':(14,4)})
    sb.set_style('white')
    plt.rcParams['xtick.major.pad']='0'

    # Plot 1
    plt1 = sb.lineplot(data = dailydataspec,
        x= 'Timeinterval',
        y= 'Movingavg',
        # Remove markers
        color = '#0A2F6E',
        errorbar= None
    )

    plt2 = sb.lineplot(
        data = avgdataspec,
        x= 'Timeinterval',
        y= 'Movingavg',
        color ='#689DF3',
        alpha=0.5,
        errorbar= None
    )
    l1= plt2.lines[0]
    l2 = plt2.lines[1]
    x2 = l2.get_xydata()[:,0]
    y2 = l2.get_xydata()[:,1]
    plt2.fill_between(x2,y2, color='#689DF3', alpha=0.3)

    # Set Formatting of plots
    plt1.margins(x=0.01, y = 0.01)
    plt1.set_title(str(snNamesDict[source]), weight='bold',fontsize = '14')
    plt1.set_xlabel(None)
    plt1.set_ylabel('Rating',size=12)
    plt1.xaxis.grid(True,which='minor')
    plt1.yaxis.grid(False) # Whether to show vertical gridlines vertical gridlines# Show the vertical gridlines
    plt1.set_ylim(ymin = 0 , ymax = limity )
    plt1.set_xlim(0,)
    plt1.tick_params(axis='x', labelright = True, rotation=90,labelsize=12)
    plt1.tick_params(axis='y',labelsize=12)
    plt1.tick_params(left=True, bottom=True, color = '#787878')


    xticklist = [i+1 for i in range(0,len(x2),2)]
    plt1.set_xticks(xticklist)

    plt1.spines['right'].set_visible(False)
    plt1.spines['top'].set_visible(False)
    plt1.spines['bottom'].set_visible(True)
    plt1.spines['bottom'].set_color('#787878')
    plt1.spines['left'].set_visible(True)
    plt1.spines['left'].set_color('#787878')

    plt.legend([l1, l2], [str(dailydataspec['Dates'].unique()[0]), f'{month_name} {year_num} average',], loc = 'upper center', bbox_to_anchor= (.5, -.22),frameon=False)
    plt.setp(plt1.get_legend().get_texts(), fontsize='12')
    chart = plt1.get_figure()
    plt.close()

    return chart


## Because dallas have had some changing requests, it's easier to stick it in its own function 
def create_chart_dallas(dailydata, avgdata, snNamesDict):

    # Get neccesary data frames
    dailydataspec = dailydata[dailydata['Viewing Source']=='S1DF']
    dailydataspec_kazd = dailydata[dailydata['Viewing Source']=='KAZD 55.1']

    # Average
    avgdataspec = avgdata[avgdata['Viewing Source']=='S1DF'] # we will only we using this -> the s1df prev month average 

    #apply the order
    dailydataspec = dailydataspec.sort_values('Order')
    dailydataspec_kazd = dailydataspec_kazd.sort_values('Order')
    avgdataspec = avgdataspec.sort_values('Order')
    
    # Sum (combine rtg of KAZD and S1DF) the rating
    dailydataspec['kazd_rtg'] = dailydataspec_kazd['RTG'].values
    dailydataspec['combined_total'] = dailydataspec['kazd_rtg'] + dailydataspec['RTG']

    # appply the moving avg column as a method of data smoothing, this is what we will chart
    dailydataspec['Movingavg_s1df'] = dailydataspec['RTG'].rolling(5,center=True,min_periods=2).mean()
    dailydataspec['Movingavg_kazd'] = dailydataspec['kazd_rtg'].rolling(5,center=True,min_periods=2).mean()
    dailydataspec['Movingavg_combined'] = dailydataspec['combined_total'].rolling(5,center=True,min_periods=2).mean()
    avgdataspec['Movingavg'] = avgdataspec['RTG'].rolling(5,center=True,min_periods=2).mean()

    # Edit the x axis to be only the last 7 characters, the time
    dailydataspec['Timeinterval'] = dailydataspec['Time'].apply(lambda x: x[-7:])
    avgdataspec['Timeinterval'] = avgdataspec['Time'].apply(lambda x: x[-7:])
    
    # grab the month name and the year
    month_num = int(str(avgdataspec['Dates'].unique()[0])[0:2])
    month_name = calendar.month_name[month_num]

    year_num = str(avgdataspec['Dates'].unique()[0])[6:10]

    # grab the max y value
    allrtgdata = pd.concat([dailydataspec['Movingavg_combined'],(avgdataspec['Movingavg'])])
    ymaxme = allrtgdata.max()
    limity = ymaxme * 1.2

    sb.reset_defaults()
    sb.set(rc={'figure.figsize':(14,4)})
    sb.set_style('white')
    plt.rcParams['xtick.major.pad']='0'
    
    plt1 = sb.lineplot(data = dailydataspec,
        x= 'Timeinterval',
        y= 'Movingavg_combined',
        # Remove markers
        color = '#0A2F6E',
        errorbar= None, 
    )
    # Plot 1
    # plt1 = sb.lineplot(data = dailydataspec,
    #     x= 'Timeinterval',
    #     y= 'Movingavg_s1df',
    #     # Remove markers
    #     color = '#0A2F6E',
    #     errorbar= None
    # )

    plt2 = sb.lineplot(
        data = avgdataspec,
        x= 'Timeinterval',
        y= 'Movingavg',
        color ='#689DF3',
        alpha=0.5,
        errorbar= None
    )

    # plt3 = sb.lineplot(data = dailydataspec,
    #     x= 'Timeinterval',
    #     y= 'Movingavg_kazd',
    #     # Remove markers
    #     color = '#0A2F6E',
    #     errorbar= None, 
    #     linestyle = 'dotted'
    # )



    l1= plt2.lines[0]
    l2 = plt2.lines[1]
    #l4 = plt2.lines[3]
    x2 = l2.get_xydata()[:,0]
    y2 = l2.get_xydata()[:,1]
    plt2.fill_between(x2,y2, color='#689DF3', alpha=0.3)


    # Set Formatting of plots
    plt1.margins(x=0.01, y = 0.01)
    plt1.set_title(str(snNamesDict['S1DF']), weight='bold',fontsize = '14')
    plt1.set_xlabel(None)
    plt1.set_ylabel('Rating',size=12)
    plt1.xaxis.grid(True,which='minor')
    plt1.yaxis.grid(False) # Whether to show vertical gridlines vertical gridlines# Show the vertical gridlines
    plt1.set_ylim(ymin = 0 , ymax = limity )
    plt1.set_xlim(0,)
    plt1.tick_params(axis='x', labelright = True, rotation=90,labelsize=12)
    plt1.tick_params(axis='y',labelsize=12)
    plt1.tick_params(left=True, bottom=True, color = '#787878')

    xticklist = [i+1 for i in range(0,len(x2),2)]
    plt1.set_xticks(xticklist)

   
    plt1.spines['right'].set_visible(False)
    plt1.spines['top'].set_visible(False)
    plt1.spines['bottom'].set_visible(True)
    plt1.spines['bottom'].set_color('#787878')
    plt1.spines['left'].set_visible(True)
    plt1.spines['left'].set_color('#787878')

    plt.legend([l1, l2], ['SN 1 Dallas + SN KAZD ' + str(dailydataspec['Dates'].unique()[0]),f'SN 1 Dallas {month_name} {year_num} average'], loc = 'upper center', bbox_to_anchor= (.5, -.22),frameon=False)
    plt.setp(plt1.get_legend().get_texts(), fontsize='12')
    chart = plt1.get_figure()
    plt.close()

    return chart


