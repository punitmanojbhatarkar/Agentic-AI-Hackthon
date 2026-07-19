#!/usr/bin/env python3
"""
SupplySense API Starter
Properly sets up environment and launches the backend API server
"""

import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Change to project root to ensure relative imports work
os.chdir(project_root)

print(f"📁 Project root: {project_root}")
print(f"🐍 Python path configured")
print(f"📦 Python version: {sys.version}")

# Now import and run the Flask app
from backend.api import app

if __name__ == '__main__':
    print("\n🚀 SupplySense Backend API Server")
    print("📡 Running on http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000, host='127.0.0.1')
