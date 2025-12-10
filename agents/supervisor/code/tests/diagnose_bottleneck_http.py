"""
Diagnose where the latency is coming from for HTTP endpoint queries.
Similar to diagnose_bottleneck.py but for HTTP endpoint testing.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
AGENT_URL = "http://localhost:64376"
SESSION_ID_PREFIX = "http-diag-session-"

print("="*80)
print("DIAGNOSING HTTP ENDPOINT LATENCY BOTTLENECK")
print("="*80)

# Setup session with timeout
session = requests.Session()
session.timeout = 30

def test_connection():
    """Test if the agent is reachable."""
    print(f"\n🔍 Testing connection to {AGENT_URL}...")
    try:
        response = session.get(f"{AGENT_URL}/", timeout=5)
        print(f"✓ Connection successful (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection failed: {e}")
        print(f"  Make sure the agent is running at {AGENT_URL}")
        return False

# Test connection first
if not test_connection():
    print("\n⚠ Cannot proceed without connection. Exiting.")
    exit(1)

# Test 1: Multiple simple queries to check for cold start
print("\n1. Testing for cold start (running 4 queries in sequence)")
print("-"*80)

session_id = f"{SESSION_ID_PREFIX}{int(time.time())}"

# Test different query types
queries = [
    ("Hi", "greeting"),
    ("What is the capital of Tunisia?", "simple_fact"),
    ("Tell me a poem", "creative"),
    ("Explain LLM for me", "fact"),
    ("137+5-9", "math_tool"),
]

for i, (query, qtype) in enumerate(queries, 1):
    payload = {
        "prompt": query,
        "session_id": session_id
    }
    
    start = time.perf_counter()
    try:
        response = session.post(
            f"{AGENT_URL}/invocations",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        end = time.perf_counter()
        
        latency = (end - start) * 1000
        
        if response.status_code == 200:
            response_data = response.json()
            answer = str(response_data)[:60]
            status = "✓"
        else:
            answer = f"HTTP {response.status_code}: {response.text[:60]}"
            status = "✗"
        
        print(f"Query {i} [{qtype:15s}] '{query:40s}': {latency:7.2f}ms {status}")
        print(f"         Response: {answer}...")
        
    except requests.exceptions.RequestException as e:
        end = time.perf_counter()
        latency = (end - start) * 1000
        print(f"Query {i} [{qtype:15s}] '{query:40s}': {latency:7.2f}ms ✗")
        print(f"         Error: {str(e)[:60]}...")
    
    time.sleep(0.5)

print("\n📊 Analysis:")
print("  - If 1st query is much slower: Cold start issue")
print("  - If greeting/math faster than kb_retrieval: Knowledge base overhead")
print("  - If all similar (~2-3s): LLM inference is the bottleneck")
print("  - If HTTP errors: Check agent configuration/deployment")

# Test 2: Check response structure and timing breakdown
print("\n2. Detailed response analysis")
print("-"*80)

payload = {
    "prompt": "hello",
    "session_id": session_id
}

start = time.perf_counter()
try:
    response = session.post(
        f"{AGENT_URL}/invocations",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    end = time.perf_counter()
    
    latency = (end - start) * 1000
    
    print(f"Total HTTP latency: {latency:.2f}ms")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"\nResponse structure:")
        print(json.dumps(response_data, indent=2, default=str)[:500])
        
        # Check for timing information in response
        if 'metadata' in response_data:
            print(f"\nMetadata found: {response_data['metadata']}")
        if 'processing_time' in response_data:
            print(f"Processing time: {response_data['processing_time']}")
    else:
        print(f"Error response: {response.text}")
        
except requests.exceptions.RequestException as e:
    end = time.perf_counter()
    latency = (end - start) * 1000
    print(f"Request failed after {latency:.2f}ms: {e}")

# Test 3: Compare different session IDs (session overhead)
print("\n3. Testing session overhead")
print("-"*80)

# Same session
start = time.perf_counter()
try:
    response1 = session.post(
        f"{AGENT_URL}/invocations",
        json={"prompt": "test 1", "session_id": session_id}
    )
    end = time.perf_counter()
    same_session_latency = (end - start) * 1000
    print(f"Same session query: {same_session_latency:.2f}ms")
except Exception as e:
    print(f"Same session failed: {e}")

time.sleep(0.5)

# New session
new_session_id = f"{SESSION_ID_PREFIX}{int(time.time())}-new"
start = time.perf_counter()
try:
    response2 = session.post(
        f"{AGENT_URL}/invocations",
        json={"prompt": "test 2", "session_id": new_session_id}
    )
    end = time.perf_counter()
    new_session_latency = (end - start) * 1000
    print(f"New session query: {new_session_latency:.2f}ms")
except Exception as e:
    print(f"New session failed: {e}")

# Test 4: Network vs processing time estimation
print("\n4. Network latency estimation")
print("-"*80)

# Simple health check to estimate network latency
network_times = []
for i in range(3):
    start = time.perf_counter()
    try:
        response = session.get(f"{AGENT_URL}/", timeout=5)
        end = time.perf_counter()
        network_time = (end - start) * 1000
        network_times.append(network_time)
        print(f"Health check {i+1}: {network_time:.2f}ms")
    except Exception as e:
        print(f"Health check {i+1} failed: {e}")
    time.sleep(0.2)

if network_times:
    avg_network = sum(network_times) / len(network_times)
    print(f"Average network latency: {avg_network:.2f}ms")
else:
    avg_network = 0
    print("Could not measure network latency")

print("\n" + "="*80)
print("HTTP ENDPOINT DIAGNOSIS SUMMARY")
print("="*80)
print(f"""
Agent URL: {AGENT_URL}

If latency is still high for simple queries:

1. AGENT NOT RUNNING (most common)
   - Check if agent is running on port 64376
   - Solution: Start the agent with 'python -m app.main'

2. COLD START
   - First query much slower than subsequent ones
   - Solution: Keep agent warm with periodic requests

3. KNOWLEDGE BASE OVERHEAD
   - KB queries much slower than simple math/greetings
   - Solution: Optimize vector search or caching

4. NETWORK LATENCY
   - High baseline network time (>{avg_network:.1f}ms measured)
   - Solution: Run agent locally or optimize network

5. HTTP PROCESSING OVERHEAD
   - Compare with boto3 results from diagnose_bottleneck.py
   - HTTP should be faster than AgentCore runtime

Next steps:
1. Check agent logs for detailed processing times
2. Compare with diagnose_bottleneck.py (boto3) results
3. Monitor CPU/memory usage during requests
4. Check if agent is using correct model/configuration
""")