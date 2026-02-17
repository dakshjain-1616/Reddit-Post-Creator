"""
Vercel Serverless Entry Point
This file is required for Vercel Python deployments
"""

from app import app

# Vercel automatically handles the WSGI interface
# Just export the Flask app instance
