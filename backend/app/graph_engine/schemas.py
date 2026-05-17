"""Graph mutation schema and utilities"""
from pydantic import BaseModel
from typing import Optional, List, Any
from enum import Enum


class MutationType(str, Enum):
    """Types of graph mutations"""
    NODE_ADDED = "node_added"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    EDGE_ADDED = "edge_added"
    EDGE_UPDATED = "edge_updated"
    EDGE_DELETED = "edge_deleted"


class GraphNodePayload(BaseModel):
    """Payload for a graph node mutation"""
    id: str
    type: str  # "person", "decision", "action", "blocker", "topic", "meeting"
    label: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    source_entity_id: Optional[str] = None  # Link to IntelligenceEntity if applicable


class GraphEdgePayload(BaseModel):
    """Payload for a graph edge mutation"""
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str  # "depends_on", "assigned_to", "discussed_in", "blocked_by", "related_to", "impacts"
    weight: str = "medium"  # "low", "medium", "high"
    metadata: Optional[dict] = None


class GraphMutationRequest(BaseModel):
    """Request to mutate the graph"""
    mutation_type: MutationType
    node: Optional[GraphNodePayload] = None
    edge: Optional[GraphEdgePayload] = None
    metadata: Optional[dict] = None


class GraphMutationResponse(BaseModel):
    """Response from graph mutation"""
    id: str
    mutation_type: MutationType
    sequence_number: int
    created_at: str
