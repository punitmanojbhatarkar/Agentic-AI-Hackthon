#!/usr/bin/env python
"""Pre-test checklist for Tests 16-18"""

import sys
import os

print("\n" + "=" * 80)
print("PRE-TEST CHECKLIST FOR TESTS 16-18")
print("=" * 80 + "\n")

checks = {
    "Database exists": os.path.exists("data/supplysense.db"),
    "backend/test_chain_1.py needed": not os.path.exists("backend/test_chain_1.py"),
    "agents/test_sweep.py needed": not os.path.exists("agents/test_sweep.py"),
    "agents/test_multistep.py needed": not os.path.exists("agents/test_multistep.py"),
}

# Check imports
import_checks = {}
try:
    from data.queries import get_demand_history, get_current_stock
    import_checks["data.queries"] = True
except Exception as e:
    import_checks["data.queries"] = str(e)

try:
    from backend.forecasting import forecast_demand
    import_checks["backend.forecasting"] = True
except Exception as e:
    import_checks["backend.forecasting"] = str(e)

try:
    from backend.inventory import predict_stockout
    import_checks["backend.inventory"] = True
except Exception as e:
    import_checks["backend.inventory"] = str(e)

try:
    from agents.orchestrator import SupplyChainAgent
    import_checks["agents.orchestrator"] = True
except Exception as e:
    import_checks["agents.orchestrator"] = str(e)

try:
    from agents.sweep import run_intelligence_sweep
    import_checks["agents.sweep"] = True
except Exception as e:
    import_checks["agents.sweep"] = str(e)

try:
    import boto3
    import_checks["boto3"] = True
except Exception as e:
    import_checks["boto3"] = f"NOT INSTALLED - {str(e)}"

# Print results
print("STEP 1: Database & Files")
print("-" * 80)
for check, status in checks.items():
    status_str = "[OK]" if status else "[NEEDED]"
    print(f"  {check}: {status_str}")

print("\nSTEP 2: Python Imports")
print("-" * 80)
all_imports_ok = True
for module, status in import_checks.items():
    if status is True:
        print(f"  {module}: [OK]")
    else:
        print(f"  {module}: [FAILED] - {status}")
        all_imports_ok = False

print("\nSTEP 3: AWS Credentials")
print("-" * 80)
aws_ok = "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ
if aws_ok:
    print(f"  AWS credentials: [OK] CONFIGURED")
else:
    print(f"  AWS credentials: [MISSING] (needed for Bedrock)")

print("\n" + "=" * 80)
print("REQUIREMENTS CHECKLIST")
print("=" * 80)

requirements = [
    ("Database populated", checks["Database exists"]),
    ("All imports working", all_imports_ok),
    ("AWS credentials set", aws_ok),
    ("Test files created", not (checks["backend/test_chain_1.py needed"] or 
                                 checks["agents/test_sweep.py needed"] or 
                                 checks["agents/test_multistep.py needed"])),
]

all_ready = True
for req, status in requirements:
    status_str = "[OK]" if status else "[NEEDED]"
    print(f"  {status_str} {req}")
    if not status:
        all_ready = False

print("\n" + "=" * 80)
if all_ready:
    print("[OK] ALL SYSTEMS READY FOR TESTING")
else:
    print("[INCOMPLETE] SETUP INCOMPLETE - SEE REQUIREMENTS ABOVE")
print("=" * 80 + "\n")

sys.exit(0 if all_ready else 1)
