"""
WebSocket Collaboration Server for WebCMS

Handles real-time connections, authentication, and message routing.
"""

import json
import asyncio
import logging
from typing import Dict, Set, Optional, Callable
from .manager import CollaborationManager
from .ot import OperationalTransformation, Operation

logger = logging.getLogger("webcms.collaboration")


class CollaborationServer:
    """
    WebSocket server for real-time collaboration.
    
    Manages client connections, authentication, and message broadcasting.
    """
    
    def __init__(self, manager: CollaborationManager = None, auth_callback: Callable = None):
        self.manager = manager or CollaborationManager()
        self.auth_callback = auth_callback
        self.clients: Dict[str, object] = {}
        self.client_info: Dict[str, Dict] = {}
    
    async def handle_client(self, websocket, path: str):
        """Handle a new WebSocket client connection."""
        client_id = None
        document_id = self._extract_document_id(path)
        
        try:
            auth_data = await websocket.recv()
            try:
                auth_message = json.loads(auth_data)
            except json.JSONDecodeError:
                await self._send_error(websocket, "Invalid JSON")
                return
            
            if not self._authenticate(auth_message):
                await self._send_error(websocket, "Authentication failed")
                return
            
            client_id = auth_message.get("client_id") or str(id(websocket))
            user_id = auth_message.get("user_id", "anonymous")
            username = auth_message.get("username", f"User {user_id}")
            
            self.clients[client_id] = websocket
            self.client_info[client_id] = {
                "user_id": user_id,
                "username": username,
                "document_id": document_id
            }
            
            self.manager.register_connection(user_id, document_id, websocket)
            presence = await self.manager.join_document(user_id, username, document_id)
            
            await self._send_message(websocket, {
                "type": "connected",
                "client_id": client_id,
                "document_id": document_id,
                "presence": self.manager.get_active_users(document_id),
                "your_color": presence.color
            })
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(client_id, document_id, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self._send_error(websocket, "Server error")
                    
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            if client_id:
                await self._disconnect_client(client_id)
    
    def _extract_document_id(self, path: str) -> str:
        """Extract document ID from WebSocket path."""
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "collab":
            return parts[1]
        return "default"
    
    async def _disconnect_client(self, client_id: str):
        """Disconnect a client and cleanup."""
        info = self.client_info.get(client_id)
        if info:
            user_id = info["user_id"]
            document_id = info["document_id"]
            await self.manager.leave_document(user_id, document_id)
        
        self.clients.pop(client_id, None)
        self.client_info.pop(client_id, None)
    
    async def _handle_message(self, client_id: str, document_id: str, data: Dict):
        """Route message to appropriate handler."""
        msg_type = data.get("type")
        
        handlers = {
            "operation": self._handle_operation,
            "presence": self._handle_presence,
            "lock_request": self._handle_lock_request,
            "lock_release": self._handle_lock_release,
            "ping": self._handle_ping,
        }
        
        handler = handlers.get(msg_type)
        if handler:
            await handler(client_id, document_id, data)
        else:
            websocket = self.clients.get(client_id)
            if websocket:
                await self._send_error(websocket, f"Unknown message type: {msg_type}")
    
    async def _handle_operation(self, client_id: str, document_id: str, data: Dict):
        """Handle edit operation from client."""
        info = self.client_info.get(client_id)
        if not info:
            return
        
        op_data = data.get("operation", {})
        operation = Operation.from_dict(op_data)
        
        await self._broadcast_to_document(document_id, {
            "type": "operation",
            "client_id": client_id,
            "user_id": info["user_id"],
            "username": info["username"],
            "operation": operation.to_dict()
        }, exclude=info["user_id"])
    
    async def _handle_presence(self, client_id: str, document_id: str, data: Dict):
        """Handle presence update."""
        info = self.client_info.get(client_id)
        if not info:
            return
        
        await self.manager.update_presence(
            info["user_id"],
            document_id,
            cursor_position=data.get("cursor_position"),
            selection_start=data.get("selection_start"),
            selection_end=data.get("selection_end"),
            is_typing=data.get("is_typing")
        )
        
        await self._broadcast_to_document(document_id, {
            "type": "presence_update",
            "user_id": info["user_id"],
            "username": info["username"],
            "presence": self.manager.get_active_users(document_id)
        }, exclude=info["user_id"])
    
    async def _handle_lock_request(self, client_id: str, document_id: str, data: Dict):
        """Handle section lock request."""
        start = data.get("start")
        end = data.get("end")
        
        acquired = await self.manager.acquire_lock(client_id, document_id, start, end)
        
        websocket = self.clients.get(client_id)
        if websocket:
            await self._send_message(websocket, {
                "type": "lock_response",
                "acquired": acquired,
                "start": start,
                "end": end
            })
    
    async def _handle_lock_release(self, client_id: str, document_id: str, data: Dict):
        """Handle section lock release."""
        start = data.get("start")
        end = data.get("end")
        
        await self.manager.release_lock(client_id, document_id, start, end)
    
    async def _handle_ping(self, client_id: str, document_id: str, data: Dict):
        """Handle ping message."""
        websocket = self.clients.get(client_id)
        if websocket:
            await self._send_message(websocket, {"type": "pong"})
    
    async def _broadcast_to_document(self, document_id: str, message: Dict, exclude: str = None):
        """Broadcast message to all clients in a document."""
        if document_id not in self.manager.connections:
            return
        
        data = json.dumps(message)
        
        for user_id, websocket in self.manager.connections[document_id].items():
            if user_id != exclude:
                try:
                    await websocket.send(data)
                except Exception:
                    pass
    
    async def _send_message(self, websocket, message: Dict):
        """Send message to a client."""
        try:
            await websocket.send(json.dumps(message))
        except Exception:
            pass
    
    async def _send_error(self, websocket, error: str):
        """Send error message to client."""
        await self._send_message(websocket, {
            "type": "error",
            "message": error
        })
    
    def _authenticate(self, data: Dict) -> bool:
        """Authenticate a client connection."""
        if self.auth_callback:
            return self.auth_callback(data)
        
        return bool(data.get("token"))
