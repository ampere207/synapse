"""AI processing job model for async queue"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class JobStatusEnum(str, enum.Enum):
    """AI job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobTypeEnum(str, enum.Enum):
    """AI job type"""
    SUMMARIZE_CHUNK = "summarize_chunk"
    EXTRACT_DECISIONS = "extract_decisions"
    EXTRACT_ACTIONS = "extract_actions"
    BUILD_GRAPH = "build_graph"
    PROCESS_BATCH = "process_batch"


class AIProcessingJob(Base):
    """AI processing job model"""
    __tablename__ = "ai_processing_jobs"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    transcript_id = Column(String(36), ForeignKey("transcripts.id"), nullable=True)
    job_type = Column(Enum(JobTypeEnum), nullable=False, index=True)
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.PENDING, nullable=False, index=True)
    priority = Column(String(50), default="medium")  # "low", "medium", "high"
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(3), default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
