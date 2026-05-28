"""WebSocket endpoint — /ws/live real-time event stream.

Provides a single WebSocket route that clients connect to in order to receive
live match updates (score changes, match start/end, activity level, bracket
updates).

Lifecycle
---------
1. Client connects → ``ConnectionManager.connect()`` registers the socket.
2. Server sends an initial payload with current live match state.
3. A background task sends periodic ``ping`` frames to keep the connection
   alive; the client is expected to respond with ``pong`` (handled by most
   WebSocket libraries automatically).
4. Incoming client messages are handled — currently only ``subscribe`` (to
   follow a specific match) is recognised; anything else is ignored.
5. When the client disconnects (or the connection drops) the manager cleans
   up automatically.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.redis.client import get_redis
from app.services.live_service import LiveService
from app.services.websocket_manager import get_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# ── Constants ──────────────────────────────────────────────────────────────

_PING_INTERVAL: float = 30.0  # seconds between keep-alive pings


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for live match event streaming.

    Protocol
    --------
    * On connect the server sends::

          {"event": "connected", "payload": {"active_connections": N}}

    * The server pushes real-time events as they happen::

          {"event": "score_update", "payload": {…}}

    * Clients may send::

          {"action": "subscribe", "matchId": 42}
          {"action": "unsubscribe", "matchId": 42}

    * Keep-alive is maintained by periodic ``ping`` frames from the server.
    """
    manager = get_manager()
    client_id: Optional[str] = None

    try:
        client_id = await manager.connect(websocket)

        # ── Send initial payload ────────────────────────────────────────
        initial = await _build_initial_payload()
        await websocket.send_text(
            json.dumps(
                {
                    "event": "connected",
                    "payload": initial,
                }
            )
        )

        # ── Start keep-alive ping loop ──────────────────────────────────
        ping_task = asyncio.create_task(
            _ping_loop(websocket, client_id)
        )

        # ── Message receive loop ────────────────────────────────────────
        try:
            while True:
                raw = await websocket.receive_text()
                await _handle_client_message(client_id, raw)
        except WebSocketDisconnect:
            logger.info(
                "Client %s sent WebSocket disconnect", client_id
            )
        finally:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass

    except Exception:
        logger.error(
            "Unexpected error in WebSocket handler for client %s",
            client_id,
            exc_info=True,
        )
    finally:
        if client_id is not None:
            await manager.disconnect(client_id)


# ── Helper functions ──────────────────────────────────────────────────────


async def _build_initial_payload() -> Dict[str, Any]:
    """Collect initial data to send immediately after connection.

    Includes the current list of live matches (if any) so the client can
    render them without waiting for the next broadcast cycle.
    """
    redis = get_redis()
    live_svc = LiveService(redis=redis)
    live_matches = await live_svc.get_live_matches()

    manager = get_manager()
    active = await manager.get_active_count()

    return {
        "active_connections": active,
        "live_matches": live_matches,
    }


async def _handle_client_message(
    client_id: str, raw: str
) -> None:
    """Parse and dispatch a single inbound message from a client."""
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(
            "Invalid JSON from client %s: %s", client_id, raw[:200]
        )
        return

    action = msg.get("action")
    manager = get_manager()

    if action == "subscribe" and "matchId" in msg:
        match_id = int(msg["matchId"])
        await manager.subscribe(client_id, match_id)
        logger.debug("Client %s subscribed to match %d", client_id, match_id)

    elif action == "unsubscribe" and "matchId" in msg:
        match_id = int(msg["matchId"])
        await manager.unsubscribe(client_id, match_id)
        logger.debug(
            "Client %s unsubscribed from match %d", client_id, match_id
        )

    else:
        logger.debug(
            "Unknown action from client %s: %s", client_id, action
        )


async def _ping_loop(websocket: WebSocket, client_id: str) -> None:
    """Periodically send ping frames to keep the connection alive."""
    try:
        while True:
            await asyncio.sleep(_PING_INTERVAL)
            await websocket.send_json({"event": "ping"})
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.debug(
            "Ping loop ended for client %s (connection likely closed)",
            client_id,
        )
