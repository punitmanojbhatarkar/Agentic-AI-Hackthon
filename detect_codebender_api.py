#!/usr/bin/env python3
"""
Test script to detect CodeBender provider connection API
"""
import os
import sys

print("=" * 80)
print("CODEBENDER PROVIDER CONNECTION DETECTION")
print("=" * 80)

# Check for CodeBender-specific environment variables
print("\n1. ENVIRONMENT VARIABLES:")
print("-" * 80)
codebender_vars = [k for k in os.environ.keys() if 'CODEBENDER' in k.upper() or 'PROVIDER' in k.upper()]
if codebender_vars:
    for var in sorted(codebender_vars):
        print(f"  {var}: {os.environ[var][:50]}...")
else:
    print("  (No CodeBender-specific variables found)")

# Check for built-in modules
print("\n2. AVAILABLE MODULES:")
print("-" * 80)
test_modules = [
    'codebender',
    'codebender.providers',
    'codebender.sdk',
    'provider_sdk',
    'bedrock_provider',
    'llm_sdk',
]
for mod in test_modules:
    try:
        __import__(mod)
        print(f"  ✓ {mod} available")
    except ImportError:
        pass

# Check sys.path for hints
print("\n3. PYTHON PATH:")
print("-" * 80)
for path in sys.path[:3]:
    print(f"  {path}")

# Try importing common patterns
print("\n4. TRYING COMMON PATTERNS:")
print("-" * 80)
patterns = [
    "from codebender import get_provider",
    "from codebender.providers import amazon_bedrock",
    "import provider_client",
]

for pattern in patterns:
    try:
        exec(pattern)
        print(f"  ✓ {pattern}")
    except Exception as e:
        print(f"  ✗ {pattern}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print("""
If CodeBender has a built-in provider API, it would typically:
  1. Be exposed as an environment variable (CODEBENDER_BEDROCK_ENDPOINT, etc.)
  2. Be available in a built-in module (codebender.providers, provider_sdk, etc.)
  3. Have a helper function to retrieve provider connections by name

Please check CodeBender's documentation or platform settings for:
  - Provider SDK/API documentation
  - Environment variables that expose your configured providers
  - Helper functions to call the Bedrock provider you configured
""")
