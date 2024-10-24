from fastapi import APIRouter, UploadFile, Form, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import pandas as pd
import warnings
import os
import glob
from sqlalchemy.orm import Session
# Models 
from models.api_responses import StandardAPIResponse
from models.nielsen_schemas import NielsenTestSchema, NielsenReportSchema, NielsenSubjectLineSchema, NielsenEMLDownloadSchema

# Dependencies
from dependencies import get_db

# Nielsen Report Functions
from transformations.nielsen.test_eml import create_eml_download_email_test
from transformations.nielsen.nielsen_daily_report import generate_nielsen_daily_report

# Nielsen Utils
from utils.nielsen_utils import verify_columns, verify_date_range, identify_nielsen_file, verify_no_dash_in_date
from utils.nielsen_utils import serve_latest_benchmark, serve_latest_benchmark_name
from utils.nielsen_utils import verify_benchmark_date_range, format_date_range
from utils.nielsen_utils import process_and_sort_daily_files, zip_eml_files
# Nielsen Crud
from crud import nielsen_crud

router = APIRouter()

###########  DAILY REPORT ENDPOINTS ##########################
@router.post("/verify_upload_file", response_model=StandardAPIResponse)
def verify_upload_file(file: UploadFile = File(...)):
    """
    Verify the upload file.
    """
    print("Verifying: ", file.filename)
    # Verify the file is a valid CSV file
    if not file.filename.endswith('.xlsx'):
        return StandardAPIResponse(success=False, message="Invalid file type. Please upload an excel file.", data=None, metadata=None)
    # Verify the file is not empty 
    if file.size == 0:
        return StandardAPIResponse(success=False, message="File is empty. Please upload a valid file.", data=None, metadata=None)

    # Read the excel file
    try: 
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = pd.read_excel(file.file, sheet_name='Live+Same Day, TV Households',header = 8,skipfooter=8).ffill()
            # Verify the columns are correct
            if not verify_columns(df, 
                                  ['Affil.', 'Daypart', 'Custom Range', 'Time', 'Viewing Source', 'Demo',
                                  'Dates', 'Geography / Metrics', 'RTG % (X.X)', 'Indicator ']):
               raise Exception(f"Columns in file do not match expected Nielsen column names. "
                               f"Columns in file: {df.columns.tolist()}, "
                               f"Expected columns: ['Affil.', 'Daypart', 'Custom Range', 'Time', 'Viewing Source', 'Demo', "
                               f"'Dates', 'Geography / Metrics', 'RTG % (X.X)', 'Indicator ']")
            
            # Verify the date range is valid, if so grab the date
            if not verify_date_range(df): 
                raise Exception(f"Could not identiify file because date range is greater than 1."
                               f"Date range in file: {df['Dates'].unique().tolist()}, ")
            
            # Verify there is no dash in the date
            if not verify_no_dash_in_date(df): 
                raise Exception(f"Looks like there is a dash in one of your dates. Please remove the dash and try again."
                               f"Date range in file: {df['Dates'].unique().tolist()}, ")

            # If all these checks pass, we can identify the file with the date and type (15min or dayparts)
            date = df['Dates'].unique().tolist()[0]
            nielsen_file_type = identify_nielsen_file(df)
    except Exception as e:
        print(e)
        return StandardAPIResponse(success=False, message=f"Error verifying the file: {e}", data=None, metadata=None)
    
    
    return StandardAPIResponse(success=True, message=f"{nielsen_file_type} - {date}", data=None, metadata=None)


@router.post("/test_eml_download")
def test_eml_download(data: NielsenTestSchema):
    """
    Test the EML download.
    """
    eml_file_path = create_eml_download_email_test(data.toEmail)
    return FileResponse(eml_file_path, filename="email_report.eml")



### MAIN GENERATION ENDPOINT ##########################
@router.post("/generate_nielsen_report")
def generate_nielsen_report(
    db: Session = Depends(get_db),
    toEmail: str = Form(...),
    uploadToDb: bool = Form(...),
    autoDownload: bool = Form(...),
    file0: UploadFile = File(...),
    file1: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate a set of nielsen reports for a single date.
    """
    print(toEmail)
    print(uploadToDb)
    print(file0.filename)
    print(file1.filename)

    daily_dayparts_content, daily_15min_content = process_and_sort_daily_files(file0, file1)


    # We should also read the contents of the benchmark file into memory
    # Eventually we will read these from s3, for now they are on the server
    # Read the contents of the benchmark files into memory
    benchmark_15min_name = serve_latest_benchmark_name("Benchmark-15min")
    benchmark_daypart_name = serve_latest_benchmark_name("Benchmark-Dayparts")

    benchmark_15min_path = os.path.join("resources/nielsen/dailyBenchmark", benchmark_15min_name['filename'])
    benchmark_daypart_path = os.path.join("resources/nielsen/dailyBenchmark", benchmark_daypart_name['filename'])

    with open(benchmark_15min_path, "rb") as f:
        benchmark_15min_content = f.read()
    
    with open(benchmark_daypart_path, "rb") as f:
        benchmark_daypart_content = f.read()

    # Now we pass the data to the nielsen daily report function
    eml_file_paths = generate_nielsen_daily_report(db, toEmail, 
                                  benchmark_15min_content, benchmark_daypart_content, 
                                  daily_15min_content, daily_dayparts_content)
    
    # TWO distinct outcomes, if autodownload is true, we return two file responses 
    if autoDownload:
        zip_filename = zip_eml_files(eml_file_paths)
        background_tasks.add_task(os.unlink, zip_filename)
        # Use FileResponse with a callback to delete the file after sending
        return FileResponse(
            zip_filename, 
            filename="nielsen_reports.zip",
        )

    print(eml_file_paths)
    # IF autodownload is false we return a success message and the eml file paths
    return StandardAPIResponse(success=True, message=f"EML files created", data=eml_file_paths, metadata=None)

@router.post("/download_daily_eml_report")
def download_daily_eml_report(
    data: NielsenEMLDownloadSchema,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Download the EML report.
    """
    filename = os.path.basename(data.file_path)
    background_tasks.add_task(os.unlink, data.file_path)
    return FileResponse(data.file_path, filename=filename)

    




###############################################    
##### CONFIG ENDPOINTS #######################
#### BENCHMARK ENDPOINTS #######################
@router.get("/download_benchmark_15min")
def download_benchmark_15min():
    """
    Get the most recent 15-minute benchmark file.
    """
    
    print("Getting 15min benchmark")
    return serve_latest_benchmark("Benchmark-15min")

@router.get("/get_benchmark_15min_name")
def get_benchmark_15min_name():
    """
    Get the name of the most recent 15-minute benchmark file.
    """
    return serve_latest_benchmark_name("Benchmark-15min")


@router.get("/download_benchmark_dayparts")
def download_benchmark_dayparts():
    """
    Get the most recent daypart benchmark file.
    """
    return serve_latest_benchmark("Benchmark-Dayparts")

@router.get("/get_benchmark_dayparts_name")
def get_benchmark_dayparts_name():
    """
    Get the name of the most recent daypart benchmark file.
    """
    return serve_latest_benchmark_name("Benchmark-Dayparts")


# Verify the benchmark file is valid 
@router.post("/verify_benchmark_file")
def verify_benchmark_file(file: UploadFile = File(...)):
    """
    Verify the benchmark file is valid.
    """
        # Verify the file is a valid CSV file
    if not file.filename.endswith('.xlsx'):
        return StandardAPIResponse(success=False, message="Invalid file type. Please upload an excel file.", data=None, metadata=None)
    # Verify the file is not empty 
    if file.size == 0:
        return StandardAPIResponse(success=False, message="File is empty. Please upload a valid file.", data=None, metadata=None)

    # Read the excel file
    try: 
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = pd.read_excel(file.file, sheet_name='Live+Same Day, TV Households',header = 8,skipfooter=8).ffill()
            # Verify the columns are correct
            if not verify_columns(df, 
                                  ['Affil.', 'Daypart', 'Custom Range', 'Time', 'Viewing Source', 'Demo',
                                  'Dates', 'Geography / Metrics', 'RTG % (X.X)', 'Indicator ']):
               raise Exception(f"Columns in file do not match expected Nielsen column names. "
                               f"Columns in file: {df.columns.tolist()}, "
                               f"Expected columns: ['Affil.', 'Daypart', 'Custom Range', 'Time', 'Viewing Source', 'Demo', "
                               f"'Dates', 'Geography / Metrics', 'RTG % (X.X)', 'Indicator ']")

            # Verify the date range is valid, if so grab the date
            if not verify_benchmark_date_range(df): 
                raise Exception(f"Benchmark files must contain a range of dates, seperated by a dash."
                               f"Date range in file: {df['Dates'].unique().tolist()}, ")
            
            # If all these checks pass, we can identify the file with the date and type (15min or dayparts)
            date_range = format_date_range(df)
            nielsen_file_type = identify_nielsen_file(df)
    except Exception as e:
        print(e)
        return StandardAPIResponse(success=False, message=f"Error verifying the file: {e}", data=None, metadata=None)
    
    return StandardAPIResponse(success=True, message=f"Benchmark-{nielsen_file_type}-{date_range}", data=None, metadata=None)

@router.post("/update_benchmark_files")
def update_benchmark_file(files: List[UploadFile] = File(...)):
    """
    Update the benchmark file.
    """
    # Delete all files in the benchmark folder
    base_path = "resources/nielsen/dailyBenchmark"
    for file in glob.glob(f"{base_path}/*"):
        os.remove(file)

    # Save the new files
    saved_files = []
    for file in files:
        file_location = os.path.join(base_path, file.filename)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        saved_files.append(file.filename)
    
    return StandardAPIResponse(success=True, message=f"Benchmark files updated: {', '.join(saved_files)}", data=None, metadata=None)

# Get the subject lines from the database
@router.get("/get_subject_lines")
def get_subject_lines(db: Session = Depends(get_db)):
    """
    Get the subject lines from the database.
    """
    subject_lines = nielsen_crud.get_nielsen_subject_lines(db)
    # Convert the list of tuples to a list of dictionaries
    subject_lines_json = [
        {"id": id, "subject": subject}
        for id, subject in subject_lines
    ]
    return StandardAPIResponse(success=True, message=f"Subject lines retrieved", data=subject_lines_json, metadata=None)

@router.post("/update_subject_lines")
def update_subject_lines(data: List[dict], db: Session = Depends(get_db)):
    """
    Update the subject lines in the database.
    """
    # The first thing we do is update the subject lines 
    nielsen_crud.update_nielsen_subject_lines(db, data)

    # If there are new subject lines, we need to create the recipient tables
    print("Subject lines updated")
    print(data)
    for subject in data:
        if not nielsen_crud.check_recpiant_table_exists(db, subject['id']):
            print(f"Creating table for subject line {subject['id']}")
            nielsen_crud.create_recipient_table(db, subject['id'])
        if not nielsen_crud.check_report_note_table_exists(db, subject['id']):
            print(f"Creating table for report notes {subject['id']}")
            nielsen_crud.create_report_note_table(db, subject['id'])
        if not nielsen_crud.check_dma_list_table_exists(db, subject['id']):
            print(f"Creating table for dma list {subject['id']}")
            nielsen_crud.create_dma_list_table(db, subject['id'])



    return StandardAPIResponse(success=True, message=f"Subject lines updated", data=None, metadata=None)


# Get the recipients from the database
@router.get("/get_email_recipients")
def get_email_recipients( db: Session = Depends(get_db)):
    """
    Get the email recipients from the database
    """
    # First we need to return all the tables that exist for subject lines (usually there is two)
    subject_lines = nielsen_crud.get_nielsen_subject_lines(db)
    subject_line_ids = [id for id, _ in subject_lines]
    print(subject_line_ids)
    # Then we need to get the recipients for each subject line
    recipients = {}
    for id in subject_line_ids: 
        recipients[str(id)] = nielsen_crud.get_email_recipients(id, db) 

    return StandardAPIResponse(success=True, message=f"Subject lines retrieved", data=recipients, metadata=None)

@router.post("/update_email_recipients")
def update_email_recipients(data: dict[str, list[str]], db: Session = Depends(get_db)):
    """
    Update the email recipients in the database.
    """
    for subject_line_id, recipients in data.items():
        print(subject_line_id, recipients)
        if len(recipients) > 0:
            nielsen_crud.update_email_recipients(subject_line_id, recipients, db)

    return StandardAPIResponse(success=True, message=f"Email recipients updated", data=None, metadata=None)


@router.get("/get_report_notes")
def get_report_notes(db: Session = Depends(get_db)):
    """
    Get the report notes from the database.
    """
        # First we need to return all the tables that exist for subject lines (usually there is two)
    subject_lines = nielsen_crud.get_nielsen_subject_lines(db)
    subject_line_ids = [id for id, _ in subject_lines]
    # Then we need to get the report notes for each subject line
    report_notes = {}
    for id in subject_line_ids: 
        report_notes[str(id)] = nielsen_crud.get_report_notes(id, db) 

    print(report_notes)
    return StandardAPIResponse(success=True, message=f"Report notes retrieved", data=report_notes, metadata=None)

@router.post("/update_report_notes")
def update_report_notes(data: dict[str, str], db: Session = Depends(get_db)):
    """
    Update the email recipients in the database.
    """
    for subject_line_id, note in data.items():
        print(subject_line_id, note)
        nielsen_crud.update_report_notes(subject_line_id, note, db)

    return StandardAPIResponse(success=True, message=f"Report notes updated", data=None, metadata=None)

@router.get("/get_dma_list")
def get_dma_list(db: Session = Depends(get_db)):
    """
    Get the dma list from the database.
    """
    subject_lines = nielsen_crud.get_nielsen_subject_lines(db)
    subject_line_ids = [id for id, _ in subject_lines]
    dma_list = {}
    for id in subject_line_ids: 
        dma_list[str(id)] = nielsen_crud.get_dma_list(id, db)   

    return StandardAPIResponse(success=True, message=f"Dma list retrieved", data=dma_list, metadata=None)


### ADJUSTABLE MAPPINGS ENDPOINTS #######################
@router.get("/get_dma_name_mapping")
def get_dma_name_mapping(db: Session = Depends(get_db)):
    """
    Get the dma name mapping from the database.
    """
    dma_mapping = nielsen_crud.get_dma_mapping(db)
    return StandardAPIResponse(success=True, message=f"Dma name mapping retrieved", data=dma_mapping, metadata=None)

@router.post("/update_dma_name_mapping")
def update_dma_name_mapping(data: list[dict], db: Session = Depends(get_db)):
    """
    Update the dma name mapping in the database.
    """
    nielsen_crud.update_dma_mapping(db, data)

    # Add logic to add the new dma names to the penetration table

    return StandardAPIResponse(success=True, message=f"Dma name mapping updated", data=None, metadata=None)

@router.get("/get_dma_penetration")
def get_dma_penetration(db: Session = Depends(get_db)):
    """
    Get the dma penetration from the database.
    """
    dma_penetration = nielsen_crud.get_dma_penetration(db)
    return StandardAPIResponse(success=True, message=f"Dma penetration retrieved", data=dma_penetration, metadata=None)

#######################################################
# NON ADJUSTABLE MAPPINGS ENDPOINTS ###################
#######################################################
# These enpoints return dictionaries in a slightly different format as they are used in the backend pandas functions to map nielsen data


# HERES AN EXAMPLE, USE THIS FORMAT FOR ALL NON ADJUSTABLE MAPPINGS in the nielsen report (config readings)
# @router.get("/get_station_network_mapping_dict")
# def get_station_network_mapping_dict(db: Session = Depends(get_db)):
#     """
#     Get the station network mapping from the database.
#     """
#     station_network_mapping = nielsen_crud.get_station_network_mapping(db)
#     station_network_mapping_dict = station_network_mapping.set_index('station_name')['network'].to_dict()
#     return StandardAPIResponse(success=True, message=f"Station network mapping retrieved", data=station_network_mapping_dict, metadata=None)


@router.get("/get_4_additional_mapping_file")
def get_4_additional_mapping_file(db: Session = Depends(get_db)):
    """
    Get the 4 additional mapping file from the database. Return as an excel file.
    """
    station_network_mapping = nielsen_crud.get_station_network_mapping(db)
    spectrum_station_name_mapping = nielsen_crud.get_spectrum_station_name_mapping(db)
    daypart_order_mapping = nielsen_crud.get_daypart_order_mapping(db)
    fifteen_min_order_mapping = nielsen_crud.get_fifteen_min_order_mapping(db)

    dataframes = [station_network_mapping, spectrum_station_name_mapping, daypart_order_mapping, fifteen_min_order_mapping]
    sheet_names = ["station_network_mapping", "spectrum_station_name_mapping", "daypart_order_mapping", "fifteen_min_order_mapping"]
    output_file = "resources/nielsen/4_additional_mapping.xlsx"

    if len(dataframes) != len(sheet_names):
        raise ValueError("Number of DataFrames must match number of sheet names")

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for df, sheet_name in zip(dataframes, sheet_names):
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Excel file '{output_file}' has been created with {len(dataframes)} sheets.")

    # Read the excel file
    return FileResponse(path="resources/nielsen/4_additional_mapping.xlsx", filename="additional_mappings.xlsx")

