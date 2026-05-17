"""Execution continuity service for tracking task status and dependencies"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.intelligence import ExecutionState, IntelligenceEntity


class ExecutionContinuityService:
    """Service for managing execution state, dependencies, and recurrence"""

    # Status definitions
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_BLOCKED = "blocked"
    STATUS_OVERDUE = "overdue"
    
    # Recurrence patterns
    RECURRENCE_DAILY = "daily"
    RECURRENCE_WEEKLY = "weekly"
    RECURRENCE_BIWEEKLY = "biweekly"
    RECURRENCE_MONTHLY = "monthly"

    @staticmethod
    async def create_execution_state(
        session: AsyncSession,
        entity_id: str,
        organization_id: str,
        status: str = STATUS_PENDING,
        due_date: Optional[datetime] = None,
        depends_on: Optional[List[str]] = None,
    ) -> ExecutionState:
        """Create initial execution state for an entity"""
        exec_state = ExecutionState(
            id=str(__import__("uuid").uuid4()),
            organization_id=organization_id,
            entity_id=entity_id,
            status=status,
            due_date=due_date,
            depends_on_entity_ids=depends_on or [],
            blocking_entity_ids=[],
            progress_percent=0,
            recurring=False,
        )
        session.add(exec_state)
        await session.flush()
        return exec_state

    @staticmethod
    async def update_status(
        session: AsyncSession,
        execution_id: str,
        new_status: str,
        progress_percent: Optional[int] = None,
    ) -> Optional[ExecutionState]:
        """Update execution status"""
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return None
        
        exec_state.status = new_status
        if progress_percent is not None:
            exec_state.progress_percent = max(0, min(100, progress_percent))
        
        if new_status == ExecutionContinuityService.STATUS_COMPLETED:
            exec_state.completed_date = datetime.utcnow()
            exec_state.progress_percent = 100
        
        exec_state.last_update = datetime.utcnow()
        await session.flush()
        return exec_state

    @staticmethod
    async def add_dependency(
        session: AsyncSession,
        execution_id: str,
        depends_on_entity_id: str,
    ) -> bool:
        """Add a dependency to an execution state"""
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return False
        
        deps = exec_state.depends_on_entity_ids or []
        if depends_on_entity_id not in deps:
            deps.append(depends_on_entity_id)
            exec_state.depends_on_entity_ids = deps
            await session.flush()
        
        return True

    @staticmethod
    async def check_blocked_status(
        session: AsyncSession,
        execution_id: str,
    ) -> bool:
        """
        Check if an execution is blocked by incomplete dependencies.
        Updates status if needed.
        """
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return False
        
        # Get all dependencies
        depends_on = exec_state.depends_on_entity_ids or []
        if not depends_on:
            return False
        
        # Check if any dependency is not completed
        blocking_ids = []
        for dep_id in depends_on:
            # Find execution state for dependency entity
            result = await session.execute(
                select(ExecutionState).where(ExecutionState.entity_id == dep_id)
            )
            dep_exec = result.scalars().first()
            
            if dep_exec and dep_exec.status != ExecutionContinuityService.STATUS_COMPLETED:
                blocking_ids.append(dep_id)
        
        # Update status if blocked
        if blocking_ids:
            if exec_state.status not in [
                ExecutionContinuityService.STATUS_COMPLETED,
                ExecutionContinuityService.STATUS_IN_PROGRESS,
            ]:
                exec_state.status = ExecutionContinuityService.STATUS_BLOCKED
                exec_state.blocking_entity_ids = blocking_ids
                await session.flush()
            return True
        
        return False

    @staticmethod
    async def detect_overdue(
        session: AsyncSession,
        execution_id: str,
    ) -> bool:
        """
        Check if an execution is overdue.
        Updates status if needed.
        """
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return False
        
        if not exec_state.due_date:
            return False
        
        # Check if overdue
        if (
            datetime.utcnow() > exec_state.due_date
            and exec_state.status != ExecutionContinuityService.STATUS_COMPLETED
        ):
            exec_state.status = ExecutionContinuityService.STATUS_OVERDUE
            await session.flush()
            return True
        
        return False

    @staticmethod
    async def detect_staleness(
        session: AsyncSession,
        execution_id: str,
        staleness_days: int = 7,
    ) -> bool:
        """
        Detect if an execution is stale (no progress in N days).
        """
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return False
        
        # Check if last update was more than staleness_days ago
        if exec_state.last_update:
            age = datetime.utcnow() - exec_state.last_update
            return age > timedelta(days=staleness_days)
        
        return False

    @staticmethod
    async def set_recurrence(
        session: AsyncSession,
        execution_id: str,
        recurrence_pattern: str,
    ) -> bool:
        """Enable recurrence for an execution"""
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return False
        
        exec_state.recurring = True
        exec_state.recurrence_pattern = recurrence_pattern
        await session.flush()
        return True

    @staticmethod
    def calculate_next_due_date(
        current_due: datetime,
        recurrence_pattern: str,
    ) -> datetime:
        """Calculate next due date based on recurrence pattern"""
        if recurrence_pattern == ExecutionContinuityService.RECURRENCE_DAILY:
            return current_due + timedelta(days=1)
        elif recurrence_pattern == ExecutionContinuityService.RECURRENCE_WEEKLY:
            return current_due + timedelta(weeks=1)
        elif recurrence_pattern == ExecutionContinuityService.RECURRENCE_BIWEEKLY:
            return current_due + timedelta(weeks=2)
        elif recurrence_pattern == ExecutionContinuityService.RECURRENCE_MONTHLY:
            return current_due + timedelta(days=30)
        else:
            return current_due

    @staticmethod
    async def handle_completion_and_recurrence(
        session: AsyncSession,
        execution_id: str,
    ) -> Optional[ExecutionState]:
        """
        Mark as completed and create new recurring instance if applicable.
        
        Returns:
            New execution state if recurring, None otherwise
        """
        exec_state = await session.get(ExecutionState, execution_id)
        if not exec_state:
            return None
        
        # Mark as completed
        exec_state.status = ExecutionContinuityService.STATUS_COMPLETED
        exec_state.completed_date = datetime.utcnow()
        exec_state.progress_percent = 100
        await session.flush()
        
        # If recurring, create next instance
        if exec_state.recurring and exec_state.recurrence_pattern:
            next_due = ExecutionContinuityService.calculate_next_due_date(
                exec_state.due_date or datetime.utcnow(),
                exec_state.recurrence_pattern,
            )
            
            # Get the original entity
            entity = await session.get(IntelligenceEntity, exec_state.entity_id)
            if entity:
                # Create new execution state for recurrence
                next_exec = ExecutionState(
                    id=str(__import__("uuid").uuid4()),
                    organization_id=exec_state.organization_id,
                    entity_id=exec_state.entity_id,
                    status=ExecutionContinuityService.STATUS_PENDING,
                    due_date=next_due,
                    depends_on_entity_ids=exec_state.depends_on_entity_ids,
                    blocking_entity_ids=[],
                    progress_percent=0,
                    recurring=True,
                    recurrence_pattern=exec_state.recurrence_pattern,
                )
                session.add(next_exec)
                await session.flush()
                return next_exec
        
        return None

    @staticmethod
    async def get_execution_summary(
        session: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Get summary of execution states in an organization"""
        # Get counts by status
        result = await session.execute(
            select(ExecutionState.status).where(
                ExecutionState.organization_id == organization_id
            )
        )
        statuses = result.scalars().all()
        
        status_counts = {}
        for status in statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_executions": len(statuses),
            "by_status": status_counts,
            "pending": status_counts.get(ExecutionContinuityService.STATUS_PENDING, 0),
            "in_progress": status_counts.get(ExecutionContinuityService.STATUS_IN_PROGRESS, 0),
            "completed": status_counts.get(ExecutionContinuityService.STATUS_COMPLETED, 0),
            "blocked": status_counts.get(ExecutionContinuityService.STATUS_BLOCKED, 0),
            "overdue": status_counts.get(ExecutionContinuityService.STATUS_OVERDUE, 0),
        }

    @staticmethod
    async def get_critical_items(
        session: AsyncSession,
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get critical items: blocked, overdue, or stale.
        """
        # Get blocked items
        blocked = await session.execute(
            select(ExecutionState).where(
                and_(
                    ExecutionState.organization_id == organization_id,
                    ExecutionState.status == ExecutionContinuityService.STATUS_BLOCKED,
                )
            )
        )
        
        critical_items = []
        for item in blocked.scalars().all():
            entity = await session.get(IntelligenceEntity, item.entity_id)
            critical_items.append({
                "execution_id": item.id,
                "entity_title": entity.title if entity else "Unknown",
                "status": item.status,
                "reason": "blocked_by_dependencies",
                "blocking_ids": item.blocking_entity_ids,
            })
        
        return critical_items
