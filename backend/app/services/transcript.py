"""Transcript service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.models.transcript import Transcript, TranscriptChunk
from app.models.ai_job import AIProcessingJob, JobTypeEnum, JobStatusEnum


class TranscriptService:
    """Service for transcript management"""
    
    @staticmethod
    async def create_transcript(
        db: AsyncSession,
        meeting_id: str,
        organization_id: str,
        source: str,
        full_text: str = None
    ) -> Transcript:
        """Create a new transcript"""
        transcript_id = str(uuid.uuid4())
        transcript = Transcript(
            id=transcript_id,
            meeting_id=meeting_id,
            organization_id=organization_id,
            source=source,
            full_text=full_text,
            status="processing" if full_text else "waiting",
        )
        db.add(transcript)
        await db.commit()
        await db.refresh(transcript)
        return transcript
    
    @staticmethod
    async def add_transcript_chunk(
        db: AsyncSession,
        transcript_id: str,
        organization_id: str,
        speaker: str,
        text: str,
        timestamp: int = None,
        sequence_number: int = 0,
    ) -> TranscriptChunk:
        """Add a chunk to transcript"""
        chunk_id = str(uuid.uuid4())
        chunk = TranscriptChunk(
            id=chunk_id,
            transcript_id=transcript_id,
            organization_id=organization_id,
            sequence_number=sequence_number,
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            token_count=len(text.split()),  # Simple approximation
        )
        db.add(chunk)
        await db.commit()
        await db.refresh(chunk)
        return chunk
    
    @staticmethod
    async def get_transcript_chunks(
        db: AsyncSession,
        transcript_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[TranscriptChunk]:
        """Get transcript chunks"""
        stmt = select(TranscriptChunk).where(
            TranscriptChunk.transcript_id == transcript_id
        ).order_by(TranscriptChunk.sequence_number).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return result.scalars().all()
