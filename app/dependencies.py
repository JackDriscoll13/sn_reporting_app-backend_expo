import os
from dotenv import load_dotenv

# Connection Logic 
from utils.connect_db import connect_db
from utils.aws_clients import create_s3_client, create_ses_client
from models.custom_types import AWSDatabaseCredentials, AWSCredentials

def get_db():
    """Dependency that provides a database session."""
    load_dotenv()
    rds_connection = AWSDatabaseCredentials(
        db_host=os.getenv('RDS_URL'),
        db_port=os.getenv('RDS_PORT'),
        db_user=os.getenv('RDS_USERNAME'),
        db_password=os.getenv('RDS_PASSWORD'),
        db_name=os.getenv('RDS_DB_NAME')
    )

    db_gen = connect_db(rds_connection)
    try:
        db = next(db_gen)  # This will execute the code inside connect_db() up to the first yield
        yield db
    except StopIteration:
        pass
    finally:
        db_gen.close()  # Close the generator, which will execute the finally block

def get_ses_client():
    """
    Dependency that provides an AWS SES client. 
    """
    load_dotenv()
    aws_credentials = AWSCredentials(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    return create_ses_client(aws_credentials)

def get_s3_client():
    """
    Dependency that provides an AWS S3 client.
    """
    load_dotenv()
    aws_credentials = AWSCredentials(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    return create_s3_client(aws_credentials)

def get_JWT_key():
    """
    Dependency that provides the JWT key.
    """
    load_dotenv()
    return os.getenv('JWT_SECRET')

def get_frontend_url():
    """
    Dependency that provides the frontend URL.
    """
    load_dotenv()
    return os.getenv('FRONTEND_URL')