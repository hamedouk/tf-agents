"""FastAPI application for the Supervisor Agent.

This module initializes the FastAPI application with all endpoints,
dependency injection, exception handlers, and service lifecycle management.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request, status

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


@app.post("/invocations", response_model=InvocationResponse, tags=["Agent"])
async def invoke_agent(
    request: InvocationRequest,
    http_request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
) -> InvocationResponse:
    """
    Process an agent invocation with session management.
    
    Accepts a user prompt and optional session ID. If a session ID is provided,
    the conversation history for that session is used as context. If no session
    ID is provided, a new session is created.
    
    Session management is handled automatically by Strands based on the
    SESSION_MODE configuration (in_memory or agentcore_memory).
    
    Args:
        request: InvocationRequest containing prompt and optional session_id
        agent_service: Injected AgentService instance
        settings: Injected Settings instance
        
    Returns:
        InvocationResponse with agent output, session_id, timestamp, and model info
        
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
