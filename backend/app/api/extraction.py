"""AI extraction API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
import re
from pydantic import BaseModel

from app.core.database import get_db, AsyncSessionLocal
from app.core.security import decode_token
from app.models import User, Meeting, Transcript, TranscriptChunk, OrganizationMember, IntelligenceEntity
from app.services.ai_extraction import AIExtractionService
from app.services.execution_continuity import ExecutionContinuityService
from app.services.embedding import EmbeddingService, QdrantMemoryService
from app.services.transcript import TranscriptService
from app.graph_engine import GraphMutationService
from app.graph_engine.schemas import GraphNodePayload, GraphEdgePayload
from app.models.graph import NodeTypeEnum

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


class TranscriptImportRequest(BaseModel):
    meeting_id: str
    transcript_text: str
    source: str = "upload"
    title: Optional[str] = None


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


def _parse_transcript_chunks(transcript_text: str) -> list[dict[str, Any]]:
    """Parse loose transcript text into speaker turns."""
    chunks: list[dict[str, Any]] = []
    sequence_number = 0
    current_timestamp: Optional[int] = None
    current_speaker: Optional[str] = None
    current_lines: list[str] = []

    timestamp_only_pattern = re.compile(r"^\[(\d{2}):(\d{2})(?::(\d{2}))?\]\s*$")
    timestamp_inline_pattern = re.compile(r"^\[(\d{2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$")
    speaker_pattern = re.compile(r"^([A-Za-z0-9 .,'\-_()]+):\s*(.*)$")

    def flush_chunk() -> None:
        nonlocal sequence_number, current_speaker, current_lines, current_timestamp
        text = " ".join(line.strip() for line in current_lines if line.strip()).strip()
        if not text and not current_speaker:
            current_lines = []
            return

        chunks.append(
            {
                "speaker": current_speaker or "Unknown",
                "text": text,
                "timestamp": current_timestamp,
                "sequence_number": sequence_number,
            }
        )
        sequence_number += 1
        current_lines = []
        current_speaker = None
        current_timestamp = None

    for raw_line in transcript_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        inline_timestamp = timestamp_inline_pattern.match(line)
        if inline_timestamp:
            flush_chunk()
            hours = int(inline_timestamp.group(1))
            minutes = int(inline_timestamp.group(2))
            seconds = int(inline_timestamp.group(3) or 0)
            current_timestamp = hours * 3600 + minutes * 60 + seconds
            remainder = inline_timestamp.group(4).strip()
            if remainder:
                speaker_match = speaker_pattern.match(remainder)
                if speaker_match:
                    current_speaker = speaker_match.group(1).strip()
                    current_lines = [speaker_match.group(2).strip()] if speaker_match.group(2).strip() else []
                else:
                    current_speaker = current_speaker or "Unknown"
                    current_lines = [remainder]
            continue

        timestamp_only = timestamp_only_pattern.match(line)
        if timestamp_only:
            flush_chunk()
            hours = int(timestamp_only.group(1))
            minutes = int(timestamp_only.group(2))
            seconds = int(timestamp_only.group(3) or 0)
            current_timestamp = hours * 3600 + minutes * 60 + seconds
            continue

        speaker_match = speaker_pattern.match(line)
        if speaker_match:
            if current_lines or current_speaker:
                flush_chunk()
            current_speaker = speaker_match.group(1).strip()
            first_text = speaker_match.group(2).strip()
            current_lines = [first_text] if first_text else []
            continue

        if current_speaker:
            current_lines.append(line)

    flush_chunk()
    return chunks


async def _run_extraction_job(meeting_id: str, organization_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await extract_and_store_intelligence(session, meeting_id, organization_id)


async def _resolve_assignee_user_id(
    session: AsyncSession,
    organization_id: str,
    candidate: Optional[str],
) -> Optional[str]:
    """Resolve a human-readable assignee to a user ID when possible."""
    if not candidate:
        return None

    normalized = candidate.strip().lower()
    with session.no_autoflush:
        result = await session.execute(
            select(User).where(
                (User.username.ilike(normalized))
                | (User.full_name.ilike(normalized))
                | (User.email.ilike(normalized))
            )
        )
        user = result.scalars().first()
        if user:
            return user.id

        # Try a looser match on the organization's members.
        result = await session.execute(
            select(User).join(OrganizationMember, OrganizationMember.user_id == User.id).where(
                (OrganizationMember.organization_id == organization_id)
                & (
                    User.username.ilike(f"%{normalized}%")
                    | User.full_name.ilike(f"%{normalized}%")
                    | User.email.ilike(f"%{normalized}%")
                )
            )
        )
        user = result.scalars().first()
        return user.id if user else None


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

        meeting = await session.get(Meeting, meeting_id)
        meeting_title = meeting.title if meeting else "Untitled Meeting"
        
        # Get all chunks
        result = await session.execute(
            select(TranscriptChunk).where(
                TranscriptChunk.transcript_id == transcript.id
            ).order_by(TranscriptChunk.sequence_number)
        )
        chunks = result.scalars().all()
        
        # Combine chunks into full transcript text
        transcript_text = transcript.full_text or " ".join([chunk.text for chunk in chunks])
        
        # Get meeting attendees
        attendees = []
        seen_attendees = set()
        for chunk in chunks:
            speaker = (chunk.speaker or "").strip()
            if speaker and speaker.lower() not in seen_attendees:
                seen_attendees.add(speaker.lower())
                attendees.append(speaker)
        
        # Extract intelligence
        extraction_service = AIExtractionService()
        extraction = await extraction_service.extract_from_transcript(
            transcript_text=transcript_text,
            meeting_title=meeting_title,
            attendees=attendees,
        )

        if not any([extraction.decisions, extraction.actions, extraction.blockers, extraction.topics]):
            extraction = extraction_service._heuristic_extract(
                transcript_text=transcript_text,
                meeting_title=meeting_title,
                attendees=attendees,
            )

        root_description = extraction.meeting_summary or transcript_text[:240].strip() or meeting_title
        root_node, _ = await GraphMutationService.create_node(
            session=session,
            meeting_id=meeting_id,
            organization_id=organization_id,
            node=GraphNodePayload(
                id=str(uuid.uuid4()),
                type=NodeTypeEnum.TOPIC.value,
                label=meeting_title,
                description=root_description,
                metadata={
                    "entity_type": "meeting_root",
                    "confidence_score": 1.0,
                    "source_speaker": None,
                    "source_timestamp": None,
                },
                source_entity_id=None,
            ),
        )
        
        # Store extracted entities
        created_entities: list[IntelligenceEntity] = []
        graph_nodes_by_type: dict[str, list[Any]] = {
            "topic": [],
            "blocker": [],
            "decision": [],
            "action": [],
        }
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
            created_entities.append(entity)
            await session.flush()
            
            # Create execution state
            await ExecutionContinuityService.create_execution_state(
                session=session,
                entity_id=entity.id,
                organization_id=organization_id,
            )
            graph_node, _ = await GraphMutationService.create_node(
                session=session,
                meeting_id=meeting_id,
                organization_id=organization_id,
                node=GraphNodePayload(
                    id=str(uuid.uuid4()),
                    type=NodeTypeEnum.DECISION.value,
                    label=decision.title,
                    description=decision.description,
                    metadata={
                        "entity_type": "decision",
                        "confidence_score": decision.confidence_score,
                        "source_speaker": None,
                        "source_timestamp": None,
                    },
                    source_entity_id=entity.id,
                ),
            )
            graph_nodes_by_type["decision"].append(graph_node)
        
        for action in extraction.actions:
            assigned_to = await _resolve_assignee_user_id(session, organization_id, action.assigned_to)
            entity = IntelligenceEntity(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                meeting_id=meeting_id,
                entity_type="action",
                title=action.title,
                description=action.description,
                assigned_to=assigned_to,
                priority=action.priority,
                confidence_score=action.confidence_score,
                meta={"tags": action.tags, "due_date": action.due_date, "assigned_to_name": action.assigned_to},
            )
            session.add(entity)
            created_entities.append(entity)
            await session.flush()
            
            # Create execution state
            await ExecutionContinuityService.create_execution_state(
                session=session,
                entity_id=entity.id,
                organization_id=organization_id,
            )
            graph_node, _ = await GraphMutationService.create_node(
                session=session,
                meeting_id=meeting_id,
                organization_id=organization_id,
                node=GraphNodePayload(
                    id=str(uuid.uuid4()),
                    type=NodeTypeEnum.ACTION.value,
                    label=action.title,
                    description=action.description,
                    metadata={
                        "entity_type": "action",
                        "confidence_score": action.confidence_score,
                        "source_speaker": None,
                        "source_timestamp": None,
                    },
                    source_entity_id=entity.id,
                ),
            )
            graph_nodes_by_type["action"].append(graph_node)
        
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
            created_entities.append(entity)
            await session.flush()
            
            # Create execution state
            await ExecutionContinuityService.create_execution_state(
                session=session,
                entity_id=entity.id,
                organization_id=organization_id,
            )
            graph_node, _ = await GraphMutationService.create_node(
                session=session,
                meeting_id=meeting_id,
                organization_id=organization_id,
                node=GraphNodePayload(
                    id=str(uuid.uuid4()),
                    type=NodeTypeEnum.TOPIC.value,
                    label=blocker.title,
                    description=blocker.description,
                    metadata={
                        "entity_type": "blocker",
                        "confidence_score": blocker.confidence_score,
                        "source_speaker": None,
                        "source_timestamp": None,
                    },
                    source_entity_id=entity.id,
                ),
            )
            graph_nodes_by_type["blocker"].append(graph_node)
        
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
            created_entities.append(entity)
            await session.flush()
            graph_node, _ = await GraphMutationService.create_node(
                session=session,
                meeting_id=meeting_id,
                organization_id=organization_id,
                node=GraphNodePayload(
                    id=str(uuid.uuid4()),
                    type=NodeTypeEnum.TOPIC.value,
                    label=topic.title,
                    description=topic.description,
                    metadata={
                        "entity_type": "topic",
                        "confidence_score": topic.confidence_score,
                        "source_speaker": None,
                        "source_timestamp": None,
                    },
                    source_entity_id=entity.id,
                ),
            )
            graph_nodes_by_type["topic"].append(graph_node)

        await session.flush()

        phase_order = ["topic", "blocker", "decision", "action"]
        phase_edges = {
            ("root", "topic"): "agenda",
            ("root", "blocker"): "agenda",
            ("root", "decision"): "agenda",
            ("root", "action"): "agenda",
            ("topic", "blocker"): "surfaces_issue",
            ("blocker", "decision"): "drives_decision",
            ("decision", "action"): "creates_action",
            ("topic", "decision"): "supports_decision",
            ("topic", "action"): "informs_action",
            ("blocker", "action"): "needs_follow_up",
        }

        previous_node = root_node
        previous_phase = "root"
        for phase in phase_order:
            phase_nodes = graph_nodes_by_type.get(phase, [])
            if not phase_nodes:
                continue

            await GraphMutationService.create_edge(
                session=session,
                meeting_id=meeting_id,
                organization_id=organization_id,
                edge=GraphEdgePayload(
                    id=str(uuid.uuid4()),
                    source_node_id=previous_node.id,
                    target_node_id=phase_nodes[0].id,
                    relationship_type=phase_edges.get((previous_phase, phase), "leads_to"),
                    weight="high",
                    metadata={"phase": phase},
                ),
            )

            for index in range(len(phase_nodes) - 1):
                await GraphMutationService.create_edge(
                    session=session,
                    meeting_id=meeting_id,
                    organization_id=organization_id,
                    edge=GraphEdgePayload(
                        id=str(uuid.uuid4()),
                        source_node_id=phase_nodes[index].id,
                        target_node_id=phase_nodes[index + 1].id,
                        relationship_type="continues",
                        weight="medium",
                        metadata={"phase": phase},
                    ),
                )

            previous_node = phase_nodes[-1]
            previous_phase = phase
        
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


@router.post("/import-transcript", response_model=Dict[str, Any])
async def import_transcript(
    payload: TranscriptImportRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist an uploaded transcript and queue intelligence extraction."""
    meeting = await session.get(Meeting, payload.meeting_id)
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

    transcript = await TranscriptService.create_transcript(
        db=session,
        meeting_id=payload.meeting_id,
        organization_id=meeting.organization_id,
        source=payload.source,
        full_text=payload.transcript_text,
    )

    chunks = _parse_transcript_chunks(payload.transcript_text)
    if not chunks:
        chunks = [
            {
                "speaker": None,
                "text": payload.transcript_text.strip(),
                "timestamp": None,
                "sequence_number": 0,
            }
        ]

    for chunk in chunks:
        await TranscriptService.add_transcript_chunk(
            db=session,
            transcript_id=transcript.id,
            organization_id=meeting.organization_id,
            speaker=chunk["speaker"],
            text=chunk["text"],
            timestamp=chunk["timestamp"],
            sequence_number=chunk["sequence_number"],
        )

    transcript.status = "completed"
    await session.commit()

    background_tasks.add_task(_run_extraction_job, payload.meeting_id, meeting.organization_id)

    return {
        "status": "processing",
        "meeting_id": payload.meeting_id,
        "transcript_id": transcript.id,
        "chunk_count": len(chunks),
        "message": "Transcript imported and extraction queued",
    }


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
