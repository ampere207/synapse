"""Graph mutation service for incremental graph operations"""
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.graph import GraphNode, GraphEdge
from app.models.intelligence import GraphMutation
from app.graph_engine.schemas import MutationType, GraphNodePayload, GraphEdgePayload


class GraphMutationService:
    """Service for creating and tracking incremental graph mutations"""

    @staticmethod
    async def create_node(
        session: AsyncSession,
        meeting_id: str,
        organization_id: str,
        node: GraphNodePayload,
        metadata: Optional[dict] = None,
    ) -> tuple[GraphNode, GraphMutation]:
        """Create a new graph node and record the mutation"""
        # Create the node
        db_node = GraphNode(
            id=node.id,
            meeting_id=meeting_id,
            organization_id=organization_id,
            node_type=node.type,
            label=node.label,
            description=node.description,
            meta=node.metadata or {},
            source_entity_id=node.source_entity_id,
        )
        session.add(db_node)

        # Record the mutation
        mutation = await GraphMutationService._create_mutation(
            session=session,
            organization_id=organization_id,
            meeting_id=meeting_id,
            mutation_type=MutationType.NODE_ADDED,
            payload=node.model_dump(),
            metadata=metadata,
        )

        await session.flush()  # Ensure IDs are generated
        return db_node, mutation

    @staticmethod
    async def update_node(
        session: AsyncSession,
        meeting_id: str,
        node_id: str,
        updates: Dict[str, Any],
        metadata: Optional[dict] = None,
    ) -> tuple[Optional[GraphNode], Optional[GraphMutation]]:
        """Update an existing graph node and record the mutation"""
        from sqlalchemy import select

        # Fetch the node
        result = await session.execute(
            select(GraphNode).where(
                and_(GraphNode.id == node_id, GraphNode.meeting_id == meeting_id)
            )
        )
        db_node = result.scalars().first()

        if not db_node:
            return None, None

        # Apply updates
        for key, value in updates.items():
            if hasattr(db_node, key):
                setattr(db_node, key, value)

        # Record the mutation
        mutation = await GraphMutationService._create_mutation(
            session=session,
            meeting_id=meeting_id,
            mutation_type=MutationType.NODE_UPDATED,
            payload={"id": node_id, **updates},
            metadata=metadata,
        )

        await session.flush()
        return db_node, mutation

    @staticmethod
    async def create_edge(
        session: AsyncSession,
        meeting_id: str,
        organization_id: str,
        edge: GraphEdgePayload,
        metadata: Optional[dict] = None,
    ) -> tuple[GraphEdge, GraphMutation]:
        """Create a new graph edge and record the mutation"""
        # Create the edge
        db_edge = GraphEdge(
            id=edge.id,
            meeting_id=meeting_id,
            organization_id=organization_id,
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            relationship_type=edge.relationship_type,
            weight=edge.weight,
            meta=edge.metadata or {},
        )
        session.add(db_edge)

        # Record the mutation
        mutation = await GraphMutationService._create_mutation(
            session=session,
            organization_id=organization_id,
            meeting_id=meeting_id,
            mutation_type=MutationType.EDGE_ADDED,
            payload=edge.model_dump(),
            metadata=metadata,
        )

        await session.flush()
        return db_edge, mutation

    @staticmethod
    async def update_edge(
        session: AsyncSession,
        meeting_id: str,
        edge_id: str,
        updates: Dict[str, Any],
        metadata: Optional[dict] = None,
    ) -> tuple[Optional[GraphEdge], Optional[GraphMutation]]:
        """Update an existing graph edge and record the mutation"""
        from sqlalchemy import select

        # Fetch the edge
        result = await session.execute(
            select(GraphEdge).where(
                and_(GraphEdge.id == edge_id, GraphEdge.meeting_id == meeting_id)
            )
        )
        db_edge = result.scalars().first()

        if not db_edge:
            return None, None

        # Apply updates
        for key, value in updates.items():
            if hasattr(db_edge, key):
                setattr(db_edge, key, value)

        # Record the mutation
        mutation = await GraphMutationService._create_mutation(
            session=session,
            meeting_id=meeting_id,
            mutation_type=MutationType.EDGE_UPDATED,
            payload={"id": edge_id, **updates},
            metadata=metadata,
        )

        await session.flush()
        return db_edge, mutation

    @staticmethod
    async def get_mutations_since_sequence(
        session: AsyncSession,
        meeting_id: str,
        since_sequence: int = 0,
        limit: int = 100,
    ) -> List[GraphMutation]:
        """Retrieve mutations since a given sequence number for realtime sync"""
        from sqlalchemy import select

        result = await session.execute(
            select(GraphMutation)
            .where(
                and_(
                    GraphMutation.meeting_id == meeting_id,
                    GraphMutation.sequence_number > since_sequence,
                )
            )
            .order_by(GraphMutation.sequence_number)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def _create_mutation(
        session: AsyncSession,
        organization_id: str,
        meeting_id: str,
        mutation_type: MutationType,
        payload: dict,
        metadata: Optional[dict] = None,
    ) -> GraphMutation:
        """Internal helper to record a graph mutation"""
        from sqlalchemy import select, func

        # Get next sequence number for this meeting
        result = await session.execute(
            select(func.max(GraphMutation.sequence_number)).where(
                GraphMutation.meeting_id == meeting_id
            )
        )
        max_sequence = result.scalar() or 0
        next_sequence = max_sequence + 1

        # Create mutation record
        mutation = GraphMutation(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            meeting_id=meeting_id,
            mutation_type=mutation_type.value,
            sequence_number=next_sequence,
            payload=payload,
            metadata=metadata or {},
        )
        session.add(mutation)
        await session.flush()

        return mutation
