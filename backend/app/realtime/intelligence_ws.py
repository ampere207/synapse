"""WebSocket handlers for realtime intelligence updates"""
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSessionLocal
from sqlalchemy import select
from app.core.security import decode_token
from app.models.user import User
from app.models.intelligence import GraphMutation
from app.realtime import manager
import json

intelligence_ws_router = APIRouter()


@intelligence_ws_router.websocket("/ws/intelligence/{org_id}/{meeting_id}")
async def intelligence_websocket(
    websocket: WebSocket,
    org_id: str,
    meeting_id: str,
    token: str = Query(None),
    since_sequence: int = Query(0),
):
    """
    WebSocket endpoint for realtime intelligence updates (graph mutations, extractions, execution status).
    
    Supports subscribing to:
    - Graph mutations (nodes/edges added/updated)
    - Extracted intelligence (decisions, actions, blockers, topics)
    - Execution status updates
    """
    
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
        # Verify user exists
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        await manager.connect(f"{org_id}_intelligence", meeting_id, user_id, websocket)
        
        # Send initial catch-up: recent mutations since sequence
        catch_up_query = select(GraphMutation).where(
            (GraphMutation.meeting_id == meeting_id) &
            (GraphMutation.sequence_number > since_sequence)
        ).order_by(GraphMutation.sequence_number).limit(100)
        
        result = await db.execute(catch_up_query)
        recent_mutations = result.scalars().all()
        
        for mutation in recent_mutations:
            await websocket.send_json({
                "type": "graph_mutation",
                "id": mutation.id,
                "mutation_type": mutation.mutation_type,
                "sequence_number": mutation.sequence_number,
                "payload": mutation.payload,
                "created_at": mutation.created_at.isoformat(),
            })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
                manager.cleanup_stale_connections()
                continue
            message_type = data.get("type")
            manager.touch(f"{org_id}_intelligence", meeting_id, user_id)
            
            if message_type == "graph_mutation":
                # Broadcast graph mutation to all subscribers
                mutation_data = {
                    "type": "graph_mutation",
                    "mutation_type": data.get("mutation_type"),
                    "sequence_number": data.get("sequence_number"),
                    "payload": data.get("payload", {}),
                }
                await manager.broadcast_to_meeting(
                    f"{org_id}_intelligence",
                    meeting_id,
                    mutation_data
                )
            
            elif message_type == "entity_extracted":
                # Broadcast extracted entity
                entity_data = {
                    "type": "entity_extracted",
                    "entity_type": data.get("entity_type"),  # decision, action, blocker, topic
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "confidence_score": data.get("confidence_score"),
                    "entity_id": data.get("entity_id"),
                }
                await manager.broadcast_to_meeting(
                    f"{org_id}_intelligence",
                    meeting_id,
                    entity_data
                )
            
            elif message_type == "execution_status_update":
                # Broadcast execution status change
                status_data = {
                    "type": "execution_status_update",
                    "entity_id": data.get("entity_id"),
                    "status": data.get("status"),
                    "progress_percent": data.get("progress_percent"),
                    "updated_at": data.get("updated_at"),
                }
                await manager.broadcast_to_meeting(
                    f"{org_id}_intelligence",
                    meeting_id,
                    status_data
                )
            
            elif message_type == "topic_transition":
                # Broadcast topic transition in transcript
                transition_data = {
                    "type": "topic_transition",
                    "from_topic": data.get("from_topic"),
                    "to_topic": data.get("to_topic"),
                    "chunk_index": data.get("chunk_index"),
                }
                await manager.broadcast_to_meeting(
                    f"{org_id}_intelligence",
                    meeting_id,
                    transition_data
                )
            
            elif message_type == "subscribe":
                # Client wants to subscribe to specific entity/topic
                subscribe_to = data.get("subscribe_to")  # "entity_id" or "all"
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "subscribe_to": subscribe_to,
                })

            elif message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    
    except WebSocketDisconnect:
        manager.disconnect(f"{org_id}_intelligence", meeting_id, user_id)
    
    finally:
        await db.close()
