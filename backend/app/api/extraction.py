"""AI extraction API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import uuid

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, Meeting, Transcript, TranscriptChunk, OrganizationMember, IntelligenceEntity, AIProcessingJob
from app.services.ai_extraction import AIExtractionService
from app.services.execution_continuity import ExecutionContinuityService
from app.services.embedding import EmbeddingService, QdrantMemoryService

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


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


async def extract_and_store_intelligence(
    session: AsyncSession,
    meeting_id: str,
    organization_id: str,
):
    """Background task to extract intelligence and store in DB"""
    try:
        # Get transcript
        result = await session.execute(
            select(Transcript).where(Transcript.meeting_id == meeting_id)
        )
        transcript = result.scalars().first()
        if not transcript:
            return
        
        # Get all chunks
        result = await session.execute(
            select(TranscriptChunk).where(
                TranscriptChunk.meeting_id == meeting_id
            ).order_by(TranscriptChunk.index)
        )
        chunks = result.scalars().all()
        
        # Combine chunks into full transcript text
        transcript_text = " ".join([chunk.text for chunk in chunks])
        
        # Get meeting attendees
        result = await session.execute(
            select(User).where(
                User.id.in_([chunk.speaker_id for chunk in chunks])
            )
        )
        attendees = [user.name or user.email for user in result.scalars().all()]
        
        # Extract intelligence
        extraction_service = AIExtractionService()
        extraction = await extraction_service.extract_from_transcript(
            transcript_text=transcript_text,
            meeting_title=transcript.title or "Untitled Meeting",
            attendees=attendees,
        )
        
        # Store extracted entities
        for decision in extraction.decisions:
            entity = IntelligenceEntity(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                meeting_id=meeting_id,
                entity_type="decision",
                title=decision.title,
                description=decision.description,
                confidence_score=decision.confidence_score,
                meta={"tags": decision.tags},
            )
            session.add(entity)
            
            # Create execution state
            await ExecutionContinuityService.create_execution_state(
                session=session,
                entity_id=entity.id,
                organization_id=organization_id,
            )
        
        for action in extraction.actions:
            entity = IntelligenceEntity(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                meeting_id=meeting_id,
                entity_type="action",
                title=action.title,
                description=action.description,
                assigned_to=action.assigned_to,
                priority=action.priority,
                confidence_score=action.confidence_score,
                meta={"tags": action.tags, "due_date": action.due_date},
            )
            session.add(entity)
            
            # Create execution state
            await ExecutionContinuityService.create_execution_state(
                session=session,
                entity_id=entity.id,
                organization_id=organization_id,
            )
        
        for blocker in extraction.blockers:
            entity = IntelligenceEntity(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                meeting_id=meeting_id,
                entity_type="blocker",
                title=blocker.title,
                description=blocker.description,
                confidence_score=blocker.confidence_score,
                meta={"tags": blocker.tags},
            )
            session.add(entity)
            
            # Create execution state
            await ExecutionContinuityService.create_execution_state(
                session=session,
                entity_id=entity.id,
                organization_id=organization_id,
            )
        
        for topic in extraction.topics:
            entity = IntelligenceEntity(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                meeting_id=meeting_id,
                entity_type="topic",
                title=topic.title,
                description=topic.description,
                confidence_score=topic.confidence_score,
                meta={"tags": topic.tags},
            )
            session.add(entity)
        
        await session.commit()
        
        # Store in vector DB
        qdrant_service = QdrantMemoryService()
        memories = []
        for decision in extraction.decisions:
            memories.append({
                "memory_id": str(uuid.uuid4()),
                "content": decision.description,
                "memory_type": "decision",
                "metadata": {"title": decision.title},
            })
        for action in extraction.actions:
            memories.append({
                "memory_id": str(uuid.uuid4()),
                "content": action.description,
                "memory_type": "action",
                "metadata": {"title": action.title, "assigned_to": action.assigned_to},
            })
        for blocker in extraction.blockers:
            memories.append({
                "memory_id": str(uuid.uuid4()),
                "content": blocker.description,
                "memory_type": "blocker",
                "metadata": {"title": blocker.title},
            })
        
        await qdrant_service.batch_store_memories(memories)
        
    except Exception as e:
        print(f"Error in extract_and_store_intelligence: {e}")


@router.post("/extract-meeting", response_model=Dict[str, Any])
async def extract_from_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract intelligence from a meeting transcript.
    
    Args:
        meeting_id: Meeting ID to extract from
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
        # Add background task to extract intelligence
        background_tasks.add_task(
            extract_and_store_intelligence,
            session,
            meeting_id,
            meeting.organization_id,
        )
        
        return {
            "status": "processing",
            "meeting_id": meeting_id,
            "message": "Intelligence extraction started",
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities", response_model=List[Dict[str, Any]])
async def get_extracted_entities(
    meeting_id: str,
    entity_type: str = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all extracted intelligence entities for a meeting"""
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
        # Get entities
        query = select(IntelligenceEntity).where(
            IntelligenceEntity.meeting_id == meeting_id
        )
        if entity_type:
            query = query.where(IntelligenceEntity.entity_type == entity_type)
        
        result = await session.execute(query)
        entities = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "entity_type": e.entity_type,
                "title": e.title,
                "description": e.description,
                "confidence_score": e.confidence_score,
                "status": e.status,
                "assigned_to": e.assigned_to,
                "due_date": e.due_date.isoformat() if e.due_date else None,
                "priority": e.priority,
            }
            for e in entities
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities-summary", response_model=Dict[str, Any])
async def get_entities_summary(
    meeting_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary of extracted entities"""
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
        # Get counts by type
        result = await session.execute(
            select(IntelligenceEntity.entity_type).where(
                IntelligenceEntity.meeting_id == meeting_id
            )
        )
        entity_types = result.scalars().all()
        
        type_counts = {}
        for etype in entity_types:
            type_counts[etype] = type_counts.get(etype, 0) + 1
        
        return {
            "meeting_id": meeting_id,
            "total_entities": len(entity_types),
            "by_type": type_counts,
            "decisions": type_counts.get("decision", 0),
            "actions": type_counts.get("action", 0),
            "blockers": type_counts.get("blocker", 0),
            "topics": type_counts.get("topic", 0),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
