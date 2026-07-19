#!/usr/bin/env python3
"""
FIX YOUR LOCAL backend/api.py
Run this script in your project root directory to fix the imports.
"""

import os

# The FIXED api.py content
FIXED_API_PY = '''"""
SupplySense Backend API Server - MINIMAL WORKING VERSION

Uses only imports that exist in the actual project structure.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

# Create Flask app
app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

print("[OK] Flask app initialized successfully")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "message": "SupplySense Backend API is running"
    })


@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify API is working."""
    return jsonify({
        "message": "[OK] API is working!",
        "timestamp": datetime.now().isoformat()
    })


# TODO: Add actual service routes when services are ready
# from backend.services.disruption.routes import disruption_bp
# from backend.services.inventory.routes import inventory_bp
# from backend.services.recommendations.routes import recommendations_bp
# app.register_blueprint(disruption_bp, url_prefix='/api/disruption')
# app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
# app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found", "message": str(error)}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error", "message": str(error)}), 500


if __name__ == '__main__':
    print("\\n" + "="*60)
    print("[START] SupplySense Backend API Server")
    print("="*60)
    print("[INFO] Running on http://localhost:5000")
    print("[OK] Health check: http://localhost:5000/health")
    print("[OK] Test endpoint: http://localhost:5000/api/test")
    print("\\n   Press Ctrl+C to stop")
    print("="*60 + "\\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)
'''

# Write the fixed version
api_file_path = os.path.join('backend', 'api.py')

print("Fixing backend/api.py...")
print(f"File path: {api_file_path}")

# Check if backend folder exists
if not os.path.exists('backend'):
    print("ERROR: backend/ folder not found!")
    print("Make sure you're in the project root directory.")
    exit(1)

# Backup the old file
if os.path.exists(api_file_path):
    backup_path = api_file_path + '.backup'
    print(f"Creating backup: {backup_path}")
    with open(api_file_path, 'r') as f:
        backup_content = f.read()
    with open(backup_path, 'w') as f:
        f.write(backup_content)
    print("Backup created!")

# Write the fixed version
with open(api_file_path, 'w') as f:
    f.write(FIXED_API_PY)

print("✅ backend/api.py has been FIXED!")
print()
print("Now you can run:")
print("  python backend/api.py")
print()
