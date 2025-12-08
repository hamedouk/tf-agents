import boto3
import json

session = boto3.session.Session(profile_name='ai', region_name='us-west-2')
client = session.client('bedrock-agentcore')

# Payload format for custom FastAPI agent
payload = json.dumps({"prompt": "Explain machine learning in simple terms"})

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-west-2:730335657558:runtime/SupervisorRuntime-9N8dUUA031',
    runtimeSessionId='dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshek',  # Must be 33+ chars
    payload=payload,
    qualifier="DEFAULT"
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)