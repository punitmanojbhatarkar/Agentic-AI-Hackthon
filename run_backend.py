#!/usr/bin/env python3
"""
Direct API launcher - sets up all paths before any imports
"""

import sys
import os

# Add project root to path FIRST, before any imports
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)

print(f"✓ Added to path: {_root}")

# Now run the backend API
if __name__ == '__main__':
    # Test import first
    try:
        from agents.orchestrator import SupplyChainAgent
        print("✓ agents.orchestrator imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print(f"  Current path: {sys.path}")
        sys.exit(1)
    
    # Now import and run Flask
    from backend.api import app
    
    print("\n" + "="*50)
    print("🚀 SupplySense Backend API Server")
    print("="*50)
    print("📡 Running on http://localhost:5000")
    print("   Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')
