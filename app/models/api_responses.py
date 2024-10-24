from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

class BaseAPIResponse(BaseModel):
    success: bool
    message: str

class ErrorAPIResponse(BaseAPIResponse):
    error_code: str
    error_details: Optional[Dict[str, Any]] = None

# This represents any JSON object, which could be a DataFrame converted to JSON
JSONObject = Dict[str, Any]

class StandardAPIResponse(BaseAPIResponse):
    """Standard API Response with data and metadata fields. Loose typing for data and metadata."""
    data: Optional[Any] = None
    metadata: Optional[Any] = None

class EngagementAPIResponse(BaseAPIResponse):
    data: Dict[str, List[Dict[Any, Any]]]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional information about the engagement data"
    )