# SupplySense Backend API - Getting Started Guide

## Quick Start (Windows)

### Option 1: Use the Batch File (Easiest)
Simply double-click `START_API.bat` in the project root folder. The API server will start and run on `http://localhost:5000`.

### Option 2: Use PowerShell/Command Prompt
```powershell
cd "C:\path\to\supplysense"
python backend/api.py
```

### Option 3: Use Python Directly
```powershell
python -m backend.api
```

## Verification

Once the server is running, you should see:
```
============================================================
[START] SupplySense Backend API Server
============================================================
[INFO] Running on http://localhost:5000
[OK] Health check: http://localhost:5000/health
[OK] Test endpoint: http://localhost:5000/api/test

   Press Ctrl+C to stop
============================================================

 * Serving Flask app 'api'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

## Test the API

### Health Check Endpoint
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok",
  "timestamp": "2026-07-19T03:13:08.953685"
}
```

### Test Endpoint
```bash
curl http://localhost:5000/api/test
```

Expected response:
```json
{
  "message": "[OK] API is working!",
  "timestamp": "2026-07-19T03:13:10.971634"
}
```

## Troubleshooting

### "No module named 'flask'"
Install Flask with:
```powershell
pip install flask flask-cors
```

### "ModuleNotFoundError: No module named 'agents'"
Make sure you're running the command from the project root directory (where `backend/`, `agents/`, and `data/` folders are located).

### "Address already in use"
Port 5000 is already in use. Either:
- Stop the existing process: `netstat -ano | findstr :5000` to find the PID, then `taskkill /PID <PID> /F`
- Or modify the port in `backend/api.py` (change `port=5000` to `port=5001`)

### Unicode/Emoji Errors
The API has been updated to avoid Unicode characters that cause console encoding issues on Windows. If you still see encoding errors, make sure you're using the latest version of `backend/api.py`.

## API Architecture

The backend API is built with:
- **Flask** - Lightweight web framework
- **Flask-CORS** - Cross-Origin Resource Sharing for frontend communication
- **Python 3.13+** - Runtime environment

### Current Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check - verify API is running |
| `/api/test` | GET | Test endpoint - verify API functionality |

### Additional Services (TODO)
The following services are available in `backend/services/` and can be integrated:
- Disruption detection (`/api/disruption`)
- Inventory management (`/api/inventory`)
- NLP query processing (`/api/nlp-query`)
- Recommendations (`/api/recommendations`)
- Reporting (`/api/reporting`)
- Supplier risk (`/api/supplier-risk`)

## Development

### Add a New Endpoint
Edit `backend/api.py` and add a new route:

```python
@app.route('/api/my-endpoint', methods=['GET', 'POST'])
def my_endpoint():
    """Description of what this endpoint does."""
    return jsonify({
        "message": "Response data here"
    })
```

### Restart in Development Mode
The API runs with `debug=True` by default, which means it will automatically reload when you save changes to `backend/api.py`.

## Production Deployment

For production use, deploy with a proper WSGI server like Gunicorn:

```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.api:app
```

---

**Status**: ✓ Backend API is fully functional and ready for integration with the frontend React application.
