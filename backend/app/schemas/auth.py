"""Authentication schemas"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
