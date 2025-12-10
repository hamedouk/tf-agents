"""
Diagnose where the 4s latency is coming from for simple queries.
"""

import boto3
import json
import time

PROFILE_NAME = 'ai'
REGION = 'us-west-2'
AGENT_RUNTIME_ARN = 'arn:aws:bedrock-agentcore:us-west-2:730335657558:runtime/SupervisorRuntime-9N8dUUA031'

session = boto3.session.Session(profile_name=PROFILE_NAME, region_name=REGION)
client = session.client('bedrock-agentcore')

print("="*80)
print("DIAGNOSING LATENCY BOTTLENECK")
print("="*80)

# Test 1: Multiple simple queries to check for cold start
print("\n1. Testing for cold start (running 3 simple queries in sequence)")
print("-"*80)

session_id = f"diag-test-session-{int(time.time())}-extra-chars"

# Test different query types
queries = [
    ("Hi", "greeting"),
    ("What is the capital of Tunisia?", "simple_fact"),
    ("Tell me a poem", "creative"),
    ("Explain LLM for me", "fact"),
    ("137+5-9", "math_tool"),
]

for i, (query, qtype) in enumerate(queries, 1):
    payload = json.dumps({"prompt": query})
    
    start = time.perf_counter()
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=payload,
        qualifier="DEFAULT"
    )
    response_body = response['response'].read()
    end = time.perf_counter()
    
    latency = (end - start) * 1000
    response_data = json.loads(response_body)
    answer = response_data.get('output', {}).get('response', 'N/A')[:60]
    
    print(f"Query {i} [{qtype:15s}] '{query:40s}': {latency:7.2f}ms")
    print(f"         Response: {answer}...")
    
    time.sleep(0.5)

print("\n📊 Analysis:")
print("  - If 1st query is much slower: Cold start issue")
print("  - If simple_fact/greeting faster than math_tool: Tool overhead")
print("  - If all similar (~2-3s): LLM inference is the bottleneck")

# Test 2: Check response metadata
print("\n2. Checking response metadata")
print("-"*80)

payload = json.dumps({"prompt": "hello"})
start = time.perf_counter()
response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_RUNTIME_ARN,
    runtimeSessionId=session_id,
    payload=payload,
    qualifier="DEFAULT"
)
response_body = response['response'].read()
end = time.perf_counter()

response_data = json.loads(response_body)
latency = (end - start) * 1000

print(f"Total latency: {latency:.2f}ms")
print(f"\nResponse structure:")
print(json.dumps(response_data, indent=2, default=str)[:500])

# Test 3: Check what model is actually being used
print("\n3. Checking deployed model configuration")
print("-"*80)
print("Model from response:", response_data.get('model', 'Not in response'))

print("\n" + "="*80)
print("DIAGNOSIS SUMMARY")
print("="*80)
print("""
If latency is still ~4s for simple queries:

1. COLD START (most likely)
   - Container takes time to initialize
   - Solution: Enable provisioned concurrency
   
2. MODEL NOT UPDATED
   - Code changes not deployed
   - Solution: Run terraform apply
   
3. NETWORK LATENCY
   - High latency to AWS
   - Solution: Check AWS region, use VPC endpoints

4. AGENTCORE OVERHEAD
   - AgentCore runtime adds processing time
   - Solution: Consider direct Lambda deployment

Next step: Check CloudWatch logs for actual model being used
""")
