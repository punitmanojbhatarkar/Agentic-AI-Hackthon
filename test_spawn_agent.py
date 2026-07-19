#!/usr/bin/env python3
"""Quick test to verify spawn_agent is available."""

try:
    from nexen_agents import spawn_agent
    print("✓ spawn_agent imported successfully")
    print(f"  Type: {type(spawn_agent)}")
    print(f"  Module: {spawn_agent.__module__}")
except ImportError as e:
    print(f"✗ spawn_agent import failed: {e}")
    print("\nAvailable modules:")
    import sys
    for mod in sys.modules:
        if 'nexen' in mod.lower() or 'agent' in mod.lower():
            print(f"  - {mod}")
