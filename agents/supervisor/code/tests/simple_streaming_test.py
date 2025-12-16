"""
Interactive chat interface with configurable response mode.
"""

import asyncio
import json
import sys
import argparse
import aiohttp
import uuid

class InteractiveChat:
    """Interactive chat interface supporting both streaming and regular modes."""
    
    def __init__(self, base_url="http://localhost:8080", mode="streaming"):
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())
        self.mode = mode
        
    async def send_message_streaming(self, prompt: str):
        """Send message and stream response."""
        payload = {
            "prompt": prompt,
            "session_id": self.session_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/invocations",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    }
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ Error: HTTP {response.status} - {error_text}")
                        return
                    
                    # Print agent response prefix
                    print("🤖 Agent: ", end="", flush=True)
                    
                    # Stream and display response
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                try:
                                    event_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                                    
                                    # Only print text data
                                    if "data" in event_data:
                                        print(event_data["data"], end="", flush=True)
                                    
                                    # Handle completion
                                    if "result" in event_data:
                                        print()  # New line after complete response
                                        break
                                        
                                except json.JSONDecodeError:
                                    pass  # Skip malformed JSON
        
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    async def send_message_regular(self, prompt: str):
        """Send message and get regular JSON response."""
        payload = {
            "prompt": prompt,
            "session_id": self.session_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/invocations",
                    json=payload,
                    headers={"Content-Type": "application/json"}  # No streaming headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ Error: HTTP {response.status} - {error_text}")
                        return
                    
                    result = await response.json()
                    response_text = result.get("output", {}).get("response", "")
                    
                    # Print complete response at once
                    print(f"🤖 Agent: {response_text}")
        
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    async def send_message(self, prompt: str):
        """Send message using the configured mode."""
        if self.mode == "streaming":
            await self.send_message_streaming(prompt)
        else:
            await self.send_message_regular(prompt)
    
    async def start_chat(self):
        """Start interactive chat loop."""
        mode_emoji = "🌊" if self.mode == "streaming" else "📋"
        print(f"{mode_emoji} Interactive Chat Interface ({self.mode.upper()} mode)")
        print("=" * 60)
        print("Type your messages and press Enter.")
        print("Type 'quit', 'exit', or press Ctrl+C to stop.")
        print("=" * 60)
        
        try:
            while True:
                # Get user input
                try:
                    user_input = input("\n👤 You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Skip empty messages
                if not user_input:
                    continue
                
                # Send message using configured mode
                await self.send_message(user_input)
        
        except KeyboardInterrupt:
            pass
        
        print("\n👋 Chat ended. Goodbye!")

def main():
    """Run the interactive chat with command line arguments."""
    parser = argparse.ArgumentParser(description="Interactive chat with configurable response mode")
    parser.add_argument(
        "--mode", 
        choices=["streaming", "regular"], 
        default="streaming",
        help="Response mode: 'streaming' for real-time streaming, 'regular' for complete JSON response (default: streaming)"
    )
    parser.add_argument(
        "--url", 
        default="http://localhost:8080",
        help="Base URL of the agent service (default: http://localhost:8080)"
    )
    
    args = parser.parse_args()
    
    chat = InteractiveChat(base_url=args.url, mode=args.mode)
    asyncio.run(chat.start_chat())

if __name__ == "__main__":
    main()