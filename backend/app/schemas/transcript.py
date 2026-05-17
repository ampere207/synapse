"""Transcript schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TranscriptCreate(BaseModel):
    """Schema for creating a transcript"""
    source: str
    full_text: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Schema for transcript response"""
    id: str
    meeting_id: str
    organization_id: str
    source: str
    status: str
    full_text: Optional[str]
    token_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranscriptChunkCreate(BaseModel):
    """Schema for creating a transcript chunk"""
    speaker: Optional[str] = None
    text: str
    timestamp: Optional[int] = None


class TranscriptChunkResponse(BaseModel):
    """Schema for transcript chunk response"""
    id: str
    transcript_id: str
    organization_id: str
    sequence_number: int
    speaker: Optional[str]
    text: str
    timestamp: Optional[int]
    token_count: int
    created_at: datetime

    class Config:
        from_attributes = True
