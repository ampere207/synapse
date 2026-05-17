"""Decision and action item models"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Decision(Base):
    """Decision model"""
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    graph_node_id = Column(String(36), ForeignKey("graph_nodes.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    decided_by = Column(String(255), nullable=True)  # person name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ActionItem(Base):
    """Action item model"""
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    graph_node_id = Column(String(36), ForeignKey("graph_nodes.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(String(255), nullable=True)  # person name
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
