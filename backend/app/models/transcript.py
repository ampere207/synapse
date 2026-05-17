"""Transcript and transcript chunk models"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Transcript(Base):
    """Transcript model"""
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # "live_stream", "upload", "zoom_export", etc.
    status = Column(String(50), default="processing", nullable=False, index=True)
    full_text = Column(Text, nullable=True)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TranscriptChunk(Base):
    """Individual transcript chunk for streaming"""
    __tablename__ = "transcript_chunks"

    id = Column(String(36), primary_key=True, index=True)
    transcript_id = Column(String(36), ForeignKey("transcripts.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    speaker = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=True)  # seconds from start
    token_count = Column(Integer, default=0)
    meta = Column('metadata_json', JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
