"""Phase 3 intelligence discovery API endpoints."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models import (
    User,
    Meeting,
    OrganizationMember,
    IntelligenceEntity,
    ExecutionState,
    SemanticMemory,
    GraphNode,
    GraphEdge,
    GraphMutation,
)
from app.services.embedding import QdrantMemoryService

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _terms(query: str) -> List[str]:
    return [term for term in re.findall(r"[a-zA-Z0-9_]+", query.lower()) if len(term) > 2]


def _lexical_score(text: str, query: str) -> float:
    normalized_text = text.lower()
    terms = _terms(query)
    if not terms:
        return 0.0
    hits = sum(1 for term in terms if term in normalized_text)
    return hits / len(terms)


def _dedupe_ranked(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    best: Dict[str, Dict[str, Any]] = {}
    for item in sorted(items, key=lambda entry: entry.get("score", 0.0), reverse=True):
        key = f"{item.get('kind')}::{item.get('id')}"
        if key not in best:
            best[key] = item
    ranked = sorted(best.values(), key=lambda entry: entry.get("score", 0.0), reverse=True)
    return ranked[:limit]


@router.get("/search", response_model=Dict[str, Any])
async def search_intelligence(
    organization_id: str,
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    meeting_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search meetings, decisions, blockers, actions, topics, and semantic memories."""
    membership = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == organization_id)
            & (OrganizationMember.user_id == current_user.id)
            & (OrganizationMember.is_active.is_(True))
        )
    )
    if not membership.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    filters = [IntelligenceEntity.organization_id == organization_id]
    if meeting_id:
        filters.append(IntelligenceEntity.meeting_id == meeting_id)

    entity_result = await session.execute(
        select(IntelligenceEntity, Meeting.title)
        .join(Meeting, Meeting.id == IntelligenceEntity.meeting_id)
        .where(*filters)
    )

    ranked: List[Dict[str, Any]] = []
    for entity, meeting_title in entity_result.all():
        score = max(
            _lexical_score(entity.title, query),
            _lexical_score(entity.description or "", query),
        )
        score += min(0.2, (entity.confidence_score or 0.0) * 0.2)
        if score > 0:
            ranked.append(
                {
                    "kind": "entity",
                    "id": entity.id,
                    "entity_type": entity.entity_type.value if hasattr(entity.entity_type, "value") else entity.entity_type,
                    "title": entity.title,
                    "description": entity.description,
                    "meeting_id": entity.meeting_id,
                    "meeting_title": meeting_title,
                    "status": entity.status,
                    "score": round(score, 4),
                }
            )

    meeting_result = await session.execute(
        select(Meeting).where(Meeting.organization_id == organization_id)
        .where(Meeting.title.ilike(f"%{query}%") | Meeting.description.ilike(f"%{query}%"))
    )
    for meeting in meeting_result.scalars().all():
        ranked.append(
            {
                "kind": "meeting",
                "id": meeting.id,
                "title": meeting.title,
                "description": meeting.description,
                "meeting_id": meeting.id,
                "meeting_title": meeting.title,
                "score": round(0.8 + _lexical_score(f"{meeting.title} {meeting.description or ''}", query) * 0.2, 4),
            }
        )

    memory_result = await session.execute(
        select(SemanticMemory, Meeting.title)
        .outerjoin(Meeting, Meeting.id == SemanticMemory.meeting_id)
        .where(SemanticMemory.organization_id == organization_id)
    )
    for memory, meeting_title in memory_result.all():
        score = _lexical_score(memory.content, query)
        if score > 0:
            ranked.append(
                {
                    "kind": "memory",
                    "id": memory.id,
                    "memory_type": memory.memory_type,
                    "title": (memory.keywords or [memory.memory_type])[0] if memory.keywords else memory.memory_type,
                    "description": memory.content[:240],
                    "meeting_id": memory.meeting_id,
                    "meeting_title": meeting_title,
                    "score": round(score, 4),
                }
            )

    qdrant_service = QdrantMemoryService()
    qdrant_results = await qdrant_service.search_similar(query, limit=limit * 2)
    for result in qdrant_results:
        payload = result.get("payload") or {}
        ranked.append(
            {
                "kind": "semantic_memory",
                "id": str(result.get("id")),
                "title": payload.get("title") or payload.get("memory_type") or "Semantic memory",
                "description": payload.get("content") or payload.get("description") or "",
                "meeting_id": payload.get("meeting_id"),
                "meeting_title": payload.get("meeting_title"),
                "score": round(float(result.get("score") or 0.0), 4),
            }
        )

    ranked = _dedupe_ranked(ranked, limit)
    return {"query": query, "results": ranked, "total": len(ranked)}


@router.get("/timeline", response_model=Dict[str, Any])
async def intelligence_timeline(
    organization_id: str,
    meeting_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a merged timeline of decisions, actions, blockers, executions, and graph mutations."""
    membership = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == organization_id)
            & (OrganizationMember.user_id == current_user.id)
            & (OrganizationMember.is_active.is_(True))
        )
    )
    if not membership.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    timeline: List[Dict[str, Any]] = []

    entity_filters = [IntelligenceEntity.organization_id == organization_id]
    if meeting_id:
        entity_filters.append(IntelligenceEntity.meeting_id == meeting_id)

    entity_result = await session.execute(select(IntelligenceEntity).where(*entity_filters))
    for entity in entity_result.scalars().all():
        timeline.append(
            {
                "id": entity.id,
                "event_type": f"entity_{entity.entity_type.value if hasattr(entity.entity_type, 'value') else entity.entity_type}",
                "title": entity.title,
                "description": entity.description,
                "meeting_id": entity.meeting_id,
                "entity_id": entity.id,
                "timestamp": entity.updated_at.isoformat() if entity.updated_at else entity.created_at.isoformat(),
                "status": entity.status,
                "score": entity.confidence_score or 0,
            }
        )

    exec_result = await session.execute(select(ExecutionState).where(ExecutionState.organization_id == organization_id))
    for execution in exec_result.scalars().all():
        if meeting_id:
            entity = await session.get(IntelligenceEntity, execution.entity_id)
            if not entity or entity.meeting_id != meeting_id:
                continue
        entity = await session.get(IntelligenceEntity, execution.entity_id)
        timeline.append(
            {
                "id": execution.id,
                "event_type": "execution_update",
                "title": entity.title if entity else execution.entity_id,
                "description": f"{execution.status} • {execution.progress_percent or 0}%",
                "meeting_id": entity.meeting_id if entity else meeting_id,
                "entity_id": execution.entity_id,
                "timestamp": execution.updated_at.isoformat() if execution.updated_at else execution.created_at.isoformat(),
                "status": execution.status,
                "blocking_ids": execution.blocking_entity_ids or [],
            }
        )

    mutation_filters = [GraphMutation.organization_id == organization_id]
    if meeting_id:
        mutation_filters.append(GraphMutation.meeting_id == meeting_id)
    mutation_result = await session.execute(
        select(GraphMutation).where(*mutation_filters).order_by(GraphMutation.sequence_number.desc()).limit(limit)
    )
    for mutation in mutation_result.scalars().all():
        timeline.append(
            {
                "id": mutation.id,
                "event_type": f"graph_{mutation.mutation_type}",
                "title": mutation.mutation_type.replace("_", " ").title(),
                "description": mutation.payload.get("label") or mutation.payload.get("title") or mutation.mutation_type,
                "meeting_id": mutation.meeting_id,
                "entity_id": mutation.payload.get("source_entity_id"),
                "timestamp": mutation.created_at.isoformat() if mutation.created_at else datetime.utcnow().isoformat(),
                "sequence_number": mutation.sequence_number,
            }
        )

    timeline.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return {"organization_id": organization_id, "meeting_id": meeting_id, "events": timeline[:limit]}


@router.get("/context/{node_id}", response_model=Dict[str, Any])
async def intelligence_context(
    node_id: str,
    meeting_id: str,
    organization_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the node, source entity, linked edges, and nearby execution context for the inspector panel."""
    membership = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == organization_id)
            & (OrganizationMember.user_id == current_user.id)
            & (OrganizationMember.is_active.is_(True))
        )
    )
    if not membership.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    node = await session.get(GraphNode, node_id)
    if not node or node.meeting_id != meeting_id:
        raise HTTPException(status_code=404, detail="Node not found")

    source_entity = None
    execution_state = None
    transcript_references: List[Dict[str, Any]] = []

    if node.source_entity_id:
        source_entity = await session.get(IntelligenceEntity, node.source_entity_id)
        if source_entity:
            execution_result = await session.execute(
                select(ExecutionState).where(ExecutionState.entity_id == source_entity.id)
            )
            execution_state = execution_result.scalars().first()

            transcript_references.append(
                {
                    "meeting_id": source_entity.meeting_id,
                    "entity_id": source_entity.id,
                    "speaker": source_entity.source_speaker,
                    "timestamp": source_entity.source_timestamp,
                    "description": source_entity.description,
                }
            )

    edges_result = await session.execute(
        select(GraphEdge).where(
            (GraphEdge.meeting_id == meeting_id)
            & ((GraphEdge.source_node_id == node_id) | (GraphEdge.target_node_id == node_id))
        )
    )
    linked_edges = [
        {
            "id": edge.id,
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "relationship_type": edge.relationship_type,
            "weight": edge.weight,
            "metadata": edge.meta,
        }
        for edge in edges_result.scalars().all()
    ]

    related_nodes: List[Dict[str, Any]] = []
    if linked_edges:
        linked_node_ids = {edge["source_node_id"] for edge in linked_edges} | {edge["target_node_id"] for edge in linked_edges}
        linked_node_ids.discard(node_id)
        linked_nodes_result = await session.execute(select(GraphNode).where(GraphNode.id.in_(linked_node_ids)))
        for linked_node in linked_nodes_result.scalars().all():
            related_nodes.append(
                {
                    "id": linked_node.id,
                    "type": linked_node.node_type.value if hasattr(linked_node.node_type, "value") else linked_node.node_type,
                    "label": linked_node.label,
                    "description": linked_node.description,
                    "source_entity_id": linked_node.source_entity_id,
                }
            )

    return {
        "node": {
            "id": node.id,
            "type": node.node_type.value if hasattr(node.node_type, "value") else node.node_type,
            "label": node.label,
            "description": node.description,
            "metadata": node.meta,
            "source_entity_id": node.source_entity_id,
        },
        "source_entity": {
            "id": source_entity.id,
            "entity_type": source_entity.entity_type.value if hasattr(source_entity.entity_type, "value") else source_entity.entity_type,
            "title": source_entity.title,
            "description": source_entity.description,
            "status": source_entity.status,
            "confidence_score": source_entity.confidence_score,
            "assigned_to": source_entity.assigned_to,
            "due_date": source_entity.due_date.isoformat() if source_entity.due_date else None,
            "priority": source_entity.priority,
        } if source_entity else None,
        "execution_state": {
            "execution_id": execution_state.id,
            "status": execution_state.status,
            "progress_percent": execution_state.progress_percent,
            "due_date": execution_state.due_date.isoformat() if execution_state and execution_state.due_date else None,
            "blocking_ids": execution_state.blocking_entity_ids or [],
            "depends_on_ids": execution_state.depends_on_entity_ids or [],
            "recurring": execution_state.recurring,
            "recurrence_pattern": execution_state.recurrence_pattern,
        } if execution_state else None,
        "related_nodes": related_nodes,
        "linked_edges": linked_edges,
        "transcript_references": transcript_references,
    }