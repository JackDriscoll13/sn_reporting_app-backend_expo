from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional, List
from datetime import datetime


# Check if an email is in the preapproved emails table
def get_email_preapproved(email: str, db: Session) -> bool:
    """
    Check if an email is in the preapproved emails table.
    """
    result = db.execute(
        text(
            "SELECT email FROM users_and_admin.pre_approved_emails WHERE email = :email"
        ),
        {"email": email}
    )
    return result.fetchone() is not None

# Check if an email is already in use
def get_email_is_existing(email: str, db: Session) -> bool:
    """
    Check if an email is already in use.
    """
    result = db.execute(
        text(
            "SELECT email FROM users_and_admin.users WHERE email = :email"
        ),
        {"email": email}
    )
    return result.fetchone() is not None

def update_user_verification_code(email: str, team: str, 
                                  hashed_pw: str, verification_code: str,
                                  expiry_time: datetime, db: Session):
    """
    Add the user's verification code and expiry time.
    Adds details to the verify_users table.



    :param email: The email address of the user.
    :param team: The team of the user.
    :param hashed_pw: The hashed password of the user.
    :param verification_code: The verification code of the user.
    :param expiry_time: The expiry time of the verification code.
    :param db: The database session.
    """
    query = text("""
    INSERT INTO users_and_admin.verify_users (email, password, team, verif_code, expiration_time) 
    VALUES (:email, :password, :team, :verif_code, :expiration_time)
    ON CONFLICT (email) 
    DO UPDATE SET verif_code = :verif_code, expiration_time = :expiration_time
    """)
    
    params = {
        "email": email,
        "password": hashed_pw,
        "team": team,
        "verif_code": verification_code,
        "expiration_time": expiry_time
    }
    
    db.execute(query, params)
    db.commit()
    print(f"Verification code for user {email} updated successfully.")

def refresh_verification_code(email: str, verification_code: str, expiry_time: datetime, db: Session):
    """
    Refresh the verification code for a specific user. 
    This function will update the verification code and expiry time for a specific user.

    """
    #We insert the email, verification code and time stamp into the verification table, we ensure it replaces any existing values with the same email.
    query = text("""
        INSERT INTO users_and_admin.verify_users (email, verif_code, expiration_time) 
        VALUES (:email, :verif_code, :expiration_time)
        ON CONFLICT (email) 
        DO UPDATE SET verif_code = :verif_code, expiration_time = :expiration_time
    """)
    
    params = {
        "email": email,
        "verif_code": verification_code,
        "expiration_time": expiry_time
    }
    
    db.execute(query, params)
    db.commit()

def get_verification_data(email: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get the verification data for a specific user.
    """
    query = text("""
        SELECT email, password, team, verif_code, expiration_time 
        FROM users_and_admin.verify_users 
        WHERE email = :email
    """)
    dataemail, password, team,  v_code, exp_time = db.execute(query, {"email": email}).fetchone()
    
    if dataemail:
        return {
            "email": dataemail,
            "password": password,
            "team": team,
            "verification_code": str(v_code),
            "expiration_time": exp_time
        }
    return None 

def complete_user_registration(email: str, password: str, team: str, role: str, db: Session):
        """
        Add a user to the database.
        """
        # If the verification code is correct and hasn't expired, we insert the user into the users table
        db.execute(text("""
        INSERT INTO users_and_admin.users (email, password, team, role) 
        VALUES (:email, :password, :team, :role)"""), 
        {"email": email, "password": password, "team": team, "role": role})
        db.commit()
        # We also delete the user from the verify_users table
        db.execute(text("""DELETE FROM users_and_admin.verify_users WHERE email = :email"""), {"email": email})
        db.commit()

def fetch_user_details(email: str, db: Session):
     """
     Fetch the user details from the database.
     """
     query = text("""
     SELECT email, password, role FROM users_and_admin.users WHERE email = :email
     """)
     result = db.execute(query, {"email": email}).fetchone()
     return result

def update_user_password(email: str, new_password: str, db: Session):
    """
    Update the user's password in the database.
    """
    query = text("""
    UPDATE users_and_admin.users SET password = :new_password WHERE email = :email
    """)
    db.execute(query, {"email": email, "new_password": new_password})
    db.commit()
    
    
# Perhaps bandaid solution, but I think an effective way to handle role assignment is to just pull
# the role from the pre_approved_emails table when we complete the signup process. 
# Its' either this or we have to transfer role to the verify_users table and then to the users table, which seems unnecessary.

def get_user_role(email: str, db: Session):
    """
    Get the role of a user.
    """
    query = text("""
    SELECT role FROM users_and_admin.pre_approved_emails WHERE email = :email""")
    result = db.execute(query, {"email": email}).fetchone()
    return result[0] if result else None


def update_user_login_time(email: str, db: Session):
    """
    Update the user's last login time in the database.
    """
    query = text("""
    UPDATE users_and_admin.users SET last_login_time = NOW() WHERE email = :email
    """)
    db.execute(query, {"email": email})
    db.commit()
