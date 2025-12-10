"""Service modules for the Supervisor Agent application."""

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional

from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.types.content import SystemContentBlock

from app.config import Settings
from app.tools import calculator


class AgentService:
    """Manages Strands Agent lifecycle and interactions."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the agent service.
        
        Args:
            settings: Application settings containing model configuration
        """
        self.settings = settings
        self._agents: Dict[str, Agent] = {}  # One agent per session
        self._lock = Lock()
    
    def _create_session_manager(self, session_id: str, actor_id: Optional[str] = None):
        """
        Create appropriate session manager based on configuration.
        
        Args:
            session_id: The session identifier
            actor_id: Optional actor/user identifier for AgentCore Memory
            
        Returns:
            Session manager instance or None for in-memory mode
        """
        if self.settings.session_mode == "agentcore_memory":
            # Import here to avoid dependency if not using AgentCore Memory
            from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
            from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
            
            if not self.settings.agentcore_memory_id:
                raise ValueError("agentcore_memory_id is required when session_mode is 'agentcore_memory'")
            
            # Create AgentCore Memory configuration
            config = AgentCoreMemoryConfig(
                memory_id=self.settings.agentcore_memory_id,
                session_id=session_id,
                actor_id=actor_id or "default_user",
            )
            
            return AgentCoreMemorySessionManager(
                agentcore_memory_config=config,
                region_name=self.settings.agentcore_memory_region or self.settings.aws_region
            )
        else:
            # No session manager for in-memory mode
            # Strands will maintain conversation in memory automatically
            return None
    
    def get_or_create_agent(self, session_id: str, actor_id: Optional[str] = None) -> Agent:
        """
        Get or create an agent for the given session.
        
        Args:
            session_id: The session identifier
            actor_id: Optional actor/user identifier for AgentCore Memory
            
        Returns:
            Agent instance configured for the session
        """
        with self._lock:
            if session_id not in self._agents:
                # Create BedrockModel with configuration from settings
                model = BedrockModel(
                    model_id=self.settings.model_id,
                    region_name=self.settings.aws_region,
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                )
                
                # Create conversation manager for automatic history trimming
                conversation_manager = SlidingWindowConversationManager(
                    window_size=self.settings.conversation_window_size,
                    should_truncate_results=True
                )
                
                # Create session manager based on configuration
                session_manager = self._create_session_manager(session_id, actor_id)
                
                # Create agent with tools and session management
                # Use SystemContentBlock with cachePoint for prompt caching
                agent_kwargs = {
                    "model": model,
                    "tools": [],  # No tools for maximum performance
                    "system_prompt": [
                        SystemContentBlock(
                            text="You are a concise AI assistant. Answer directly and briefly.",
                        
                        ),
                        SystemContentBlock(cachePoint= {"type": "default"})
                    ],
                    "conversation_manager": conversation_manager,
                }
                
                # Only add session_manager if not None (in-memory mode doesn't need it)
                if session_manager is not None:
                    agent_kwargs["session_manager"] = session_manager
                
                self._agents[session_id] = Agent(**agent_kwargs)
            
            return self._agents[session_id]
    
    def process_message(
        self, 
        prompt: str, 
        session_id: str,
        actor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with conversation context.
        
        Args:
            prompt: The user's message/prompt
            session_id: Session ID for conversation history
            actor_id: Optional actor ID for AgentCore Memory (user identifier)
            
        Returns:
            Dictionary containing the agent's response and metadata
        """
        # Get or create agent for this session (pass actor_id for AgentCore Memory)
        agent = self.get_or_create_agent(session_id, actor_id)
        
        # Execute agent - Strands handles conversation history automatically
        response = agent(prompt)
        
        return {
            "output": str(response),
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.settings.model_id
        }
    
    def cleanup_session(self, session_id: str) -> None:
        """
        Remove an agent instance for a session to free memory.
        
        Args:
            session_id: The session identifier to cleanup
        """
        with self._lock:
            if session_id in self._agents:
                del self._agents[session_id]
