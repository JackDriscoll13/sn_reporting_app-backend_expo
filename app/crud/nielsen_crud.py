from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd

# Subject Lines
def get_nielsen_subject_lines(db: Session):
    """
    Get the subject lines from the Nielsen table.
    """
    result = db.execute(
        text("SELECT * FROM nielsen_report_config.email_subject_lines;")
    )
    return result.fetchall()

def update_nielsen_subject_lines(db: Session, subject_lines: list):
    """
    Update the subject lines in the Nielsen table.
    """
    db.execute(
        text("UPDATE nielsen_report_config.email_subject_lines SET subject = :subject WHERE id = :id"),
        subject_lines
    )
    db.commit()

# Recipiants 
def check_recpiant_table_exists(db: Session, subject_line_id: int):
    """
    Check if the recipient table exists. These tables are created dynamically based on the subject line id.
    """
    query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'nielsen_report_config'
            AND table_name = :table_name
        )
    """)
    result = db.execute(query, {"table_name": f"email_recipients_{subject_line_id}"})
    exists = result.scalar()
    result.close()
    return exists

def create_recipient_table(db: Session, subject_line_id: int):
    """
    Create the recipient table. Created dynamically based on the subject line id.
    """
    db.execute(text(f"CREATE TABLE nielsen_report_config.email_recipients_{subject_line_id} (email VARCHAR(255) PRIMARY KEY)"))
    print(f"Created table: nielsen_report_config.email_recipients_{subject_line_id}")
    db.commit()


def get_email_recipients(subject_line_id: int, db: Session):
    """
    Get all email recipients.
    """
    result = db.execute(
        text(f"SELECT * FROM nielsen_report_config.email_recipients_{subject_line_id};")
    )
    recipients = [row[0] for row in result]  # Convert Row objects to a list of email strings
    result.close()
    return recipients

def update_email_recipients(subject_line_id: int, recipients: list, db: Session):
    """
    Update the email recipients in the database.
    """
    db.execute(text(f"DELETE FROM nielsen_report_config.email_recipients_{subject_line_id};"))
    
    # Convert recipients to a list of dictionaries
    recipients_dicts = [{"email": email} for email in recipients]
    
    db.execute(
        text(f"INSERT INTO nielsen_report_config.email_recipients_{subject_line_id} (email) VALUES (:email)"),
        recipients_dicts
    )
    db.commit()


# Report Notes
def check_report_note_table_exists(db: Session, subject_line_id: int):
    """
    Check if the report note table exists.
    """
    query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'nielsen_report_config'
            AND table_name = :table_name
        )
    """)
    result = db.execute(query, {"table_name": f"report_notes_{subject_line_id}"})
    exists = result.scalar()
    result.close()
    return exists

def create_report_note_table(db: Session, subject_line_id: int):
    """
    Create the report note table.
    """ 
    db.execute(text(f"CREATE TABLE nielsen_report_config.report_notes_{subject_line_id} (note VARCHAR(255))"))
    print(f"Created table: nielsen_report_config.report_notes_{subject_line_id}")
    db.commit()

def get_report_notes(subject_line_id: int, db: Session):
    """
    Get the report note from the database.
    """
    result = db.execute(text(f"SELECT * FROM nielsen_report_config.report_notes_{subject_line_id};"))
    note = result.scalar()  # Get the first column of the first row
    result.close()
    return note if note else ""  # Return an empty string if no note is found

def update_report_notes(subject_line_id: int, note: str, db: Session):
    """
    Update the report note in the database.
    """
    db.execute(text(f"TRUNCATE TABLE nielsen_report_config.report_notes_{subject_line_id}"))
    db.execute(text(f"INSERT INTO nielsen_report_config.report_notes_{subject_line_id} (note) VALUES (:note)"), {"note": note})
    db.commit()

# Dma List
def check_dma_list_table_exists(db: Session, subject_line_id: int):
    """
    Check if the dma list table exists.
    """
    query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'nielsen_report_config'
            AND table_name = :table_name
        )
    """)
    result = db.execute(query, {"table_name": f"dma_list_{subject_line_id}"})
    exists = result.scalar()
    result.close()
    return exists

def create_dma_list_table(db: Session, subject_line_id: int):
    """
    Create the dma list table.
    """ 
    db.execute(text(f"CREATE TABLE nielsen_report_config.dma_list_{subject_line_id} (dma VARCHAR(255))"))
    print(f"Created table: nielsen_report_config.dma_list_{subject_line_id}")
    db.commit()

def get_dma_list(subject_line_id: int, db: Session):
    """
    Get the dma list from the database.
    """
    result = db.execute(
        text(f"SELECT * FROM nielsen_report_config.dma_list_{subject_line_id};")
    )
    dma_list = [row[0] for row in result]  # Convert Row objects to a list of dma strings
    result.close()
    return dma_list

########################################################
# ADJUSTABLE MAPPINGS
#########################################################

def get_dma_mapping(db: Session):
    """
    Get the dma mapping from the database.
    """
    result = db.execute(text("SELECT * FROM nielsen_report_config.dma_name_mapping;"))
    dma_mapping = [dict(row._mapping) for row in result]
    result.close()
    print(dma_mapping)
    return dma_mapping

def update_dma_mapping(db: Session, dma_mapping: list[dict]):
    """
    Update the dma mapping in the database by truncating the existing table and inserting new mappings.
    """
    try:
        # Truncate the existing table
        db.execute(text("TRUNCATE TABLE nielsen_report_config.dma_name_mapping"))
        
        # Insert new mappings
        insert_query = text("""
            INSERT INTO nielsen_report_config.dma_name_mapping (nielsen_dma_name, sn_dma_name, penetration_percent)
            VALUES (:nielsen_dma_name, :sn_dma_name, :penetration_percent)
        """)
        
        db.execute(insert_query, dma_mapping)
        
        db.commit()
        print("DMA mapping updated successfully")
    except Exception as e:
        db.rollback()
        print(f"Error updating DMA mapping: {str(e)}")
        raise



########################################################
# Aditional, non adjustable mappings, returned as pandas df for backend
########################################################
def get_station_network_mapping(db: Session) -> pd.DataFrame:
    """
    Get the station network mapping from the database.
    """
    result = pd.read_sql("SELECT * FROM nielsen_main.station_network_mapping", db.connection())
    return result

def get_spectrum_station_name_mapping(db: Session) -> pd.DataFrame:
    """
    Get the spectrum station name mapping from the database.
    """
    result = pd.read_sql("SELECT * FROM nielsen_main.spectrum_station_names", db.connection())
    return result

def get_daypart_order_mapping(db: Session) -> pd.DataFrame:
    """
    Get the daypart order mapping from the database.
    """
    result = pd.read_sql("SELECT * FROM nielsen_main.daypart_order_mapping", db.connection())
    return result

def get_fifteen_min_order_mapping(db: Session) -> pd.DataFrame:
    """
    Get the fifteen minute order mapping from the database.
    """
    result = pd.read_sql("SELECT * FROM nielsen_main.fifteen_minute_order_mapping", db.connection())
    return result


## Adjustable Mapping, but returned as a dataframe for the backend nielsen_daily_report
def get_dma_name_mapping(db: Session) -> pd.DataFrame:
    """
    Get the dma name mapping from the database.
    """
    result = pd.read_sql("SELECT nielsen_dma_name, sn_dma_name FROM nielsen_report_config.dma_name_mapping", db.connection())
    return result

def get_dma_penetration_mapping(db: Session) -> pd.DataFrame:
    """
    Get the dma penetration from the database.
    """
    result = pd.read_sql("SELECT sn_dma_name, penetration_percent FROM nielsen_report_config.dma_name_mapping", db.connection())
    return result

##################
#### REPORT DETAILS, RETURNED AS PANDAS DATAFRAMES FOR THE BACKEND 
###################
def get_subject_lines_as_dataframe(db: Session) -> pd.DataFrame:
    """
    Get the subject lines from the database.
    """
    result = pd.read_sql("SELECT * FROM nielsen_report_config.email_subject_lines", db.connection())
    return result

def get_report_notes_as_dataframe(db: Session, subject_line_id: str|int) -> pd.DataFrame:
    """
    Get the report notes from the database.
    """
    result = pd.read_sql(f"SELECT * FROM nielsen_report_config.report_notes_{subject_line_id}", db.connection())
    return result

def get_report_recipients_as_dataframe(db: Session, subject_line_id: str|int) -> pd.DataFrame:
    """
    Get the report recipients from the database.
    """
    result = pd.read_sql(f"SELECT * FROM nielsen_report_config.email_recipients_{subject_line_id}", db.connection())
    return result

def get_report_dma_lists_as_dataframe(db: Session, subject_line_id: str|int) -> pd.DataFrame:
    """
    Get the report dma lists from the database.
    """
    result = pd.read_sql(f"SELECT * FROM nielsen_report_config.dma_list_{subject_line_id}", db.connection())
    return result

