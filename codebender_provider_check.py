#!/usr/bin/env python3
"""
Determine the correct way to call CodeBender's built-in Bedrock provider
"""
import os

# Based on CodeBender documentation, check if there's a standard pattern
print("=" * 80)
print("CODEBENDER PROVIDER LOOKUP")
print("=" * 80)

# The most common patterns for agent platforms:
# 1. Direct API endpoint via env var
# 2. SDK method to get provider
# 3. Context injection into functions

patterns_to_check = {
    "CODEBENDER_BEDROCK_ENDPOINT": "API endpoint to Bedrock provider",
    "CODEBENDER_LLM_API_KEY": "API key for LLM calls",
    "CODEBENDER_PROVIDER_TOKEN": "Provider authentication token",
    "LLM_API_ENDPOINT": "Generic LLM endpoint",
}

print("\nCHECKING ENVIRONMENT VARIABLES:")
found = False
for var, desc in patterns_to_check.items():
    if var in os.environ:
        print(f"[FOUND] {var}: {desc}")
        found = True

if not found:
    print("[NOT FOUND] No CodeBender provider environment variables detected")

print("\n" + "=" * 80)
print("QUESTION FOR YOU:")
print("=" * 80)
print("""
I cannot auto-detect CodeBender's built-in provider API because:
  1. No CodeBender-specific environment variables are exposed in this environment
  2. No built-in SDK modules are available in Python's path
  3. CodeBender's platform API documentation is not publicly accessible to me

HOWEVER, CodeBender DOES support provider connections through:
  - The UI (you configured Amazon Bedrock provider)
  - The agent/spawn system (which likely has access to configured providers)

BEST SOLUTION: Check your CodeBender documentation or contact support for:
  1. Is there a built-in Python SDK/helper to call configured providers?
  2. What's the function signature? (e.g., get_provider("amazon_bedrock")?)
  3. Should I use the spawn_agent() tool instead to delegate LLM calls?

IN THE MEANTIME:
  - Current system works with mock Bedrock (all tests passing)
  - When you provide the correct API, I'll rewrite aws_config.py immediately
""")
