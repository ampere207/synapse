"""Decision and action item schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DecisionCreate(BaseModel):
    """Schema for creating a decision"""
    title: str
    description: Optional[str] = None
    decided_by: Optional[str] = None


class DecisionResponse(BaseModel):
    """Schema for decision response"""
    id: str
    meeting_id: str
    organization_id: str
    graph_node_id: Optional[str]
    title: str
    description: Optional[str]
    decided_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionItemCreate(BaseModel):
    """Schema for creating an action item"""
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class ActionItemResponse(BaseModel):
    """Schema for action item response"""
    id: str
    meeting_id: str
    organization_id: str
    graph_node_id: Optional[str]
    title: str
    description: Optional[str]
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
