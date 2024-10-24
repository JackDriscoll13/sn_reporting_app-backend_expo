## Connect to AWS Services

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models.custom_types import AWSDatabaseCredentials, AWSCredentials

import boto3

def create_s3_client(credentials: AWSCredentials) -> boto3.client:
    """
    Create an S3 client using the provided credentials

    :param credentials: AWSS3Credentials object containing the necessary AWS credentials
    :return: boto3 S3 client object
    """
    return boto3.client(
        's3',
        aws_access_key_id=credentials.aws_access_key_id,
        aws_secret_access_key=credentials.aws_secret_access_key, 
        region_name=credentials.region_name
    )

def create_ses_client(credentials: AWSCredentials) -> boto3.client:
    """
    Create an SES client using the provided credentials

    :param credentials: AWSCredentials object containing the necessary AWS credentials
    :return: boto3 SES client object
    """
    return boto3.client(
        'ses',
        aws_access_key_id=credentials.aws_access_key_id,
        aws_secret_access_key=credentials.aws_secret_access_key, 
        region_name=credentials.region_name
    )

