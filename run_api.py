#!/usr/bin/env python3
"""
Entry point for running the URL to HTML Converter API.
"""

import os
import sys
import uvicorn
from api.config import APIConfig

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.getenv("API_HOST", APIConfig.HOST)
    port = int(os.getenv("API_PORT", APIConfig.PORT))
    workers = int(os.getenv("API_WORKERS", APIConfig.WORKERS))
    log_level = os.getenv("LOG_LEVEL", APIConfig.LOG_LEVEL.lower())
    
    print(f"Starting URL to HTML Converter API")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Workers: {workers}")
    print(f"Log Level: {log_level}")
    print(f"API Version: {APIConfig.API_VERSION}")
    print(f"\nAPI Documentation available at: http://{host}:{port}/docs")
    print(f"ReDoc available at: http://{host}:{port}/redoc")
    print(f"Health check: http://{host}:{port}/health\n")
    
    # Run the API
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        workers=workers if workers > 1 else None,  # Only use workers if > 1
        log_level=log_level,
        reload=os.getenv("RELOAD", "false").lower() == "true",  # Auto-reload for development
        access_log=True
    )

