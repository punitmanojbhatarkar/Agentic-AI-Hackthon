#!/usr/bin/env python3
"""
Inspect the current Python runtime context for CodeBender injected objects.
This checks if CodeBender injects a provider client or request context.
"""

import sys
import inspect

print("=" * 80)
print("RUNTIME CONTEXT INSPECTION - CODEBENDER PROVIDER CLIENT")
print("=" * 80)

# 1. Check globals for injected objects
print("\n1. CHECKING GLOBAL SCOPE:")
print("-" * 80)
global_names = [
    'provider_client',
    'bedrock_client',
    'codebender_client',
    'llm_client',
    'agent_client',
    'provider',
    'bedrock',
    'request',
    'context',
]

for name in global_names:
    if name in globals():
        obj = globals()[name]
        print(f"  FOUND: {name}")
        print(f"    Type: {type(obj)}")
        print(f"    Methods: {[m for m in dir(obj) if not m.startswith('_')][:10]}")

# 2. Check sys modules for provider SDK
print("\n2. CHECKING LOADED MODULES FOR 'PROVIDER' OR 'BEDROCK':")
print("-" * 80)
provider_modules = []
for mod_name in sorted(sys.modules.keys()):
    if any(x in mod_name.lower() for x in ['provider', 'bedrock', 'agent', 'codebender', 'spawn']):
        mod = sys.modules[mod_name]
        print(f"  {mod_name}")
        if hasattr(mod, '__file__'):
            print(f"    File: {mod.__file__}")

# 3. Try to find if there's a special import path
print("\n3. TRYING SPECIAL IMPORTS:")
print("-" * 80)

special_imports = [
    ("from __main__ import provider_client", "Main provider_client"),
    ("import provider_client", "Direct provider_client import"),
    ("from . import provider_client", "Relative provider_client"),
    ("from codebender import get_provider", "CodeBender get_provider"),
    ("from codebender_sdk import Client", "CodeBender SDK Client"),
]

for import_str, desc in special_imports:
    try:
        exec(import_str, {"__name__": "__main__"})
        print(f"  SUCCESS: {desc}")
        print(f"    Import: {import_str}")
    except Exception as e:
        pass

# 4. Check if __builtins__ has been extended
print("\n4. CHECKING __BUILTINS__:")
print("-" * 80)
builtins_obj = __builtins__
if isinstance(builtins_obj, dict):
    custom_builtins = [k for k in builtins_obj.keys() if not k.startswith('__')]
else:
    custom_builtins = [k for k in dir(builtins_obj) if not k.startswith('__') and not k.isupper()]

if custom_builtins:
    print(f"  Custom builtins: {custom_builtins}")
else:
    print("  (no custom builtins)")

# 5. Try introspecting the call stack for context
print("\n5. CHECKING CALL STACK LOCALS:")
print("-" * 80)
frame = sys.currentframe()
while frame:
    locals_dict = frame.f_locals
    relevant_locals = {k: v for k, v in locals_dict.items() 
                      if any(x in k.lower() for x in ['provider', 'bedrock', 'client', 'agent'])}
    if relevant_locals:
        print(f"  Frame: {frame.f_code.co_filename}:{frame.f_lineno}")
        for k, v in relevant_locals.items():
            print(f"    {k}: {type(v).__name__}")
    frame = frame.f_back

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("""
If CodeBender injects a provider client, it would be available as:
1. A module in sys.modules (checked above)
2. A global variable in __main__ (checked above)
3. A parameter passed to your functions
4. An environment variable pointing to a config file
5. A local HTTP endpoint that your code calls

Since we found localhost:8000 responding, but it's your SupplySense API
(not CodeBender's), we need to check CodeBender's documentation for
how to access the "claud haiku" profile you configured.

LIKELY SCENARIO:
CodeBender uses one of these patterns:
- spawn_agent(agent_type="general", task="...") - delegates to platform
- A provider_client object passed to functions
- An HTTP endpoint provided by CodeBender's runtime environment
- Environment variables with the profile name and API key

Check CodeBender's Python SDK documentation for the correct pattern.
""")
