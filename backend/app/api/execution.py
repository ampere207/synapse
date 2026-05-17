"""Execution continuity API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, Meeting, OrganizationMember, IntelligenceEntity, ExecutionState
from app.services.execution_continuity import ExecutionContinuityService

router = APIRouter(prefix="/api/execution", tags=["execution"])


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


@router.get("/status/{entity_id}", response_model=Dict[str, Any])
async def get_execution_status(
    entity_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution status for an entity"""
    try:
        # Get execution state
        result = await session.execute(
            select(ExecutionState).where(ExecutionState.entity_id == entity_id)
        )
        exec_state = result.scalars().first()
        
        if not exec_state:
            raise HTTPException(status_code=404, detail="Execution state not found")
        
        # Verify access by checking organization
        entity = await session.get(IntelligenceEntity, entity_id)
        if entity:
            member = await session.execute(
                select(OrganizationMember).where(
                    (OrganizationMember.organization_id == entity.organization_id)
                    & (OrganizationMember.user_id == current_user.id)
                )
            )
            if not member.scalars().first():
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Check for updates
        await ExecutionContinuityService.check_blocked_status(session, exec_state.id)
        await ExecutionContinuityService.detect_overdue(session, exec_state.id)
        
        return {
            "execution_id": exec_state.id,
            "entity_id": entity_id,
            "status": exec_state.status,
            "progress_percent": exec_state.progress_percent,
            "due_date": exec_state.due_date.isoformat() if exec_state.due_date else None,
            "completed_date": exec_state.completed_date.isoformat() if exec_state.completed_date else None,
            "depends_on": exec_state.depends_on_entity_ids or [],
            "blocking": exec_state.blocking_entity_ids or [],
            "recurring": exec_state.recurring,
            "recurrence_pattern": exec_state.recurrence_pattern,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/status/{entity_id}", response_model=Dict[str, Any])
async def update_execution_status(
    entity_id: str,
    status: str,
    progress_percent: int = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update execution status for an entity"""
    try:
        # Get execution state
        result = await session.execute(
            select(ExecutionState).where(ExecutionState.entity_id == entity_id)
        )
        exec_state = result.scalars().first()
        
        if not exec_state:
            raise HTTPException(status_code=404, detail="Execution state not found")
        
        # Verify access
        entity = await session.get(IntelligenceEntity, entity_id)
        if entity:
            member = await session.execute(
                select(OrganizationMember).where(
                    (OrganizationMember.organization_id == entity.organization_id)
                    & (OrganizationMember.user_id == current_user.id)
                )
            )
            if not member.scalars().first():
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update status
        updated = await ExecutionContinuityService.update_status(
            session=session,
            execution_id=exec_state.id,
            new_status=status,
            progress_percent=progress_percent,
        )
        
        await session.commit()
        
        # If completed and recurring, handle recurrence
        if status == ExecutionContinuityService.STATUS_COMPLETED:
            next_exec = await ExecutionContinuityService.handle_completion_and_recurrence(
                session=session,
                execution_id=exec_state.id,
            )
            await session.commit()
        
        return {
            "execution_id": exec_state.id,
            "status": updated.status,
            "progress_percent": updated.progress_percent,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-dependency", response_model=Dict[str, Any])
async def add_dependency(
    entity_id: str,
    depends_on_entity_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a dependency to an execution state"""
    try:
        # Get execution state
        result = await session.execute(
            select(ExecutionState).where(ExecutionState.entity_id == entity_id)
        )
        exec_state = result.scalars().first()
        
        if not exec_state:
            raise HTTPException(status_code=404, detail="Execution state not found")
        
        # Verify access
        entity = await session.get(IntelligenceEntity, entity_id)
        if entity:
            member = await session.execute(
                select(OrganizationMember).where(
                    (OrganizationMember.organization_id == entity.organization_id)
                    & (OrganizationMember.user_id == current_user.id)
                )
            )
            if not member.scalars().first():
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Add dependency
        success = await ExecutionContinuityService.add_dependency(
            session=session,
            execution_id=exec_state.id,
            depends_on_entity_id=depends_on_entity_id,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add dependency")
        
        await session.commit()
        
        return {
            "execution_id": exec_state.id,
            "depends_on": exec_state.depends_on_entity_ids or [],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-recurrence", response_model=Dict[str, Any])
async def set_recurrence(
    entity_id: str,
    recurrence_pattern: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable recurrence for an execution"""
    try:
        # Get execution state
        result = await session.execute(
            select(ExecutionState).where(ExecutionState.entity_id == entity_id)
        )
        exec_state = result.scalars().first()
        
        if not exec_state:
            raise HTTPException(status_code=404, detail="Execution state not found")
        
        # Verify access
        entity = await session.get(IntelligenceEntity, entity_id)
        if entity:
            member = await session.execute(
                select(OrganizationMember).where(
                    (OrganizationMember.organization_id == entity.organization_id)
                    & (OrganizationMember.user_id == current_user.id)
                )
            )
            if not member.scalars().first():
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Set recurrence
        success = await ExecutionContinuityService.set_recurrence(
            session=session,
            execution_id=exec_state.id,
            recurrence_pattern=recurrence_pattern,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to set recurrence")
        
        await session.commit()
        
        return {
            "execution_id": exec_state.id,
            "recurring": True,
            "recurrence_pattern": recurrence_pattern,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{organization_id}", response_model=Dict[str, Any])
async def get_execution_summary(
    organization_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution summary for an organization"""
    try:
        # Verify access
        member = await session.execute(
            select(OrganizationMember).where(
                (OrganizationMember.organization_id == organization_id)
                & (OrganizationMember.user_id == current_user.id)
            )
        )
        if not member.scalars().first():
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get summary
        summary = await ExecutionContinuityService.get_execution_summary(
            session=session,
            organization_id=organization_id,
        )
        
        # Get critical items
        critical = await ExecutionContinuityService.get_critical_items(
            session=session,
            organization_id=organization_id,
        )
        
        return {
            **summary,
            "critical_items": critical,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
