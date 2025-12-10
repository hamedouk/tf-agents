"""Custom tools for the Supervisor Agent.

This module defines custom tools that can be used by the Strands Agent,
as well as imports community tools from the strands-agents-tools package.
"""

from datetime import datetime, timezone
from strands import tool
from strands.types.tools import ToolUse, ToolResult

# Import community tools from strands-agents-tools
from strands_tools.calculator import calculator
from strands_tools import http_request
from strands_tools.retrieve import retrieve as _retrieve_base


@tool
def get_current_time() -> str:
    """Get the current UTC date and time.
    
    Returns the current date and time in ISO 8601 format (UTC timezone).
    Useful for timestamping events, scheduling tasks, or providing
    time-aware responses.
    
    Returns:
        A string containing the current UTC timestamp in ISO 8601 format
        (e.g., "2024-12-08T15:30:45.123456+00:00")
    """
    return datetime.now(timezone.utc).isoformat()


@tool
def retrieve(tool: ToolUse, **kwargs) -> ToolResult:
    """Retrieve relevant knowledge from Amazon Bedrock Knowledge Base.
    
    This tool searches your knowledge base for information relevant to the query.
    Optimized for fast retrieval with a limited number of high-quality results.
    
    Args:
        tool: Tool use information containing:
            text: The query text to search for
            numberOfResults: Maximum results to return (default: 3, max: 10)
            score: Minimum relevance score threshold (default: 0.4)
    
    Returns:
        Retrieved results from the knowledge base sorted by relevance
    """
    # Override numberOfResults to optimize latency (default to 3 instead of 10)
    if hasattr(tool, 'input') and isinstance(tool.input, dict):
        if 'numberOfResults' not in tool.input:
            tool.input['numberOfResults'] = 3
        else:
            # Cap at 5 for performance
            tool.input['numberOfResults'] = min(tool.input['numberOfResults'], 5)
    
    return _retrieve_base(tool, **kwargs)


# Export all tools for easy import
__all__ = ["get_current_time", "calculator", "http_request", "retrieve"]
