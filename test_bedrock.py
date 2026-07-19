#!/usr/bin/env python3
"""Test actual Bedrock connectivity."""

import json
import boto3
import os

print("Attempting to create Bedrock client...")

try:
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    print(f"SUCCESS: Created Bedrock client: {type(client)}")
    
    # Try a simple invoke
    print("\nAttempting to invoke Claude Haiku...")
    
    response = client.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-06-01",
            "max_tokens": 100,
            "system": "You are a supply chain analyst.",
            "messages": [
                {
                    "role": "user",
                    "content": "What is 2+2?"
                }
            ]
        })
    )
    
    # Read response
    response_text = json.loads(response['body'].read().decode('utf-8'))
    print(f"Response: {response_text}")
    
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Type: {type(e)}")
    
    # Check environment
    print("\nEnvironment check:")
    print(f"  AWS_ACCESS_KEY_ID: {'SET' if os.getenv('AWS_ACCESS_KEY_ID') else 'NOT SET'}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'SET' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'NOT SET'}")
    print(f"  AWS_REGION: {os.getenv('AWS_REGION', 'NOT SET')}")
