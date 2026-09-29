from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # We store active connections categorized by role and ID
        # e.g., {"VENDOR": {"store_1": [websocket1, websocket2]}, "RIDER": [websocket1, ...]}
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {
            "VENDOR": {},
            "RIDER": {"available": []}
        }

    async def connect_vendor(self, websocket: WebSocket, store_id: str):
        await websocket.accept()
        if store_id not in self.active_connections["VENDOR"]:
            self.active_connections["VENDOR"][store_id] = []
        self.active_connections["VENDOR"][store_id].append(websocket)

    async def connect_rider(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections["RIDER"]["available"].append(websocket)

    def disconnect_vendor(self, websocket: WebSocket, store_id: str):
        if store_id in self.active_connections["VENDOR"]:
            self.active_connections["VENDOR"][store_id].remove(websocket)

    def disconnect_rider(self, websocket: WebSocket):
        if websocket in self.active_connections["RIDER"]["available"]:
            self.active_connections["RIDER"]["available"].remove(websocket)

    async def alert_vendor(self, store_id: str, message: dict):
        """Pings the specific store that an order has been paid and needs packing."""
        if store_id in self.active_connections["VENDOR"]:
            for connection in self.active_connections["VENDOR"][store_id]:
                await connection.send_text(json.dumps(message))

    async def broadcast_to_riders(self, message: dict):
        """Pings all available riders in the area to trigger the 'Claim' race."""
        for connection in self.active_connections["RIDER"]["available"]:
            await connection.send_text(json.dumps(message))

# Instantiate a global manager to be used across the app
manager = ConnectionManager()