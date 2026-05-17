"""Organizations API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.models.organization import Organization, OrganizationMember, RoleEnum
from app.models.user import User
from fastapi import Header

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


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


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new organization"""
    org_id = str(uuid.uuid4())
    
    db_org = Organization(
        id=org_id,
        name=org_data.name,
        slug=org_data.slug,
        description=org_data.description,
        owner_id=current_user.id,
    )
    db.add(db_org)
    
    # Add owner as member
    member_id = str(uuid.uuid4())
    member = OrganizationMember(
        id=member_id,
        organization_id=org_id,
        user_id=current_user.id,
        role=RoleEnum.OWNER,
    )
    db.add(member)
    
    await db.commit()
    await db.refresh(db_org)
    return db_org


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get organization by ID (with access control)"""
    # Check if user is member of organization
    stmt = select(OrganizationMember).where(
        (OrganizationMember.organization_id == org_id) &
        (OrganizationMember.user_id == current_user.id) &
        (OrganizationMember.is_active == True)
    )
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Access denied")
    
    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org
