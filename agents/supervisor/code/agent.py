"""Entry point for the Supervisor Agent application.

This module imports the FastAPI app from app.main and runs it using uvicorn.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)