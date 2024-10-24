from pydantic import BaseModel

class PreApprovedEmailInput(BaseModel):
    email: str
    role: str

class PreApprovedEmailDeleteInput(BaseModel):
    email: str


class UpdateUserRoleInput(BaseModel):
    email: str
    old_role: str
    new_role: str

class DeleteUserInput(BaseModel):
    email: str