"""WebSocket connection manager — registration, broadcasting, and lifecycle.

The ``ConnectionManager`` maintains an in-process registry of active WebSocket
connections and provides broadcast primitives used by ``LiveService`` (and
other services) to push real-time events to connected clients.

Design notes
------------
- Connections are identified by a unique ``client_id`` (UUID string).
- Each connection optionally subscribes to specific ``match_id`` channels so
  that per-match broadcasts are efficient.
- All public methods are safe to call from any async context; internal state
  is guarded by an ``asyncio.Lock``.
- The manager is a module-level singleton accessed via ``get_manager()`` so
  that services and controllers share the same instance.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from app.schemas.ws_schema import WSEventType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Registry of active WebSocket connections with broadcast helpers.

    Thread-safety is ensured by an internal ``asyncio.Lock``.  The manager
    keeps two indexes:

    * ``_connections`` — ``client_id → WebSocket``
    * ``_match_subscriptions`` — ``match_id → {client_id, …}``
    """

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._match_subscriptions: Dict[int, Set[str]] = {}
        self._lock = asyncio.Lock()

    # ── connection lifecycle ────────────────────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        *,
        client_id: Optional[str] = None,
    ) -> str:
        """Accept a WebSocket connection and register it.

        Parameters
        ----------
        websocket:
            The raw ``WebSocket`` object from FastAPI.
        client_id:
            Optional explicit ID.  When ``None`` a UUID4 is generated.

        Returns
        -------
        str
            The ``client_id`` assigned to this connection.
        """
        await websocket.accept()
        cid = client_id or str(uuid.uuid4())

        async with self._lock:
            self._connections[cid] = websocket

        logger.info(
            "WebSocket client connected: %s (total: %d)",
            cid,
            len(self._connections),
        )
        return cid

    async def disconnect(self, client_id: str) -> None:
        """Remove a client from the registry and clean up subscriptions."""
        async with self._lock:
            self._connections.pop(client_id, None)
            for subscribers in self._match_subscriptions.values():
                subscribers.discard(client_id)
            # Prune empty subscription sets
            self._match_subscriptions = {
                mid: subs
                for mid, subs in self._match_subscriptions.items()
                if subs
            }

        logger.info(
            "WebSocket client disconnected: %s (total: %d)",
            client_id,
            len(self._connections),
        )

    # ── subscription helpers ───────────────────────────────────────────────

    async def subscribe(self, client_id: str, match_id: int) -> None:
        """Subscribe a client to updates for a specific match."""
        async with self._lock:
            if match_id not in self._match_subscriptions:
                self._match_subscriptions[match_id] = set()
            self._match_subscriptions[match_id].add(client_id)

    async def unsubscribe(self, client_id: str, match_id: int) -> None:
        """Remove a client's subscription to a specific match."""
        async with self._lock:
            subs = self._match_subscriptions.get(match_id)
            if subs:
                subs.discard(client_id)

    # ── broadcast primitives ───────────────────────────────────────────────

    async def broadcast(
        self,
        event_type: WSEventType,
        data: Dict[str, Any],
    ) -> None:
        """Send a message to **all** connected clients.

        Payload shape::

            {"event": "<event_type>", "payload": {…}}
        """
        message = json.dumps({"event": event_type.value, "payload": data})
        await self._send_to(list(self._connections.keys()), message)

    async def broadcast_to_match(
        self,
        match_id: int,
        event_type: WSEventType,
        data: Dict[str, Any],
    ) -> None:
        """Send a message only to clients subscribed to *match_id*.

        Falls back to a full broadcast when there are no explicit subscribers
        for the given match (ensures nobody misses an event during early
        connection phase).
        """
        async with self._lock:
            subscribers = list(
                self._match_subscriptions.get(match_id, set())
            )

        if not subscribers:
            # No explicit subscribers yet — broadcast to everyone
            await self.broadcast(event_type, data)
            return

        message = json.dumps({"event": event_type.value, "payload": data})
        await self._send_to(subscribers, message)

    # ── informational helpers ──────────────────────────────────────────────

    async def get_active_count(self) -> int:
        """Return the number of currently connected clients."""
        return len(self._connections)

    async def get_live_initial_payload(self) -> Dict[str, Any]:
        """Build the initial data payload sent to newly connected clients.

        This is a placeholder that will be enriched when the live-service
        integration is wired up.  For now it returns a simple status object
        so clients can verify the connection is alive.
        """
        return {
            "type": "connected",
            "active_connections": len(self._connections),
        }

    # ── internal helpers ───────────────────────────────────────────────────

    async def _send_to(
        self, client_ids: List[str], message: str
    ) -> None:
        """Send a raw JSON string to a list of clients, removing broken ones."""
        stale: List[str] = []

        for cid in client_ids:
            ws = self._connections.get(cid)
            if ws is None:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                logger.warning(
                    "Failed to send to client %s — marking for removal",
                    cid,
                    exc_info=True,
                )
                stale.append(cid)

        # Clean up broken connections
        for cid in stale:
            await self.disconnect(cid)


# ── Module-level singleton ────────────────────────────────────────────────

_manager: Optional[ConnectionManager] = None


def get_manager() -> ConnectionManager:
    """Return the shared ``ConnectionManager`` singleton.

    Lazily created on first access so it works even before the application
    lifespan runs.
    """
    global _manager  # noqa: PLW0603
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
