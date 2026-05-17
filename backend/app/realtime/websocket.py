"""WebSocket endpoint for realtime transcript streaming"""
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.services.transcript import TranscriptService
from app.realtime import manager
import json
import uuid

ws_router = APIRouter()


async def get_db_session():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session


@ws_router.websocket("/ws/meetings/{org_id}/{meeting_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    org_id: str,
    meeting_id: str,
    token: str = Query(None),
):
    """WebSocket endpoint for realtime meeting updates"""
    
    # Authenticate
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    db = AsyncSessionLocal()
    
    try:
        # Verify user is member of organization
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        await manager.connect(org_id, meeting_id, user_id, websocket)
        
        # Notify others of new connection
        await manager.broadcast_to_meeting(
            org_id,
            meeting_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": user.username,
            },
            exclude_user=user_id
        )
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
            except asyncio.TimeoutError:
                await manager.send_personal_message(
                    org_id,
                    meeting_id,
                    user_id,
                    {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()},
                )
                manager.cleanup_stale_connections()
                continue
            
            # Handle different message types
            message_type = data.get("type")
            manager.touch(org_id, meeting_id, user_id)
            
            if message_type == "transcript_chunk":
                # Broadcast transcript chunk to all users
                chunk_data = {
                    "type": "transcript_chunk",
                    "speaker": data.get("speaker"),
                    "text": data.get("text"),
                    "timestamp": data.get("timestamp"),
                    "sequence_number": data.get("sequence_number", 0),
                }
                await manager.broadcast_to_meeting(org_id, meeting_id, chunk_data)
                
            elif message_type == "graph_update":
                # Broadcast graph update
                graph_data = {
                    "type": "graph_update",
                    "nodes": data.get("nodes", []),
                    "edges": data.get("edges", []),
                }
                await manager.broadcast_to_meeting(org_id, meeting_id, graph_data)
            
            elif message_type == "decision_extracted":
                # Broadcast decision
                decision_data = {
                    "type": "decision_extracted",
                    "title": data.get("title"),
                    "description": data.get("description"),
                }
                await manager.broadcast_to_meeting(org_id, meeting_id, decision_data)
            
            elif message_type == "action_extracted":
                # Broadcast action item
                action_data = {
                    "type": "action_extracted",
                    "title": data.get("title"),
                    "assigned_to": data.get("assigned_to"),
                }
                await manager.broadcast_to_meeting(org_id, meeting_id, action_data)

            elif message_type == "ping":
                await manager.send_personal_message(
                    org_id,
                    meeting_id,
                    user_id,
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                )
    
    except WebSocketDisconnect:
        manager.disconnect(org_id, meeting_id, user_id)
        await manager.broadcast_to_meeting(
            org_id,
            meeting_id,
            {
                "type": "user_left",
                "user_id": user_id,
            }
        )
    finally:
        await db.close()
