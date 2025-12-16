"""
Interactive WebSocket chat interface with latency metrics.
"""

import asyncio
import json
import sys
import time
import websockets
import uuid
from concurrent.futures import ThreadPoolExecutor

class WebSocketChat:
    """Interactive chat interface using WebSocket streaming."""
    
    def __init__(self, websocket_url="ws://localhost:8080/ws"):
        self.websocket_url = websocket_url
        self.session_id = str(uuid.uuid4())
        self.websocket = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    async def send_message(self, prompt: str):
        """Send message and stream response with latency metrics."""
        if not self.websocket:
            print("❌ Not connected to WebSocket")
            return
            
        message = {
            "prompt": prompt,
            "session_id": self.session_id
        }
        
        try:
            # Start timing
            start_time = time.time()
            ttft_time = None
            first_token_received = False
            
            # Send message
            await self.websocket.send(json.dumps(message))
            
            # Print agent response prefix
            print("🤖 Agent: ", end="", flush=True)
            
            # Stream and display response
            async for message in self.websocket:
                try:
                    event_data = json.loads(message)
                    
                    # Record TTFT on first data token
                    if "data" in event_data and not first_token_received:
                        ttft_time = time.time() - start_time
                        first_token_received = True
                    
                    # Only print text data
                    if "data" in event_data:
                        print(event_data["data"], end="", flush=True)
                    
                    # Handle completion
                    if "result" in event_data:
                        total_time = time.time() - start_time
                        print()  # New line after complete response
                        
                        # Display latency metrics
                        if ttft_time is not None:
                            print(f"⏱️  TTFT: {ttft_time:.3f}s | Total: {total_time:.3f}s")
                        else:
                            print(f"⏱️  Total: {total_time:.3f}s")
                        break
                    
                    # Handle errors
                    if "error" in event_data:
                        total_time = time.time() - start_time
                        print(f"\n❌ Error: {event_data['error']}")
                        print(f"⏱️  Total: {total_time:.3f}s")
                        break
                        
                except json.JSONDecodeError:
                    pass  # Skip malformed JSON
        
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed")
            self.websocket = None
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def get_user_input(self):
        """Get user input in a separate thread to avoid blocking."""
        try:
            return input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
    
    async def start_chat(self):
        """Start interactive chat loop."""
        print("🚀 WebSocket Chat Interface")
        print("=" * 50)
        print("Type your messages and press Enter.")
        print("Type 'quit', 'exit', or press Ctrl+C to stop.")
        print("=" * 50)
        
        try:
            # Connect to WebSocket
            print("🔌 Connecting to WebSocket...")
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                print("✅ Connected!")
                
                while True:
                    # Get user input
                    try:
                        loop = asyncio.get_event_loop()
                        user_input = await loop.run_in_executor(
                            self.executor, self.get_user_input
                        )
                        
                        if user_input is None:  # EOF or Ctrl+C
                            break
                            
                    except (EOFError, KeyboardInterrupt):
                        break
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    # Skip empty messages
                    if not user_input:
                        continue
                    
                    # Send message and stream response
                    await self.send_message(user_input)
        
        except websockets.exceptions.ConnectionRefused:
            print("❌ Could not connect to WebSocket server.")
            print("   Make sure the agent is running at ws://localhost:8080/ws")
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Connection error: {e}")
        finally:
            self.websocket = None
            self.executor.shutdown(wait=False)
        
        print("\n👋 Chat ended. Goodbye!")

async def main():
    """Run the interactive WebSocket chat."""
    chat = WebSocketChat()
    await chat.start_chat()

if __name__ == "__main__":
    asyncio.run(main())