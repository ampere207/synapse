"""Realtime infrastructure - WebSocket manager"""
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections per organization and meeting"""
    
    def __init__(self):
        # Structure: org_id -> meeting_id -> {user_id: websocket}
        self.active_connections: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}
        self.connection_last_seen: Dict[str, Dict[str, Dict[str, datetime]]] = {}
    
    async def connect(self, org_id: str, meeting_id: str, user_id: str, websocket: WebSocket):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        
        if org_id not in self.active_connections:
            self.active_connections[org_id] = {}
        if meeting_id not in self.active_connections[org_id]:
            self.active_connections[org_id][meeting_id] = {}
        if org_id not in self.connection_last_seen:
            self.connection_last_seen[org_id] = {}
        if meeting_id not in self.connection_last_seen[org_id]:
            self.connection_last_seen[org_id][meeting_id] = {}
        
        self.active_connections[org_id][meeting_id][user_id] = websocket
        self.connection_last_seen[org_id][meeting_id][user_id] = datetime.utcnow()

    def touch(self, org_id: str, meeting_id: str, user_id: str):
        if (
            org_id in self.connection_last_seen
            and meeting_id in self.connection_last_seen[org_id]
            and user_id in self.connection_last_seen[org_id][meeting_id]
        ):
            self.connection_last_seen[org_id][meeting_id][user_id] = datetime.utcnow()
    
    def disconnect(self, org_id: str, meeting_id: str, user_id: str):
        """Remove a WebSocket connection"""
        if org_id in self.active_connections:
            if meeting_id in self.active_connections[org_id]:
                if user_id in self.active_connections[org_id][meeting_id]:
                    del self.active_connections[org_id][meeting_id][user_id]
                if (
                    org_id in self.connection_last_seen
                    and meeting_id in self.connection_last_seen[org_id]
                    and user_id in self.connection_last_seen[org_id][meeting_id]
                ):
                    del self.connection_last_seen[org_id][meeting_id][user_id]
                if not self.active_connections[org_id][meeting_id]:
                    del self.active_connections[org_id][meeting_id]
                    if org_id in self.connection_last_seen and meeting_id in self.connection_last_seen[org_id]:
                        del self.connection_last_seen[org_id][meeting_id]
            if not self.active_connections[org_id]:
                del self.active_connections[org_id]
                if org_id in self.connection_last_seen:
                    del self.connection_last_seen[org_id]
    
    async def broadcast_to_meeting(
        self,
        org_id: str,
        meeting_id: str,
        message: Dict[str, Any],
        exclude_user: str = None
    ):
        """Broadcast message to all users in a meeting"""
        if org_id not in self.active_connections:
            return
        if meeting_id not in self.active_connections[org_id]:
            return
        
        disconnected_users = []
        for user_id, websocket in self.active_connections[org_id][meeting_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await websocket.send_json(message)
                self.touch(org_id, meeting_id, user_id)
            except Exception:
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(org_id, meeting_id, user_id)
    
    async def send_personal_message(
        self,
        org_id: str,
        meeting_id: str,
        user_id: str,
        message: Dict[str, Any]
    ):
        """Send message to specific user"""
        if org_id in self.active_connections:
            if meeting_id in self.active_connections[org_id]:
                if user_id in self.active_connections[org_id][meeting_id]:
                    websocket = self.active_connections[org_id][meeting_id][user_id]
                    try:
                        await websocket.send_json(message)
                        self.touch(org_id, meeting_id, user_id)
                    except Exception:
                        self.disconnect(org_id, meeting_id, user_id)

    def cleanup_stale_connections(self, max_age_seconds: int = 120):
        """Remove sockets that have not been touched recently."""
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        stale = []
        for org_id, meetings in self.connection_last_seen.items():
            for meeting_id, users in meetings.items():
                for user_id, last_seen in users.items():
                    if last_seen < cutoff:
                        stale.append((org_id, meeting_id, user_id))

        for org_id, meeting_id, user_id in stale:
            self.disconnect(org_id, meeting_id, user_id)


# Global connection manager
manager = ConnectionManager()
