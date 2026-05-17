"""Graph node and edge models for operational intelligence"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class NodeTypeEnum(str, enum.Enum):
    """Graph node types"""
    TOPIC = "topic"
    DECISION = "decision"
    ACTION = "action"
    PERSON = "person"
    OBJECTIVE = "objective"


class GraphNode(Base):
    """Graph node model"""
    __tablename__ = "graph_nodes"

    id = Column(String(36), primary_key=True, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    node_type = Column(Enum(NodeTypeEnum), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_entity_id = Column(String(36), ForeignKey("intelligence_entities.id"), nullable=True, index=True)
    meta = Column('metadata_json', JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GraphEdge(Base):
    """Graph edge model - relationships between nodes"""
    __tablename__ = "graph_edges"

    id = Column(String(36), primary_key=True, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    source_node_id = Column(String(36), ForeignKey("graph_nodes.id"), nullable=False)
    target_node_id = Column(String(36), ForeignKey("graph_nodes.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # "depends_on", "relates_to", etc.
    weight = Column(String(50), default="medium")  # "low", "medium", "high"
    meta = Column('metadata_json', JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
