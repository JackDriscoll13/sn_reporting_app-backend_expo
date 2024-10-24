
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

#Schemas 
from models.useradmin_schemas import PreApprovedEmailInput, PreApprovedEmailDeleteInput, UpdateUserRoleInput, DeleteUserInput

# Models
from models.api_responses import StandardAPIResponse

# Dependencies
from dependencies import get_db

# Crud
from crud import useradmin_crud


router = APIRouter()


@router.get("/get_current_users")
def get_current_users(db: Session = Depends(get_db)):
    users = useradmin_crud.get_current_active_users(db)
    return StandardAPIResponse(success=True, message="users_retrieved_successfully", data=users, metadata=None)

@router.post("/update_user_role")
def update_user_role(input: UpdateUserRoleInput, db: Session = Depends(get_db)):
    if useradmin_crud.update_user_role(input.email, input.old_role, input.new_role, db):
        return StandardAPIResponse(success=True, message="user_role_updated_successfully", data=None, metadata=None)
    else:
        raise HTTPException(status_code=400, detail="Failed to update user role")


@router.post("/delete_user")
def delete_user(input: DeleteUserInput, db: Session = Depends(get_db)):
    if useradmin_crud.delete_user(input.email, db):
        return StandardAPIResponse(success=True, message="user_deleted_successfully", data=None, metadata=None)
    else:
        raise HTTPException(status_code=400, detail="Failed to delete user")

# Pre Approved Emails Table
@router.get("/get_pre_approved_emails")
def get_pre_approved_emails(db: Session = Depends(get_db)):
    emails = useradmin_crud.get_pre_approved_emails(db)
    return StandardAPIResponse(success=True, message="emails_retrieved_successfully", data=emails, metadata=None)

@router.post("/add_pre_approved_email")
def create_pre_approved_email(input: PreApprovedEmailInput, db: Session = Depends(get_db)):
    date_approved = date.today()
    if useradmin_crud.add_pre_approved_email(input.email, input.role, date_approved, db)["success"]:   
        return StandardAPIResponse(success=True, message="email_added_successfully", data=None, metadata=None)
    else:
        raise HTTPException(status_code=400, detail="Email already exists in pre-approved list")
    
@router.post("/delete_pre_approved_email")
def delete_pre_approved_email(input: PreApprovedEmailDeleteInput, db: Session = Depends(get_db)):
    if useradmin_crud.delete_pre_approved_email(input.email, db):   
        return StandardAPIResponse(success=True, message="email_deleted_successfully", data=None, metadata=None)
    else:
        raise HTTPException(status_code=400, detail="Email not found in pre-approved list")
    


