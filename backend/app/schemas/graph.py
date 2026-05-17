"""Graph schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from app.models.graph import NodeTypeEnum


class GraphNodeCreate(BaseModel):
    """Schema for creating a graph node"""
    node_type: NodeTypeEnum
    label: str
    description: Optional[str] = None
    metadata: Optional[Any] = None


class GraphNodeResponse(BaseModel):
    """Schema for graph node response"""
    id: str
    meeting_id: str
    organization_id: str
    node_type: NodeTypeEnum
    label: str
    description: Optional[str]
    metadata: Optional[Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphEdgeCreate(BaseModel):
    """Schema for creating a graph edge"""
    source_node_id: str
    target_node_id: str
    relationship_type: str
    weight: Optional[str] = "medium"
    metadata: Optional[Any] = None


class GraphEdgeResponse(BaseModel):
    """Schema for graph edge response"""
    id: str
    meeting_id: str
    organization_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    weight: str
    metadata: Optional[Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
