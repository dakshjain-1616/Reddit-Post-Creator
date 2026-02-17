"""
Vercel Serverless Entry Point
This file is required for Vercel Python deployments
"""

from app import app

# Vercel uses this as the entry point
def handler(request, context=None):
    return app(request.environ, lambda *args: None)

# Export for Vercel
app = app
