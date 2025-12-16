"""FastAPI application for the Supervisor Agent.

This module initializes the FastAPI application with all endpoints,
dependency injection, exception handlers, and service lifecycle management.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict
import uuid

import json
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse

from app.config import Settings
from app.exceptions import (
    AgentError,
    ValidationError,
    agent_error_handler,
    validation_error_handler,
    generic_exception_handler,
)
from app.models import HealthResponse, InvocationRequest, InvocationResponse
from app.services import AgentService


# Global service instances
_agent_service: AgentService = None
_settings: Settings = None


def get_settings() -> Settings:
    """Dependency injection for application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_agent_service() -> AgentService:
    """Dependency injection for agent service."""
    global _agent_service
    if _agent_service is None:
        raise RuntimeError("Agent service not initialized")
    return _agent_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for service initialization and cleanup.
    
    Initializes services on startup and performs cleanup on shutdown.
    """
    global _agent_service, _settings
    
    # Startup: Initialize services
    _settings = Settings()
    _agent_service = AgentService(_settings)
    
    yield
    
    # Shutdown: Cleanup (if needed)
    _agent_service = None
    _settings = None


# Initialize FastAPI application
app = FastAPI(
    title="Supervisor Agent",
    version="1.0.0",
    description="Production-ready FastAPI application for AI agent orchestration with conversation history management",
    lifespan=lifespan,
)


# Register exception handlers
app.add_exception_handler(AgentError, agent_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/ping", response_model=HealthResponse, tags=["Health"])
async def ping(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Simple health check endpoint.
    
    Returns a basic health status to verify the service is running.
    This endpoint does not check agent initialization status.
    
    Returns:
        HealthResponse with status "ok" and current timestamp
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.app_version,
    )


@app.get("/ready", response_model=HealthResponse, tags=["Health"])
async def ready(
    agent_service: AgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Readiness check endpoint.
    
    Verifies that the agent service is properly initialized and ready
    to process requests.
    
    Returns:
        HealthResponse with status "ready"
    """
    return HealthResponse(
        status="ready",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.app_version,
    )


@app.get("/debug/sessions", tags=["Debug"])
async def debug_sessions(
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Debug endpoint to check active sessions.
    
    Returns information about currently active agent sessions.
    """
    return agent_service.get_session_info()


@app.post("/invocations", tags=["Agent"])
async def invoke_agent(
    request: InvocationRequest,
    http_request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
):
    """
    Process an agent invocation with optional streaming support.
    
    Supports both regular JSON responses and streaming responses based on headers:
    - Regular response: Default behavior, returns complete JSON response
    - Streaming response: Set Accept header to "text/event-stream" or "application/x-ndjson"
    
    Session management is handled automatically by Strands based on the
    SESSION_MODE configuration (in_memory or agentcore_memory).
    
    Args:
        request: InvocationRequest containing prompt and optional session_id
        http_request: HTTP request with headers for streaming control
        agent_service: Injected AgentService instance
        settings: Injected Settings instance
        
    Returns:
        InvocationResponse (JSON) or StreamingResponse based on Accept header
        
    Raises:
        HTTPException: 400 for validation errors, 500 for agent errors
    """
    # Validate prompt
    if not request.prompt or not request.prompt.strip():
        raise ValidationError(
            message="Prompt is required and cannot be empty",
            details={"field": "prompt"},
        )
    
    # Get session ID with priority:
    # 1. From AgentCore Runtime header (when deployed)
    # 2. From request payload (for direct API calls)
    # 3. Generate new UUID if neither exists
    session_id = (
        http_request.headers.get("X-Amzn-Bedrock-AgentCore-Runtime-Session-Id") or
        request.session_id or
        str(uuid.uuid4())
    )
    
    # Check if streaming is requested via Accept header
    accept_header = http_request.headers.get("accept", "").lower()
    is_streaming = (
        "text/event-stream" in accept_header or 
        "application/x-ndjson" in accept_header or
        http_request.headers.get("x-stream", "").lower() == "true"
    )
    
    if is_streaming:
        # Return streaming response
        async def generate_stream():
            """Generate streaming response."""
            try:
                async for event in agent_service.process_message_stream(
                    prompt=request.prompt,
                    session_id=session_id,
                    actor_id=request.actor_id if hasattr(request, 'actor_id') else None
                ):
                    # Send each event as a JSON line
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except ValidationError:
                # Re-raise validation errors
                raise
            except Exception as e:
                # Send error as final event
                error_event = {
                    "error": str(e),
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    
    else:
        # Return regular JSON response
        try:
            # Process the message - Strands handles session management automatically
            result = agent_service.process_message(
                prompt=request.prompt,
                session_id=session_id,
                actor_id=request.actor_id if hasattr(request, 'actor_id') else None
            )
            
            # Return response
            return InvocationResponse(
                output={"response": result["output"]},
                session_id=result["session_id"],
                timestamp=result["timestamp"],
                model=result["model"],
            )
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Wrap other errors as AgentError
            raise AgentError(
                message="Failed to process agent invocation",
                details={"error": str(e), "session_id": session_id},
            )


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    WebSocket endpoint for real-time agent interaction.
    
    Supports session management via headers (AgentCore style) or message payload.
    Streams back agent events in real-time as JSON messages.
    
    Session ID priority:
    1. User-Agent header (AgentCore format: "AgentRuntime-Client/1.0 (Session: session_id)")
    2. X-Amzn-Bedrock-AgentCore-Runtime-Session-Id header
    3. session_id in message payload
    4. Auto-generated UUID
    
    Message format:
    - Send: {"prompt": "your message"}
    - Receive: {"data": "text chunk", "session_id": "...", "timestamp": "..."}
    """
    # Extract session ID from headers before accepting connection
    session_id = None
    
    # Method 1: Extract from User-Agent header (AgentCore format)
    user_agent = websocket.headers.get("user-agent", "")
    if "Session:" in user_agent:
        try:
            # Format: "AgentRuntime-Client/1.0 (Session: session_id)"
            session_part = user_agent.split("Session:")[1].strip()
            session_id = session_part.rstrip(")")
        except (IndexError, AttributeError):
            pass
    
    # Method 2: Extract from AgentCore session header
    if not session_id:
        session_id = websocket.headers.get("x-amzn-bedrock-agentcore-runtime-session-id")
    
    # Method 3: Extract from custom session header
    if not session_id:
        session_id = websocket.headers.get("x-session-id")
    
    # Method 4: Generate new session ID if none found
    if not session_id:
        session_id = str(uuid.uuid4())
    
    await websocket.accept()
    
    print(f"WebSocket connected with session ID: {session_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                prompt = message.get("prompt")
                
                # Allow session_id override from message (fallback)
                message_session_id = message.get("session_id", session_id)
                
                if not prompt or not prompt.strip():
                    await websocket.send_text(json.dumps({
                        "error": "Prompt is required and cannot be empty",
                        "session_id": message_session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }))
                    continue
                
                # Stream agent response
                async for event in agent_service.process_message_stream(
                    prompt=prompt,
                    session_id=message_session_id
                ):
                    await websocket.send_text(json.dumps(event))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }))
                
    except WebSocketDisconnect:
        pass  # Client disconnected
