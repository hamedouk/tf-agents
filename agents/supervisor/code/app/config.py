"""Configuration module for the Supervisor Agent application."""

from typing import Literal, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    app_name: str = "Supervisor Agent"
    app_version: str = "1.0.0"
    
    # Model configuration
    model_id: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"  # Much faster than Sonnet
    temperature: float = 0.1
    max_tokens: int = 512  # Reduced for sub-1s latency
    aws_region: str = "us-west-2"
    aws_profile: Optional[str] = None
    
    # Session management configuration
    session_mode: Literal["in_memory", "agentcore_memory"] = "in_memory"
    conversation_window_size: int = 20  # Increased to remember more conversation history
    
    # AgentCore Memory configuration (only used when session_mode="agentcore_memory")
    agentcore_memory_id: Optional[str] = None
    agentcore_memory_region: Optional[str] = None
    
    # Knowledge Base configuration
    knowledge_base_id: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
