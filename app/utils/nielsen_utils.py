# Utils for Nielsen Endpoint 
import pandas as pd
import os 
import glob
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
import zipfile
import tempfile

## VERIFICATION FUNCTIONS for Verification of Daily Nielsen Files
def verify_columns(df: pd.DataFrame, expected_columns: list):
    """
    Get the Nielsen columns based on the dataframe columns.
    """
    # Check if the dataframe has the correct columns
    if not df.columns.tolist() == expected_columns:
        return False
    return True

def verify_date_range(df: pd.DataFrame) -> bool | list:
    """
    Verify the date range is valid.
    """
    # Check if the dataframe has the correct columns
    if len(df['Dates'].unique().tolist()) > 1:
        return False
    return True

def verify_no_dash_in_date(df: pd.DataFrame) -> bool:
    """
    Verify the date range is valid.
    """
    # Check if the dataframe has the correct columns
    if "-" in df['Dates'].unique().tolist()[0]:
        return False
    return True


def identify_nielsen_file(df: pd.DataFrame) -> str:
    """
    Identify the Nielsen file type based on the values in the Time column.
    """
    # Honestly the most reliable way to identify the file is by the number of unique values in the Time column
    # 15min files should 76 unique values in this column 
    # Dayparts should have less than 10, we could do this more deterministically but this is good enough
    # In case the format of this column changes I think this should stil work
    if len(df['Time'].unique().tolist()) > 70:
        return "15min"
    else: 
        return "Dayparts"
    
## Serving the latest benchmark file
def serve_latest_benchmark(prefix: str):
    base_path = "resources/nielsen/dailyBenchmark"
    pattern = os.path.join(base_path, f"{prefix}*.xlsx")
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"No {prefix} benchmark file found")
    
    # Sort files by modification time, most recent first
    latest_file = max(matching_files, key=os.path.getmtime)
    filename = os.path.basename(latest_file)

    return FileResponse(
        path=latest_file,
        filename=filename)

## Serving the latest benchmark file *NAME*
def serve_latest_benchmark_name(prefix: str):
    base_path = "resources/nielsen/dailyBenchmark"
    pattern = os.path.join(base_path, f"{prefix}*.xlsx")
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"No {prefix} benchmark file found")
    
    # Sort files by modification time, most recent first
    latest_file = max(matching_files, key=os.path.getmtime)
    filename = os.path.basename(latest_file)

    return {"filename": filename}


def verify_benchmark_date_range(df: pd.DataFrame) -> bool | list:
    """
    Verify the date range is valid.
    """
    # Check if the dataframe has the correct columns
    if len(df['Dates'].unique()[0].split("-")) <= 1:
        return False
    return True

def format_date_range(df:pd.DataFrame) -> str:
    """
    Get the most current date and the oldest date from the benchmark file.
    """
    # Get the most current date and the oldest date from the benchmark file.
    date_range = df['Dates'].unique().tolist()
    date_range_str = date_range[0]
    # Replace '/' with '_' in the date range string
    date_range_str = date_range_str.replace('/', '_')
    date_range_str = date_range_str.replace(' ', '')
    return date_range_str

### Filtering function for determining if daypart or 15min daily file before passing to main report function

def process_and_sort_daily_files(file0: UploadFile, file1: UploadFile):
    """
    Process and sort the 2 uploaded daily files into dayparts and 15-minute content.
    
    Args:
    file0 (UploadFile): First uploaded file
    file1 (UploadFile): Second uploaded file
    
    Returns:
    tuple: (daily_dayparts_content, daily_15min_content)
    
    Raises:
    HTTPException: If both required file types are not present
    """
    daily_dayparts_content = None
    daily_15min_content = None

    for file in [file0, file1]:
        content = file.file.read()
        if "Dayparts" in file.filename:
            daily_dayparts_content = content
        else:
            daily_15min_content = content

    if daily_dayparts_content is None or daily_15min_content is None:
        raise HTTPException(status_code=400, detail="Missing either dayparts or 15-minute file")

    return daily_dayparts_content, daily_15min_content

# Function to zip the eml files
def zip_eml_files(eml_file_paths: list):
    """
    Zip the eml files into a single zip file.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
        zip_filename = tmp_zip.name
        
    # Create the zip file
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for eml_path in eml_file_paths:
            zipf.write(eml_path, os.path.basename(eml_path))
    
    return zip_filename
    


