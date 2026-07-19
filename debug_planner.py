#!/usr/bin/env python3
"""Debug test to see what parameters the Groq planner is generating."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import aws_config
aws_config.configure_test_environment()

from agents.planner import plan_investigation
from agents.tool_registry import format_tools_for_prompt
import json

question = "What is causing today's biggest supply chain disruption?"
tools_desc = format_tools_for_prompt()

print("=" * 80)
print("DEBUGGING GROQ PLANNER OUTPUT")
print("=" * 80)
print(f"\nQuestion: {question}\n")

steps = plan_investigation(question, tools_desc)

print(f"Generated {len(steps)} steps:\n")
for step in steps:
    print(f"Step {step['step']}: {step['tool']}")
    print(f"  Parameters:")
    for param_name, param_value in step['parameters'].items():
        print(f"    {param_name}: {param_value}")
    print(f"  Reasoning: {step['reasoning']}\n")

print("=" * 80)
print("Analysis:")
print("=" * 80)

# Check which parameters are FROM_DB vs hardcoded vs FROM_STEP
for step in steps:
    for param_name, param_value in step['parameters'].items():
        if isinstance(param_value, str):
            if param_value == "FROM_DB":
                tool_name = step['tool']
                key = (tool_name, param_name)
                from agents.orchestrator import PARAMETER_DB_FETCHERS
                if key in PARAMETER_DB_FETCHERS:
                    fetcher_name, fk = PARAMETER_DB_FETCHERS[key]
                    print(f"✓ {tool_name}.{param_name} = FROM_DB → mapped to {fetcher_name}({fk})")
                else:
                    print(f"✗ {tool_name}.{param_name} = FROM_DB → NOT in mapping!")
            elif param_value.startswith("FROM_STEP"):
                print(f"  {step['tool']}.{param_name} = {param_value} (dependency)")
            else:
                print(f"  {step['tool']}.{param_name} = '{param_value}' (literal)")
