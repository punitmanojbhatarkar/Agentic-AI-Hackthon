"""
Demonstration of the tool registry for the LLM.

Shows how the registry provides structured tool access and formatting.
"""

from tool_registry import (
    get_tool_by_name,
    format_tools_for_prompt,
    get_tool_names,
    get_system_prompt,
)


def demo_tool_registry():
    """Demonstrate the tool registry functionality."""
    
    print("=" * 80)
    print("TOOL REGISTRY DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Demo 1: List all available tools
    print("1. AVAILABLE TOOLS")
    print("-" * 80)
    tool_names = get_tool_names()
    for i, name in enumerate(tool_names, 1):
        print(f"   {i}. {name}")
    print()
    
    # Demo 2: Get a specific tool
    print("2. RETRIEVING SPECIFIC TOOL")
    print("-" * 80)
    tool = get_tool_by_name("forecast_demand")
    print(f"Tool: {tool['name']}")
    print(f"Description: {tool['description']}")
    print(f"Parameters: {list(tool['parameters'].keys())}")
    print()
    
    # Demo 3: Format tools for LLM prompt
    print("3. FORMATTED TOOL REGISTRY FOR LLM")
    print("-" * 80)
    formatted = format_tools_for_prompt()
    print(formatted)
    print()
    
    # Demo 4: Generate complete system prompt
    print("4. COMPLETE SYSTEM PROMPT (first 500 chars)")
    print("-" * 80)
    system_prompt = get_system_prompt()
    print(system_prompt[:500] + "...")
    print()
    
    print("=" * 80)
    print("Registry is ready for LLM integration!")
    print("=" * 80)


if __name__ == "__main__":
    demo_tool_registry()
