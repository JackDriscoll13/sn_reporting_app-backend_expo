from pydantic import BaseModel
from fastapi import UploadFile

class NielsenTestSchema(BaseModel):
    """
    Schema for testing the Nielsen EML download.

    :attr toEmail: The email address to send the EML file to.
    """
    toEmail: str


class NielsenReportSchema(BaseModel):
    """
    Schema for generating a Nielsen report.

    :attr file_15min: The 15min file to generate the report from.
    :attr file_daypart: The daypart file to generate the report from.
    :attr date: The date of the Nielsen data in mm-dd-yyyy format.
    """
    file_15min: UploadFile
    file_daypart: UploadFile
    date: str


class NielsenSubjectLineSchema(dict):
    """
    Schema for updating the subject lines in the Nielsen table.

    :attr id: The id of the subject line.
    :attr subject: The subject line.
    """
    id: int
    subject: str


class NielsenEMLDownloadSchema(BaseModel):
    """
    Schema for downloading the EML report.

    :attr file_path: The path to the EML file.
    """
    file_path: str
   