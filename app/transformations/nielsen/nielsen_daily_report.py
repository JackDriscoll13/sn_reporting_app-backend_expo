import io
from . import nielsen_daily_report_funcs as report_utils

def generate_nielsen_daily_report(db, user_email, 
                                benchmark_15min_content, benchmark_daypart_content,
                                daily_15min_content, daily_daypart_content):
    """
    Generate a Nielsen daily report.
    """
    print('Reading mappings from database->',end = ' ')
    # Read the 6 data mappings from the config file, can async these later
    dma_name_mapping = report_utils.get_dma_name_mapping_dict(db)
    dma_penetration_mapping = report_utils.get_dma_penetration_mapping_dict(db)   
    fifteen_min_order_mapping = report_utils.get_fifteen_min_order_mapping_dict(db)
    daypart_order_mapping = report_utils.get_daypart_order_mapping_dict(db)
    spectrum_station_names_mapping = report_utils.get_spectrum_station_names_dict(db)
    station_network_mapping = report_utils.get_station_network_mapping_dict(db)
    print('Done.')

    print('Reading report details from database ->',end = ' ')
    # Read the report details from the database
    # Have to get the subject_line_ids from the database first
    subject_line_ids = report_utils.get_subject_line_ids(db)
    # We can async these later calls later:
    subject_lines = report_utils.get_subject_lines(db)
    report_notes = report_utils.get_report_notes(db, subject_line_ids)
    report_recipients = report_utils.get_report_recipients(db, subject_line_ids)
    report_dma_lists = report_utils.get_report_dma_lists(db, subject_line_ids)
    print('Done.')

    # Clean the data
    print('Reading in and cleaning data ->',end = ' ')
    benchmark_15min_df = report_utils.clean_15min_data(io.BytesIO(benchmark_15min_content), 
                                                            station_network_mapping, fifteen_min_order_mapping, dma_name_mapping)
    daily_15min_df = report_utils.clean_15min_data(io.BytesIO(daily_15min_content), 
                                                            station_network_mapping, fifteen_min_order_mapping, dma_name_mapping)

    benchmark_daypart_df = report_utils.clean_daypart_data(io.BytesIO(benchmark_daypart_content), 
                                                            station_network_mapping, daypart_order_mapping,  dma_name_mapping)
    daily_daypart_df = report_utils.clean_daypart_data(io.BytesIO(daily_daypart_content), 
                                                            station_network_mapping, daypart_order_mapping, dma_name_mapping)
    print('Done.')
    # Add logic here to save this data to our database, can call another service
    #TODO: ADD LOGIC TO SAVE NIELSEN DATA TO DAILY NIELSEN DATABASE

    # Now we can generate the report, first we create a directory to store the images
    print('Preparing to generate images, grabbing daily date, creating image directory, retrieving unique DMAs ->',end = ' ')
    dateofdata = str(daily_15min_df['Dates'].unique()[0])
    img_dump_path = report_utils.create_image_directory(user_email) 
    uniquedmas = {x for i in report_dma_lists for x in i}
    print('Done.')

    # Create the html and image objects for each DMA
    print('Generating image objects ->',end = ' ')

    dma_html_dict, chart_path_dict, table_path_dict = report_utils.create_dma_html(uniquedmas, img_dump_path, 
                                                                                   benchmark_15min_df, benchmark_daypart_df,
                                                                                   daily_15min_df, daily_daypart_df,
                                                                          spectrum_station_names_mapping, dma_penetration_mapping)
    print('Done.')
    print('Creating eml directory ->',end = ' ')
    eml_dump_path = report_utils.create_eml_directory(user_email)
    print('Done.')

    print('Creating Emails ->',end = ' ')
    eml_file_paths = report_utils.create_nielsen_daily_emails(report_dma_lists, user_email, dateofdata,
                                             subject_lines, report_notes, report_recipients,
                                             dma_html_dict, chart_path_dict, table_path_dict,
                                             eml_dump_path)
    print('Done.')

    return eml_file_paths