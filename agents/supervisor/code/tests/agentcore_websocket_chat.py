"""
Interactive WebSocket chat interface for deployed AgentCore runtime.

This script uses the official AgentCore WebSocket API to connect directly
to your deployed agent runtime for real-time streaming communication.
"""

import asyncio
import json
import sys
import argparse
import boto3
import uuid
import time
import websockets
from concurrent.futures import ThreadPoolExecutor

# Import AgentCore runtime client
try:
    from bedrock_agentcore.runtime import AgentCoreRuntimeClient
except ImportError:
    print("❌ bedrock-agentcore package not found.")
    print("Install it with: pip install bedrock-agentcore")
    sys.exit(1)

class AgentCoreWebSocketChat:
    """Interactive WebSocket chat interface for AgentCore runtime."""
    
    def __init__(self, agent_runtime_arn: str, aws_profile: str = "ai", aws_region: str = "us-west-2"):
        self.agent_runtime_arn = agent_runtime_arn
        self.aws_profile = aws_profile
        self.aws_region = aws_region
        self.session_id = str(uuid.uuid4())
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Initialize AgentCore runtime client
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
            self.client = AgentCoreRuntimeClient(region=aws_region, session=session)
        else:
            self.client = AgentCoreRuntimeClient(region=aws_region)
    
    async def send_message(self, websocket, prompt: str):
        """Send message via existing WebSocket connection and stream response."""
        try:
            print("🤖 Agent: ", end="", flush=True)
            start_time = time.perf_counter()
            first_token_time = None
            
            # Send message (try both formats for compatibility)
            message = {"prompt": prompt}
            await websocket.send(json.dumps(message))
            
            # Receive streaming response
            response_complete = False
            timeout_count = 0
            max_timeout = 10  # Maximum number of timeouts before giving up
            
            while not response_complete and timeout_count < max_timeout:
                try:
                    # Wait for response with timeout - increased for agent processing time
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    
                    try:
                        data = json.loads(response)
                        
                        # Handle different event types
                        if "data" in data:
                            # Text chunk from streaming
                            if first_token_time is None:
                                first_token_time = time.perf_counter()
                            print(data["data"], end="", flush=True)
                            
                        elif "output" in data:
                            # Complete response
                            if first_token_time is None:
                                first_token_time = time.perf_counter()
                            response_text = data.get("output", {}).get("response", "")
                            print(response_text, end="", flush=True)
                            response_complete = True
                            
                        elif "error" in data:
                            print(f"\n❌ Error: {data['error']}")
                            response_complete = True
                            
                        # Check if response is complete
                        if data.get("complete") or data.get("result"):
                            response_complete = True
                            
                    except json.JSONDecodeError:
                        # Handle non-JSON responses
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        print(response, end="", flush=True)
                        response_complete = True
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"\n⏰ Timeout {timeout_count}/{max_timeout} - waiting for agent response...")
                    if timeout_count >= max_timeout:
                        print("\n⏰ Response timeout - assuming complete")
                        response_complete = True
                    # Continue waiting for more data
                    
            end_time = time.perf_counter()
            total_latency = (end_time - start_time) * 1000
            ttft = (first_token_time - start_time) * 1000 if first_token_time else total_latency
            
            print(f"\n⏱️  TTFT: {ttft:.0f}ms | Total: {total_latency:.0f}ms")
            
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    def get_user_input(self):
        """Get user input in a separate thread to avoid blocking."""
        try:
            return input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
    
    async def start_chat(self):
        """Start interactive WebSocket chat loop with persistent connection."""
        print("🚀 AgentCore WebSocket Chat Interface")
        print("=" * 60)
        print(f"Runtime ARN: {self.agent_runtime_arn}")
        print(f"Session ID: {self.session_id}")
        print(f"AWS Profile: {self.aws_profile}")
        print(f"AWS Region: {self.aws_region}")
        print("=" * 60)
        print("Type your messages and press Enter.")
        print("Type 'quit', 'exit', or press Ctrl+C to stop.")
        print("=" * 60)
        
        try:
            # Generate WebSocket connection with session
            ws_url, headers = self.client.generate_ws_connection(
                runtime_arn=self.agent_runtime_arn,
                session_id=self.session_id,
                endpoint_name="DEFAULT"
            )
            
            print("🔌 Connecting to WebSocket...")
            
            # Establish persistent WebSocket connection with longer timeout
            async with websockets.connect(
                ws_url, 
                additional_headers=headers,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=10   # Wait 10 seconds for close
            ) as websocket:
                print("✅ Connected! Session maintained across messages.")
                print("💡 Type your message and press Enter (connection will stay alive)\n")
                
                while True:
                    # Get user input with timeout handling
                    try:
                        # Use asyncio.wait_for with timeout to prevent hanging
                        loop = asyncio.get_event_loop()
                        user_input = await asyncio.wait_for(
                            loop.run_in_executor(self.executor, self.get_user_input),
                            timeout=300.0  # 5 minute timeout for user input
                        )
                        
                        if user_input is None:  # EOF or Ctrl+C
                            break
                            
                    except asyncio.TimeoutError:
                        print("\n⏰ No input for 5 minutes, keeping connection alive...")
                        continue
                    except (EOFError, KeyboardInterrupt):
                        break
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    # Skip empty messages
                    if not user_input:
                        continue
                    
                    # Send message via persistent WebSocket
                    await self.send_message(websocket, user_input)
        
        except websockets.exceptions.InvalidStatus as e:
            print(f"❌ WebSocket handshake failed: {e.response.status_code}")
            if hasattr(e.response, 'headers'):
                print(f"Response headers: {dict(e.response.headers)}")
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Connection error: {e}")
        finally:
            self.executor.shutdown(wait=False)
        
        print("\n👋 Chat ended. Goodbye!")

def get_runtime_arn_from_terraform():
    """Try to get the runtime ARN from terraform outputs."""
    try:
        import subprocess
        import os
        
        # Change to terraform directory
        terraform_dir = "../../terraform"
        if os.path.exists(terraform_dir):
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=terraform_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                dev_endpoint_arn = outputs.get("dev_endpoint_arn", {}).get("value")
                if dev_endpoint_arn:
                    # Extract base runtime ARN by removing /runtime-endpoint/DEV suffix
                    # From: arn:aws:bedrock-agentcore:us-west-2:123:runtime/RuntimeId/runtime-endpoint/DEV
                    # To:   arn:aws:bedrock-agentcore:us-west-2:123:runtime/RuntimeId
                    if "/runtime-endpoint/" in dev_endpoint_arn:
                        base_runtime_arn = dev_endpoint_arn.split("/runtime-endpoint/")[0]
                        return base_runtime_arn
                    return dev_endpoint_arn
    except Exception:
        pass
    
    return None

def main():
    """Run the interactive AgentCore WebSocket chat."""
    parser = argparse.ArgumentParser(description="Interactive WebSocket chat with deployed AgentCore runtime")
    parser.add_argument(
        "--runtime-arn", 
        help="AgentCore Runtime ARN (if not provided, will try to get from terraform outputs)"
    )
    parser.add_argument(
        "--profile", 
        default="ai",
        help="AWS profile to use (default: ai)"
    )
    parser.add_argument(
        "--region", 
        default="us-west-2",
        help="AWS region (default: us-west-2)"
    )
    
    args = parser.parse_args()
    
    # Get runtime ARN
    runtime_arn = args.runtime_arn
    if not runtime_arn:
        print("🔍 Trying to get runtime ARN from terraform outputs...")
        runtime_arn = get_runtime_arn_from_terraform()
        
        if not runtime_arn:
            print("❌ Could not find runtime ARN.")
            print("Please provide it manually:")
            print("  python agentcore_websocket_chat.py --runtime-arn 'arn:aws:bedrock-agentcore:...'")
            print("\nOr run 'terraform output' in agents/supervisor/terraform/ to get the dev_endpoint_arn")
            sys.exit(1)
        else:
            print(f"✅ Found runtime ARN: {runtime_arn}")
    
    # Create and start chat
    chat = AgentCoreWebSocketChat(
        agent_runtime_arn=runtime_arn,
        aws_profile=args.profile,
        aws_region=args.region
    )
    
    asyncio.run(chat.start_chat())

if __name__ == "__main__":
    main()