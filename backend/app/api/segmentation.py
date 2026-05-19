"""Semantic segmentation API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, Meeting, Transcript, TranscriptChunk, OrganizationMember
from app.services.semantic_segmentation import SemanticSegmentationService

router = APIRouter(prefix="/api/segmentation", tags=["segmentation"])


async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@router.post("/segment-transcript", response_model=Dict[str, Any])
async def segment_transcript(
    meeting_id: str,
    transition_threshold: float = 0.6,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Segment a meeting transcript into topic clusters.
    
    Args:
        meeting_id: Meeting ID to segment
        transition_threshold: Threshold for topic transitions (0-1)
    """
    # Verify access
    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get all transcript chunks for this meeting
        transcript_result = await session.execute(
            select(Transcript).where(Transcript.meeting_id == meeting_id)
        )
        transcript = transcript_result.scalars().first()
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript found")

        result = await session.execute(
            select(TranscriptChunk).where(
                TranscriptChunk.transcript_id == transcript.id
            ).order_by(TranscriptChunk.sequence_number)
        )
        chunks = result.scalars().all()
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No transcript chunks found")
        
        # Convert to segment format
        chunk_data = [
            {
                "text": chunk.text,
                "speaker": chunk.speaker,
                "timestamp": chunk.timestamp,
                "index": chunk.sequence_number,
            }
            for chunk in chunks
        ]
        
        # Perform segmentation
        segments = await SemanticSegmentationService.segment_transcript(
            chunk_data,
            transition_threshold=transition_threshold,
        )
        
        # Group similar segments
        grouped = SemanticSegmentationService.group_similar_segments(segments)
        
        # Format response
        response_segments = []
        for item in grouped:
            segment = item["segment"]
            summary = SemanticSegmentationService.summarize_segment(segment)
            
            response_segments.append({
                "topic_id": segment["topic_id"],
                "cluster_id": item["cluster_id"],
                "start_chunk": segment["start_index"],
                "end_chunk": segment["end_index"],
                "summary": summary,
                "keywords": segment["keywords"],
                "speakers": segment["speakers"],
                "chunk_count": len(segment["chunks"]),
            })
        
        return {
            "meeting_id": meeting_id,
            "total_segments": len(response_segments),
            "segments": response_segments,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segment-metadata", response_model=Dict[str, Any])
async def get_segment_metadata(
    meeting_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get metadata about segmentation for a meeting"""
    # Verify access
    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get chunk statistics
        transcript_result = await session.execute(
            select(Transcript).where(Transcript.meeting_id == meeting_id)
        )
        transcript = transcript_result.scalars().first()
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript found")

        result = await session.execute(
            select(TranscriptChunk).where(
                TranscriptChunk.transcript_id == transcript.id
            )
        )
        chunks = result.scalars().all()
        
        # Calculate statistics
        unique_speakers = set(chunk.speaker for chunk in chunks)
        total_words = sum(len(chunk.text.split()) for chunk in chunks)
        
        return {
            "meeting_id": meeting_id,
            "total_chunks": len(chunks),
            "total_words": total_words,
            "unique_speakers": len(unique_speakers),
            "speakers": list(unique_speakers),
            "avg_chunk_length": total_words / len(chunks) if chunks else 0,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
