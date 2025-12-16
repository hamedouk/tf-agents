"""Service modules for the Supervisor Agent application."""

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional

from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.types.content import SystemContentBlock

from app.config import Settings
from app.tools import calculator, retrieve


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
                print(f"🔄 Creating new agent for session: {session_id}")
            else:
                print(f"♻️  Reusing existing agent for session: {session_id}")
            
            if session_id not in self._agents:
                # Create BedrockModel with configuration from settings
                model_kwargs = {
                    "model_id": self.settings.model_id,
                    "region_name": self.settings.aws_region,
                    "temperature": self.settings.temperature,
                    "max_tokens": self.settings.max_tokens,
                }
                
                # Add AWS profile if specified (for local development)
                if self.settings.aws_profile:
                    model_kwargs["profile_name"] = self.settings.aws_profile
                
                model = BedrockModel(**model_kwargs)
                
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
                    "tools": [retrieve],  # Include retrieve tool for knowledge base access
                    "system_prompt": [
                        SystemContentBlock(
                            text="You are a helpful AI assistant with access to a knowledge base. Use the retrieve tool to search for relevant information when answering questions. Answer directly and concisely based on the retrieved information.",
                        
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
    
    async def process_message_stream(
        self, 
        prompt: str, 
        session_id: str,
        actor_id: Optional[str] = None
    ):
        """
        Process a user message with streaming response.
        
        Args:
            prompt: The user's message/prompt
            session_id: Session ID for conversation history
            actor_id: Optional actor ID for AgentCore Memory (user identifier)
            
        Yields:
            Dictionary containing streaming events and metadata
        """
        # Get or create agent for this session (pass actor_id for AgentCore Memory)
        agent = self.get_or_create_agent(session_id, actor_id)
        
        # Stream agent response - Strands handles conversation history automatically
        async for event in agent.stream_async(prompt):
            # Filter and serialize only JSON-safe event data
            filtered_event = {}
            
            # Add text data if present
            if "data" in event:
                filtered_event["data"] = event["data"]
            
            # Add lifecycle events
            if event.get("init_event_loop", False):
                filtered_event["init_event_loop"] = True
            if event.get("start_event_loop", False):
                filtered_event["start_event_loop"] = True
            if event.get("complete", False):
                filtered_event["complete"] = True
            if event.get("force_stop", False):
                filtered_event["force_stop"] = True
                filtered_event["force_stop_reason"] = event.get("force_stop_reason", "unknown")
            
            # Add tool usage info
            if "current_tool_use" in event and isinstance(event["current_tool_use"], dict):
                tool_use = event["current_tool_use"]
                if tool_use.get("name"):
                    filtered_event["tool_name"] = tool_use["name"]
                if tool_use.get("toolUseId"):
                    filtered_event["tool_use_id"] = tool_use["toolUseId"]
            
            # Add message info if present
            if "message" in event and isinstance(event["message"], dict):
                message = event["message"]
                if message.get("role"):
                    filtered_event["message_role"] = message["role"]
            
            # Add result if present (final response)
            if "result" in event:
                filtered_event["result"] = str(event["result"])
            
            # Add metadata to each event
            filtered_event.update({
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": self.settings.model_id
            })
            
            # Only yield events that have meaningful content
            if any(key in filtered_event for key in ["data", "init_event_loop", "start_event_loop", 
                                                   "complete", "force_stop", "tool_name", "result"]):
                yield filtered_event
    
    def cleanup_session(self, session_id: str) -> None:
        """
        Remove an agent instance for a session to free memory.
        
        Args:
            session_id: The session identifier to cleanup
        """
        with self._lock:
            if session_id in self._agents:
                print(f"🗑️  Cleaning up session: {session_id}")
                del self._agents[session_id]
    
    def get_session_info(self) -> dict:
        """Get information about active sessions."""
        with self._lock:
            return {
                "active_sessions": len(self._agents),
                "session_ids": list(self._agents.keys())
            }
