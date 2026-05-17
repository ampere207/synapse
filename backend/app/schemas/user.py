"""User schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
