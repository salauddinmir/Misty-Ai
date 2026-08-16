"""
WebSocket Brain Activity Stream.

Provides a WebSocket endpoint at /ws/brain that streams
brain activity events in real-time as JSON messages.

Events include:
- brain_state: Current state snapshot
- processing_start: When a message starts processing
- phase_update: Progress through cognitive phases
- processing_complete: When processing finishes with result
- concept_created: When a new concept is added
- error: When an error occurs
"""

import json
import time as time_module
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from brain.core.brain import Brain


router = APIRouter()

# Track active WebSocket connections
active_connections: Set[WebSocket] = set()


async def broadcast_event(event_type: str, data: Dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSocket clients.

    Args:
        event_type: Type of event (e.g., 'brain_state', 'phase_update').
        data: Event payload data.
    """
    message = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": time_module.time(),
    })

    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception:
            disconnected.add(connection)

    # Clean up disconnected clients
    for conn in disconnected:
        active_connections.discard(conn)


@router.websocket("/ws/brain")
async def brain_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming brain activity.

    Clients connect to receive real-time brain events.
    Clients can also send messages to process through the brain.

    Protocol:
    - Connect: receives initial brain_state event
    - Send {"action": "process", "message": "..."}: processes text
    - Send {"action": "get_state"}: receives current brain state
    - Receive: JSON events with type, data, timestamp fields
    """
    await websocket.accept()
    active_connections.add(websocket)

    brain: Brain = websocket.app.state.brain

    try:
        # Send initial state on connection
        state = brain.get_state()
        await websocket.send_text(json.dumps({
            "type": "brain_state",
            "data": state,
            "timestamp": time_module.time(),
        }))

        # Listen for messages from client
        while True:
            raw_message = await websocket.receive_text()

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                    "timestamp": time_module.time(),
                }))
                continue

            action = message.get("action", "")

            if action == "process":
                # Process a text message through the brain
                text = message.get("message", "")
                if not text:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": "Empty message"},
                        "timestamp": time_module.time(),
                    }))
                    continue

                # Notify processing start
                await broadcast_event("processing_start", {
                    "input": text,
                })

                # Track concepts before processing
                concepts_before = set(brain.concept_graph._concepts.keys())

                # Process through cognitive cycle
                result = brain.process(text)

                # Check for new concepts
                concepts_after = set(brain.concept_graph._concepts.keys())
                new_concepts = concepts_after - concepts_before
                for concept_id in new_concepts:
                    concept = brain.concept_graph.get_concept(concept_id)
                    if concept:
                        await broadcast_event("concept_created", {
                            "concept_id": concept.concept_id,
                            "name": concept.name,
                            "concept_type": concept.concept_type,
                        })

                # Broadcast processing complete
                await broadcast_event("processing_complete", {
                    "response": result["response"],
                    "processing_time": result["processing_time"],
                    "cycle_count": result["cycle_count"],
                    "active_concepts": result["active_concepts"],
                    "emotional_state": result["emotional_state"],
                })

            elif action == "get_state":
                # Return current brain state
                state = brain.get_state()
                await websocket.send_text(json.dumps({
                    "type": "brain_state",
                    "data": state,
                    "timestamp": time_module.time(),
                }))

            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": f"Unknown action: {action}"},
                    "timestamp": time_module.time(),
                }))

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.discard(websocket)
