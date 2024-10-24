# Fast Api Imports
from fastapi import APIRouter, Depends, HTTPException

# Imports for Hashing and Passwords
import random
from datetime import datetime, timedelta, timezone

# Dependencies
from dependencies import get_db, get_ses_client, get_JWT_key, get_frontend_url

# Models
import boto3
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.auth_schemas import EmailSchema, UserSchema, VerificationCodeSchema, LoginSchema, NewPasswordSchema
from models.api_responses import StandardAPIResponse

# Crud Operations
from crud import auth_crud

# PW Hashing
from utils.auth_utils import hash_password, verify_password

#JWT for login
import jwt 

# AWS Email
import utils.aws_email as aws_email

router = APIRouter()

@router.post("/check_email", response_model=StandardAPIResponse)
def check_email(email:EmailSchema, db: Session = Depends(get_db)):
    """
    Check if an email is already in use. or is not pre approved.
    """
    is_preapproved = auth_crud.get_email_preapproved(email.email, db)
    is_existing = auth_crud.get_email_is_existing(email.email, db)
    response = {
        "is_preapproved": is_preapproved,
        "is_existing": is_existing
    }
    if is_preapproved and not is_existing:
        message = "Email is preapproved and available for signup."
    elif is_existing: 
        message = "Email is already in use."
    else: 
        message = "Email is not preapproved. Please contact the audince insights team to request access."
    # Even tho the email is not preapproved, we still return true because we want to display the message
    return StandardAPIResponse(success=True, message=message, data=response, metadata=None)

# 2.A Add the email to the verify_users table along with a expiry timestamp and verification code,
# 2.B AND send the verification code to the email address
@router.post("/send_verification_code", response_model=StandardAPIResponse)
def send_verification_code(user: UserSchema, db: Session = Depends(get_db), ses_client: boto3.client = Depends(get_ses_client)):
    """
    Send a verification email to the user.
    """
    # Generate a random verification code
    verification_code = random.randint(100000, 999999)
    expiry_time = datetime.now() + timedelta(hours=24)
    hashed_password = hash_password(user.password)
    # Update the user's verification code and expiry time
    auth_crud.update_user_verification_code(user.email, user.team, hashed_password, verification_code, expiry_time, db)

    # Now we sent the email to the user
    try:
        aws_email.send_verification_code_email(ses_client, user.email, verification_code)
        email_sent = True
    except Exception as e:
        email_sent = False
        print(f"Failed to send email: {e}")

    if email_sent:
        return StandardAPIResponse(success=True, message="verification_email_sent", data=None, metadata=None)
    else:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

@router.post("/refresh_verification_code", response_model=StandardAPIResponse)
def refresh_verification_code(email:EmailSchema, db: Session = Depends(get_db), ses_client: boto3.client = Depends(get_ses_client)):
    """
    Refresh the verification code for a user.
    """
    # Generate a random verification code
    verification_code = random.randint(100000, 999999)
    expiry_time = datetime.now() + timedelta(hours=24)
    auth_crud.refresh_verification_code(email.email, verification_code, expiry_time, db)

    # Now we sent the email to the user
    try:
        aws_email.send_verification_code_email(ses_client, email.email, verification_code)
        email_sent = True
    except Exception as e:
        email_sent = False
        print(f"Failed to send email: {e}")

    if email_sent:
        return StandardAPIResponse(success=True, message="verification_email_sent", data=None, metadata=None)
    else:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
@router.post("/verify_signup", response_model=StandardAPIResponse)
def verify_signup(verification_data: VerificationCodeSchema, db: Session = Depends(get_db)):
    """
    Verify a user's signup.
    """
    result = auth_crud.get_verification_data(verification_data.email, db)
    user_role = auth_crud.get_user_role(verification_data.email, db)

    if result['verification_code'] == verification_data.verification_code and result['expiration_time'] > datetime.now():
        print("User created successfully")
        auth_crud.complete_user_registration(verification_data.email, result['password'], result['team'], user_role, db)
        print(f"Successfully completed user registration for {verification_data.email} with role {user_role}")
        return StandardAPIResponse(success=True, message="user_created_successfully", data=None, metadata=None)
    elif result['verification_code'] != verification_data.verification_code:
        return StandardAPIResponse(success=False, message="verification_code_incorrect", data=None, metadata=None)
    elif result['expiration_time'] < datetime.now():       
        return StandardAPIResponse(success=False, message="verification_code_expired", data=None, metadata=None)
    else:
        return StandardAPIResponse(success=False, message="unknown_error_verifying_signup", data=None, metadata=None)

@router.post("/login", response_model=StandardAPIResponse)
def login(login_data: LoginSchema, db: Session = Depends(get_db), jwt_key: str = Depends(get_JWT_key)):
    """
    Login a user.
    """
    # Check if a user exists with the given email
    user_details = auth_crud.fetch_user_details(login_data.email, db)
    if not user_details:
        return StandardAPIResponse(success=False, message="user_not_found", data=None, metadata=None)
    
    email, hashed_password, role = user_details
    if verify_password(login_data.password, hashed_password):
        # If the password is correct, we generate a JWT token and return it to the user (encoded with email, role, and expiration time)
        xpiry_time = datetime.now(timezone.utc) + timedelta(minutes=60)
        token_payload = {"email": email, "role": role, "exp": xpiry_time}
        token = jwt.encode(token_payload, jwt_key, algorithm="HS256")
        auth_crud.update_user_login_time(email, db)
        return StandardAPIResponse(success=True, message="login_successful", data=token, metadata=None)
    else:
        return StandardAPIResponse(success=False, message="incorrect_password", data=None, metadata=None)


@router.post("/request_password_reset", response_model=StandardAPIResponse)
def request_password_reset(email: EmailSchema, db: Session = Depends(get_db), 
                           ses_client: boto3.client = Depends(get_ses_client), 
                           jwt_key: str = Depends(get_JWT_key),
                           frontend_url: str = Depends(get_frontend_url)):
    """
    Request a password reset. Requires a lot of dependencies.
    """
    user_details = auth_crud.fetch_user_details(email.email, db)
    if not user_details:
        return StandardAPIResponse(success=False, message="user_not_found", data=None, metadata=None)
    
    # Generate a secure token
    reset_token = jwt.encode({"email": email.email, "exp": datetime.now(timezone.utc) + timedelta(hours=3)}, jwt_key, algorithm="HS256")
    reset_link = f"{frontend_url}/reset_password?token={reset_token}"
    
    # Send email with reset link
    try:
        aws_email.send_password_reset_email(ses_client, email.email, reset_link)
        email_sent = True
    except Exception as e:
        email_sent = False
        print(f"Failed to send email: {e}")

    if email_sent:
        return StandardAPIResponse(success=True, message="password_reset_email_sent", data=None, metadata=None)
    else:
        raise HTTPException(status_code=500, detail="Failed to send password reset email")


@router.post("/reset_password", response_model=StandardAPIResponse)
def reset_password(token__and_newpassword: NewPasswordSchema, db: Session = Depends(get_db), jwt_key: str = Depends(get_JWT_key)):
    """
    Reset a user's password.
    """
    token = token__and_newpassword.token
    new_password = token__and_newpassword.newpassword

    try: 
        payload = jwt.decode(token, jwt_key, algorithms=["HS256"])
        email = payload["email"]
    except jwt.ExpiredSignatureError:
        return StandardAPIResponse(success=False, message="token_expired", data=None, metadata=None)
    except jwt.InvalidTokenError:
        return StandardAPIResponse(success=False, message="invalid_token", data=None, metadata=None)
    
    hashed_password = hash_password(new_password)
    # Check if the new password is the same as the old password
    user_details = auth_crud.fetch_user_details(email, db)
    old_password = user_details[1]
    if user_details and verify_password(new_password, old_password):
        return StandardAPIResponse(success=False, message="new_password_same_as_old", data=None, metadata=None)

    # Update the user's password in the database, return success
    auth_crud.update_user_password(email, hashed_password, db)
    return StandardAPIResponse(success=True, message="password_reset_successful", data=None, metadata=None)
        