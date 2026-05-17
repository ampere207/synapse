"""Organization schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.organization import RoleEnum


class OrganizationCreate(BaseModel):
    """Schema for creating an organization"""
    name: str
    slug: str
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Schema for organization response"""
    id: str
    name: str
    slug: str
    description: Optional[str]
    owner_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member response"""
    id: str
    organization_id: str
    user_id: str
    role: RoleEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
