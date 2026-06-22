"""
Vercel serverless function entry point.

Exposes the FastAPI app as a Vercel Python serverless function.
All /api/* requests are routed here via vercel.json rewrites.
"""

import sys
import os

# Add the backend directory to Python path so existing
# `from app.xxx` imports continue to work unchanged.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app  # noqa: E402
