#!/usr/bin/env python3
"""
Deep inspection of CodeBender's provider system.
Looking for any hints in the Python environment about how to access saved profiles.
"""

import os
import sys
import json

print("=" * 80)
print("CODEBENDER PROVIDER SYSTEM INSPECTION")
print("=" * 80)

# 1. Check ALL environment variables for clues
print("\n1. ALL ENVIRONMENT VARIABLES CONTAINING 'PROVIDER', 'BEDROCK', 'LLM', 'API':")
print("-" * 80)
relevant_vars = {k: v for k, v in os.environ.items() 
                 if any(x in k.upper() for x in ['PROVIDER', 'BEDROCK', 'LLM', 'API', 'CLAUDE', 'PROFILE', 'CODEBENDER'])}

if relevant_vars:
    for k, v in sorted(relevant_vars.items()):
        # Truncate long values
        v_display = v[:100] + "..." if len(v) > 100 else v
        print(f"  {k} = {v_display}")
else:
    print("  (none found)")

# 2. List ALL environment variables
print("\n2. ALL ENVIRONMENT VARIABLES:")
print("-" * 80)
all_vars = sorted(os.environ.keys())
for var in all_vars:
    print(f"  {var}")

# 3. Check if there's a CODEBENDER_PROFILE environment variable
print("\n3. CHECKING FOR PROFILE NAME ENV VAR:")
print("-" * 80)
profile_name = os.getenv("CODEBENDER_PROFILE")
if profile_name:
    print(f"  Found profile name: {profile_name}")
else:
    print("  CODEBENDER_PROFILE not set")

# 4. Look in common paths for config files
print("\n4. CHECKING FOR CONFIG FILES:")
print("-" * 80)
config_paths = [
    os.path.expanduser("~/.codebender"),
    os.path.expanduser("~/.codebender/config.json"),
    os.path.expanduser("~/.codebender/profiles.json"),
    "/etc/codebender/config.json",
    "./.codebender",
    "./.codebender/config.json",
]

for path in config_paths:
    if os.path.exists(path):
        print(f"  Found: {path}")
        if os.path.isfile(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                print(f"    Content preview: {content[:200]}...")
            except Exception as e:
                print(f"    Error reading: {e}")

# 5. Check /proc or /sys for process environment (Linux only)
print("\n5. CHECKING PARENT PROCESS INFO:")
print("-" * 80)
try:
    with open(f"/proc/{os.getpid()}/environ", "r") as f:
        proc_env = f.read().split('\x00')
        provider_env = [e for e in proc_env if any(x in e for x in ['PROVIDER', 'BEDROCK', 'PROFILE', 'CODEBENDER'])]
        if provider_env:
            for e in provider_env:
                print(f"  {e}")
        else:
            print("  (no relevant vars in /proc)")
except:
    print("  (not on Linux or cannot read /proc)")

print("\n" + "=" * 80)
print("FINDINGS:")
print("=" * 80)
print("""
If CodeBender is managing your provider profile "claud haiku" through
the platform UI (not environment variables), then the connection likely
needs to be accessed through:

  OPTION A: An HTTP API endpoint injected by the platform
  OPTION B: A CLI command that routes through the platform
  OPTION C: A Python SDK function that queries the platform
  OPTION D: Direct environment variable injection at runtime

Check your CodeBender documentation for:
  - How to call configured providers from Python code
  - Whether there's a provider_client or similar module
  - If there's an HTTP endpoint your code should hit
  - If there's a CLI wrapper (like "codebender run" or "codebender invoke")
""")
