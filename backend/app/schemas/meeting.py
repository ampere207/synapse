"""Meeting schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.meeting import MeetingStatusEnum


class MeetingCreate(BaseModel):
    """Schema for creating a meeting"""
    title: str
    description: Optional[str] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MeetingStatusEnum] = None


class MeetingResponse(BaseModel):
    """Schema for meeting response"""
    id: str
    organization_id: str
    created_by: str
    title: str
    description: Optional[str]
    status: MeetingStatusEnum
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
