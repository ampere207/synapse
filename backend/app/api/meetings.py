"""Meetings API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.organizations import get_current_user
from app.schemas.meeting import MeetingCreate, MeetingResponse, MeetingUpdate
from app.models.meeting import Meeting, MeetingStatusEnum
from app.models.user import User
from app.models.organization import OrganizationMember

router = APIRouter(prefix="/api/organizations", tags=["meetings"])


async def check_org_access(org_id: str, current_user: User, db: AsyncSession):
    """Check if user has access to organization"""
    stmt = select(OrganizationMember).where(
        (OrganizationMember.organization_id == org_id) &
        (OrganizationMember.user_id == current_user.id) &
        (OrganizationMember.is_active == True)
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None


@router.post("/{org_id}/meetings", response_model=MeetingResponse)
async def create_meeting(
    org_id: str,
    meeting_data: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new meeting"""
    if not await check_org_access(org_id, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    meeting_id = str(uuid.uuid4())
    db_meeting = Meeting(
        id=meeting_id,
        organization_id=org_id,
        created_by=current_user.id,
        title=meeting_data.title,
        description=meeting_data.description,
    )
    db.add(db_meeting)
    await db.commit()
    await db.refresh(db_meeting)
    return db_meeting


@router.get("/{org_id}/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    org_id: str,
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get meeting by ID"""
    if not await check_org_access(org_id, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    stmt = select(Meeting).where(
        (Meeting.id == meeting_id) & (Meeting.organization_id == org_id)
    )
    result = await db.execute(stmt)
    meeting = result.scalars().first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return meeting


@router.patch("/{org_id}/meetings/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    org_id: str,
    meeting_id: str,
    meeting_data: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update meeting"""
    if not await check_org_access(org_id, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    stmt = select(Meeting).where(
        (Meeting.id == meeting_id) & (Meeting.organization_id == org_id)
    )
    result = await db.execute(stmt)
    meeting = result.scalars().first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting_data.title is not None:
        meeting.title = meeting_data.title
    if meeting_data.description is not None:
        meeting.description = meeting_data.description
    if meeting_data.status is not None:
        meeting.status = meeting_data.status
        if meeting_data.status == MeetingStatusEnum.LIVE:
            meeting.started_at = datetime.now(timezone.utc)
        elif meeting_data.status == MeetingStatusEnum.COMPLETED:
            meeting.ended_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(meeting)
    return meeting
