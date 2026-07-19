#!/usr/bin/env python3
"""
Check if CodeBender is running a local provider proxy server
or if there's a CLI tool available.
"""

import subprocess
import socket
import os

print("=" * 80)
print("CODEBENDER PROVIDER ACCESS METHODS")
print("=" * 80)

# 1. Check for CodeBender CLI
print("\n1. CHECKING FOR CODEBENDER CLI:")
print("-" * 80)
cli_commands = [
    "codebender --help",
    "codebender-cli --help",
    "cb --help",
    "codebender invoke --help",
]

for cmd in cli_commands:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=2)
        if result.returncode == 0 or "codebender" in result.stdout.decode().lower():
            print(f"  FOUND: {cmd}")
            print(f"    Output: {result.stdout.decode()[:200]}")
    except:
        pass

# 2. Check for local HTTP proxy servers (common ports)
print("\n2. CHECKING FOR LOCAL HTTP PROVIDER SERVERS:")
print("-" * 80)
common_ports = [
    8000,  # Django, Flask default
    3000,  # Node.js default
    5000,  # Flask alt
    8080,  # HTTP proxy
    9000,  # Various services
    8888,  # Jupyter, others
    4000,  # Various services
]

for port in common_ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            print(f"  OPEN: localhost:{port}")
            # Try to get info
            try:
                import requests
                resp = requests.get(f"http://localhost:{port}/", timeout=1)
                print(f"    Response: {resp.status_code}")
            except:
                pass
        sock.close()
    except:
        pass

# 3. Check environment for HTTP endpoint hints
print("\n3. CHECKING ENVIRONMENT FOR HTTP ENDPOINTS:")
print("-" * 80)
endpoint_vars = [
    "CODEBENDER_ENDPOINT",
    "CODEBENDER_API_URL",
    "LLM_PROVIDER_URL",
    "BEDROCK_ENDPOINT",
    "API_ENDPOINT",
    "PROVIDER_ENDPOINT",
]

for var in endpoint_vars:
    val = os.getenv(var)
    if val:
        print(f"  {var} = {val}")

# 4. Check if there's a way to invoke providers
print("\n4. CHECKING FOR PROVIDER INVOCATION METHODS:")
print("-" * 80)

# Check if we can import anything related to providers
import sys
import pkgutil

print("  Checking installed packages for provider-related modules...")
provider_modules = []

try:
    import pip._internal.commands.list as list_cmd
    for dist in list_cmd.get_installed_distributions():
        if any(x in dist.project_name.lower() for x in ['provider', 'bedrock', 'agent', 'codebender']):
            print(f"    {dist.project_name} ({dist.version})")
            provider_modules.append(dist.project_name)
except:
    # Fallback: try importing common candidates
    candidates = [
        'provider_client',
        'bedrock_client', 
        'agent_client',
        'codebender',
        'codebender_sdk',
    ]
    for cand in candidates:
        try:
            __import__(cand)
            print(f"    Found: {cand}")
        except ImportError:
            pass

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("""
If CodeBender manages your "claud haiku" profile through the UI, it likely:

1. Stores it in a local config file (e.g., ~/.codebender/profiles.json)
2. Runs a local HTTP server to proxy requests to Bedrock
3. Provides a CLI tool to invoke profiles
4. Injects the profile into environment variables at runtime

Since we found GROQ_API_KEY and OPENAI_API_KEY in the environment, CodeBender
is clearly managing provider credentials. However, Bedrock specifically may need
AWS credentials.

NEXT STEPS:
- Check if CodeBender has an HTTP API you can call
- Check if there's a CLI wrapper you should use
- Look for documentation on the CodeBender web interface
- Check ~/.codebender/ directory for profile configuration
""")
