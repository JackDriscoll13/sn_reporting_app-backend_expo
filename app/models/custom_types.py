from datetime import datetime
from pydantic import GetCoreSchemaHandler, BaseModel, Field, field_validator
from pydantic.fields import Field as FieldInfo
from pydantic_core import core_schema
from typing import Any, Optional
import re 

# The below objects are pydantic models used to validate different datatypes in our application. 


# Custom string Types
class FullMonthStr(str):
    """
    A custom string type that represents a full month in the format 'Month Year' (e.g., 'January 2022').

    Used in receiving API requests and responses from our frontend. This type is used to ensure that the month is in the correct format.
    """

    # This ensures that the custom type is correctly serialized and deserialized
    # Basically ensures that pydantic knows how to handle this custom type
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, value: str) -> 'FullMonthStr':
        try:
            datetime.strptime(value, "%B %Y")
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid month format. Expected 'Month Year' (e.g., 'January 2022'), got '{value}'")

    def __repr__(self):
        return f"FullMonthStr({super().__repr__()})"
    

class AWSDatabaseCredentials(BaseModel):
    """
    A custom class to validate AWS Database credentials

    :param db_host: The hostname of the RDS instance
    :param db_port: The port number for the database connection
    :param db_name: The name of the database
    :param db_user: The username for database access
    :param db_password: The password for database access
    """
    db_host: str = Field(..., description="The hostname of the RDS instance")
    db_port: int = Field(..., ge=1, le=65535, description="The port number for the database connection")
    db_name: str = Field(..., min_length=1, description="The name of the database")
    db_user: str = Field(..., min_length=1, description="The username for database access")
    db_password: str = Field(..., min_length=8, description="The password for database access")

    @field_validator('db_host')
    @classmethod
    def validate_db_host(cls, v: str) -> str:
        # Basic validation for hostname format
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid AWS hostname format')
        return v

    @field_validator('db_name', 'db_user', 'db_password')
    @classmethod
    def no_whitespace(cls, v: str) -> str:
        if ' ' in v:
            raise ValueError('Database Name, Username, Password should not contain whitespace')
        return v

  
class AWSCredentials(BaseModel):
    """
    A custom class to validate AWS credentialsin our env file

    :param aws_access_key_id: The AWS access key ID
    :param aws_secret_access_key: The AWS secret access key
    :param region_name: The AWS region name (optional)
    """
    aws_access_key_id: str = Field(..., min_length=16, max_length=128, description="The AWS access key ID")
    aws_secret_access_key: str = Field(..., min_length=40, description="The AWS secret access key")
    region_name: Optional[str] = Field(None, description="The AWS region name")

    @field_validator('aws_access_key_id')
    @classmethod
    def validate_access_key_id(cls, v: str) -> str:
        if not re.match(r'^[A-Z0-9]+$', v):
            raise ValueError('Invalid AWS access key ID format')
        return v

    @field_validator('aws_secret_access_key')
    @classmethod
    def validate_secret_access_key(cls, v: str) -> str:
        if ' ' in v:
            raise ValueError('AWS secret access key should not contain whitespace')
        return v

    @field_validator('region_name')
    @classmethod
    def validate_region_name(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Invalid AWS region name format')
        return v
