"""Graph mutation API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, Meeting, OrganizationMember, GraphNode, GraphEdge
from app.graph_engine import GraphMutationService, GraphMutationRequest
from app.graph_engine.schemas import GraphNodePayload, GraphEdgePayload

router = APIRouter(prefix="/api/graph", tags=["graph"])


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


@router.post("/nodes", response_model=dict)
async def create_graph_node(
    meeting_id: str,
    node: GraphNodePayload,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new graph node in a meeting"""
    # Verify user has access to meeting
    from sqlalchemy import select
    
    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        db_node, mutation = await GraphMutationService.create_node(
            session=session,
            meeting_id=meeting_id,
            node=node,
        )
        await session.commit()
        return {
            "node": {
                "id": db_node.id,
                "type": db_node.node_type.value if hasattr(db_node.node_type, "value") else db_node.node_type,
                "label": db_node.label,
                "description": db_node.description,
                "metadata": db_node.meta,
                "source_entity_id": db_node.source_entity_id,
            },
            "mutation": {
                "id": mutation.id,
                "mutation_type": mutation.mutation_type,
                "sequence_number": mutation.sequence_number,
                "created_at": mutation.created_at.isoformat(),
            },
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/nodes/{node_id}", response_model=dict)
async def update_graph_node(
    node_id: str,
    meeting_id: str,
    updates: dict,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing graph node"""
    from sqlalchemy import select

    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        db_node, mutation = await GraphMutationService.update_node(
            session=session,
            meeting_id=meeting_id,
            node_id=node_id,
            updates=updates,
        )
        if not db_node:
            raise HTTPException(status_code=404, detail="Node not found")

        await session.commit()
        return {
            "node": {
                "id": db_node.id,
                "type": db_node.node_type.value if hasattr(db_node.node_type, "value") else db_node.node_type,
                "label": db_node.label,
                "description": db_node.description,
                "metadata": db_node.meta,
                "source_entity_id": db_node.source_entity_id,
            },
            "mutation": {
                "id": mutation.id,
                "mutation_type": mutation.mutation_type,
                "sequence_number": mutation.sequence_number,
                "created_at": mutation.created_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges", response_model=dict)
async def create_graph_edge(
    meeting_id: str,
    edge: GraphEdgePayload,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new graph edge between nodes"""
    from sqlalchemy import select

    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        db_edge, mutation = await GraphMutationService.create_edge(
            session=session,
            meeting_id=meeting_id,
            edge=edge,
        )
        await session.commit()
        return {
            "edge": {
                "id": db_edge.id,
                "source_node_id": db_edge.source_node_id,
                "target_node_id": db_edge.target_node_id,
                "relationship_type": db_edge.relationship_type,
                "weight": db_edge.weight,
            },
            "mutation": {
                "id": mutation.id,
                "mutation_type": mutation.mutation_type,
                "sequence_number": mutation.sequence_number,
                "created_at": mutation.created_at.isoformat(),
            },
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/edges/{edge_id}", response_model=dict)
async def update_graph_edge(
    edge_id: str,
    meeting_id: str,
    updates: dict,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing graph edge"""
    from sqlalchemy import select

    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        db_edge, mutation = await GraphMutationService.update_edge(
            session=session,
            meeting_id=meeting_id,
            edge_id=edge_id,
            updates=updates,
        )
        if not db_edge:
            raise HTTPException(status_code=404, detail="Edge not found")

        await session.commit()
        return {
            "edge": {
                "id": db_edge.id,
                "source_node_id": db_edge.source_node_id,
                "target_node_id": db_edge.target_node_id,
                "relationship_type": db_edge.relationship_type,
                "weight": db_edge.weight,
            },
            "mutation": {
                "id": mutation.id,
                "mutation_type": mutation.mutation_type,
                "sequence_number": mutation.sequence_number,
                "created_at": mutation.created_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mutations", response_model=List[dict])
async def get_graph_mutations(
    meeting_id: str,
    since_sequence: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve graph mutations for realtime sync"""
    from sqlalchemy import select

    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    mutations = await GraphMutationService.get_mutations_since_sequence(
        session=session,
        meeting_id=meeting_id,
        since_sequence=since_sequence,
        limit=limit,
    )

    return [
        {
            "id": m.id,
            "mutation_type": m.mutation_type,
            "sequence_number": m.sequence_number,
            "payload": m.payload,
            "metadata": m.metadata,
            "created_at": m.created_at.isoformat(),
        }
        for m in mutations
    ]


@router.get("/nodes", response_model=List[dict])
async def get_graph_nodes(
    meeting_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all graph nodes for a meeting"""
    from sqlalchemy import select
    from app.models import GraphNode

    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await session.execute(
        select(GraphNode).where(GraphNode.meeting_id == meeting_id)
    )
    nodes = result.scalars().all()

    return [
        {
            "id": n.id,
            "type": n.node_type.value if hasattr(n.node_type, "value") else n.node_type,
            "label": n.label,
            "description": n.description,
            "metadata": n.meta,
            "source_entity_id": n.source_entity_id,
        }
        for n in nodes
    ]


@router.get("/edges", response_model=List[dict])
async def get_graph_edges(
    meeting_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all graph edges for a meeting"""
    meeting = await session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify membership
    from app.models import OrganizationMember
    member = await session.execute(
        select(OrganizationMember).where(
            (OrganizationMember.organization_id == meeting.organization_id)
            & (OrganizationMember.user_id == current_user.id)
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await session.execute(
        select(GraphEdge).where(GraphEdge.meeting_id == meeting_id)
    )
    edges = result.scalars().all()

    return [
        {
            "id": e.id,
            "source_node_id": e.source_node_id,
            "target_node_id": e.target_node_id,
            "relationship_type": e.relationship_type,
            "weight": e.weight,
            "metadata": e.meta,
        }
        for e in edges
    ]
