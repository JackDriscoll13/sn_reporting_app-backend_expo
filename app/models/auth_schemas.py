from pydantic import BaseModel
from typing import Any, Dict, Optional

# These models are pretty basic, don't need anything fancy

# Email schema for validatng our emails
class EmailSchema(BaseModel):
    email: str

# User schema for validating our signup user data
class UserSchema(BaseModel):
    email: str
    password: str
    team: str

# Verification schema for validating our verification data
class VerificationCodeSchema(BaseModel):
    """
    Schema for validating our verification data. 

    :attr email: The email of the user
    :attr verification_code: The verification code sent to the user
    """
    email: str
    verification_code: str

# Login schema for validating our login data
class LoginSchema(BaseModel):
    email: str
    password: str

# New Password schema for validating our new password data
class NewPasswordSchema(BaseModel):
    token: str
    newpassword: str
