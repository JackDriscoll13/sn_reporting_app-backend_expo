from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
import pytz


# These query the same tables as the auth_crud functions, but are different as they are used for the user admin page

def get_current_active_users(db: Session):
    """
    Get all current active users.
    """
    result = db.execute(text("SELECT * FROM users_and_admin.users"))
    # Convert the result to a list of dictionaries
    current_users = [dict(row._mapping) for row in result]
    for user in current_users:
        if user['last_login_time']:
            # Convert to EST
            est = pytz.timezone('US/Eastern')
            user['last_login_time'] = user['last_login_time'].replace(tzinfo=pytz.UTC).astimezone(est).strftime('%Y-%m-%d %H:%M:%S %Z')
        else:
            user['last_login_time'] = None

    return current_users

def update_user_role(email: str, old_role: str, new_role: str, db: Session) -> bool:
    """
    Update the role of a user.
    """
    db.execute(text("UPDATE users_and_admin.users SET role = :new_role WHERE email = :email AND role = :old_role"), {"email": email, "old_role": old_role, "new_role": new_role})
    db.commit()
    return True

def delete_user(email: str, db: Session) -> bool:
    """
    Delete a user from the database.
    """
    db.execute(text("DELETE FROM users_and_admin.users WHERE email = :email"), {"email": email})
    db.commit()
    return True





# Pre Approved Emails Table
def get_pre_approved_emails(db: Session):
    """
    Get all pre-approved emails.
    """
    result = db.execute(text("SELECT * FROM users_and_admin.pre_approved_emails"))
    return [dict(row._mapping) for row in result]

def add_pre_approved_email(email: str, role: str, date_approved: date, db: Session) -> Dict[str, Any]:
    """
    Add a pre-approved email to the database or update if it already exists.
    Returns a dictionary with 'success' status and 'message' explaining the result.
    """
    try:
        result = db.execute(
            text("""
            INSERT INTO users_and_admin.pre_approved_emails (email, role, date_approved)
            VALUES (:email, :role, CURRENT_DATE)
            ON CONFLICT (email) DO UPDATE
            SET role = :role, date_approved = :date_approved
            RETURNING *
            """),
            {"email": email, "role": role, "date_approved": date_approved}
        )
        db.commit()
        updated_row = result.fetchone()
        if updated_row:
            return {
                "success": True,
                "message": "Pre-approved email added or updated successfully",
                "data": dict(updated_row._mapping)
            }
        else:
            return {
                "success": False,
                "message": "Failed to add or update pre-approved email"
            }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }
    
def delete_pre_approved_email(email: str, db: Session) -> Dict[str, Any]:
    """
    Delete a pre-approved email from the database.
    """
    db.execute(text("DELETE FROM users_and_admin.pre_approved_emails WHERE email = :email"), {"email": email})
    db.commit()
    return True