"""Organization and workspace models"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class Organization(Base):
    """Organization model"""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(1024), nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RoleEnum(str, enum.Enum):
    """Organization member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationMember(Base):
    """Organization member model"""
    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
