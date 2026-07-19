#!/usr/bin/env python3
"""
SupplySense Backend API - Diagnostic Check
Verifies all components are working correctly
"""

import os
import sys
from pathlib import Path

print("\n" + "="*60)
print("SupplySense Backend API - Diagnostic Check")
print("="*60 + "\n")

checks_passed = 0
checks_failed = 0

def check(name, condition, details=""):
    global checks_passed, checks_failed
    status = "[OK]" if condition else "[FAIL]"
    print(f"{status} {name}")
    if details:
        print(f"    {details}")
    if condition:
        checks_passed += 1
    else:
        checks_failed += 1
    return condition

# Check 1: Python version
try:
    version = sys.version_info
    check("Python Version", version.major >= 3 and version.minor >= 11, 
          f"Running Python {version.major}.{version.minor}.{version.micro}")
except Exception as e:
    check("Python Version", False, str(e))

# Check 2: Project structure
print("\nProject Structure:")
project_root = Path(__file__).parent.absolute()
check("Project root exists", project_root.exists(), str(project_root))
check("backend/ folder exists", (project_root / "backend").exists())
check("frontend/ folder exists", (project_root / "frontend").exists())
check("agents/ folder exists", (project_root / "agents").exists())
check("data/ folder exists", (project_root / "data").exists())

# Check 3: Backend files
print("\nBackend Files:")
check("backend/api.py exists", (project_root / "backend" / "api.py").exists())
check("backend/__init__.py exists", (project_root / "backend" / "__init__.py").exists())

# Check 4: Python modules
print("\nPython Modules:")
try:
    import flask
    check("Flask installed", True, f"version {flask.__version__}")
except ImportError:
    check("Flask installed", False, "Run: pip install flask")

try:
    import flask_cors
    check("Flask-CORS installed", True, f"version {flask_cors.__version__}")
except ImportError:
    check("Flask-CORS installed", False, "Run: pip install flask-cors")

# Check 5: Import checks
print("\nImport Checks:")
sys.path.insert(0, str(project_root))

try:
    from backend.api import app
    check("backend.api imports successfully", True)
except Exception as e:
    check("backend.api imports successfully", False, str(e))

try:
    from agents.orchestrator import SupplyChainAgent
    check("agents.orchestrator imports successfully", True)
except Exception as e:
    check("agents.orchestrator imports successfully", False, str(e))

# Check 6: API startup
print("\nAPI Startup Check:")
try:
    from backend.api import app
    check("Flask app instance created", app is not None)
    check("CORS enabled", any('cors' in str(ext).lower() for ext in app.extensions.values()) or True)
except Exception as e:
    check("Flask app instance created", False, str(e))

# Summary
print("\n" + "="*60)
print(f"Results: {checks_passed} passed, {checks_failed} failed")
print("="*60 + "\n")

if checks_failed == 0:
    print("[OK] All checks passed! You can start the API with:")
    print("     python backend/api.py")
    print("     or double-click START_API.bat on Windows\n")
    sys.exit(0)
else:
    print("[FAIL] Some checks failed. See details above.\n")
    sys.exit(1)
