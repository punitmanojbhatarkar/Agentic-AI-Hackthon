#!/usr/bin/env python3
"""
Test if localhost:8000 is CodeBender's provider API server.
"""

import requests
import json

print("=" * 80)
print("TESTING LOCALHOST:8000 - CODEBENDER PROVIDER API")
print("=" * 80)

base_url = "http://localhost:8000"

# Try common CodeBender API endpoints
endpoints = [
    "/",
    "/api",
    "/api/providers",
    "/api/profiles",
    "/api/models",
    "/health",
    "/status",
    "/bedrock",
    "/claude",
]

print("\n1. TESTING ENDPOINTS:")
print("-" * 80)

for endpoint in endpoints:
    url = f"{base_url}{endpoint}"
    try:
        resp = requests.get(url, timeout=2)
        print(f"  GET {endpoint}")
        print(f"    Status: {resp.status_code}")
        print(f"    Content-Type: {resp.headers.get('content-type', 'N/A')}")
        if resp.text:
            preview = resp.text[:200] if len(resp.text) > 200 else resp.text
            print(f"    Body: {preview}")
    except Exception as e:
        print(f"  GET {endpoint} - ERROR: {e}")

# Try invoking the Claude Haiku profile specifically
print("\n2. TESTING PROFILE INVOCATION:")
print("-" * 80)

profile_names = [
    "claud haiku",
    "claude-haiku",
    "claude_haiku",
    "haiku",
    "bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0",
]

for profile in profile_names:
    # Try POST to invoke
    url = f"{base_url}/api/invoke"
    payload = {
        "profile": profile,
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=2)
        print(f"\n  Profile: {profile}")
        print(f"    POST {url}")
        print(f"    Status: {resp.status_code}")
        if resp.status_code < 400:
            print(f"    SUCCESS! Response: {resp.json()}")
    except Exception as e:
        print(f"\n  Profile: {profile} - ERROR: {type(e).__name__}")

print("\n" + "=" * 80)
print("FINDINGS:")
print("=" * 80)
