#!/usr/bin/env python3
"""Check what agent/LLM modules are available."""

import sys
import importlib

candidates = [
    'nexen_agents',
    'codebender_agents',
    'spawn_agent',
    'bedrock',
    'boto3',
    'agents',
]

print("Checking for available modules...")
for mod in candidates:
    try:
        m = importlib.import_module(mod)
        print(f"FOUND: {mod}")
    except ImportError:
        print(f"  missing: {mod}")

print("\nChecking sys.modules for clues...")
for key in sorted(sys.modules.keys()):
    if any(x in key.lower() for x in ['agent', 'bedrock', 'aws', 'spawn', 'nexen', 'codebender']):
        print(f"  {key}")
