"""Data models for the Supervisor Agent application."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InvocationRequest(BaseModel):
    """Request model for agent invocation."""
    
    prompt: str = Field(..., description="The user's prompt to send to the agent")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation history")
    actor_id: Optional[str] = Field(None, description="Optional actor/user ID for AgentCore Memory")


class InvocationResponse(BaseModel):
    """Response model for agent invocation."""
    
    output: Dict[str, Any] = Field(..., description="The agent's response output")
    session_id: str = Field(..., description="The session ID for this conversation")
    timestamp: str = Field(..., description="ISO format timestamp of the response")
    model: str = Field(..., description="The model used for the response")


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    
    status: str = Field(..., description="Health status of the service")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: Optional[str] = Field(None, description="Application version")
