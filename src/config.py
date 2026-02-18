"""Configuration management for PostAgent"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "PostAgent/1.0")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", str(PROJECT_ROOT / "Content Organiser - Sheet1 (1).csv"))
DATA_DIR = PROJECT_ROOT / "data"
VIRAL_EXAMPLES_DIR = DATA_DIR / "viral_examples"
GENERATED_POSTS_DIR = DATA_DIR / "generated_posts"
SUBREDDIT_DB_PATH = DATA_DIR / "subreddit_db.json"

# Ensure directories exist
VIRAL_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_POSTS_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
OPENAI_MODEL = "gpt-4-turbo-preview"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 2000

# GitHub Configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# Reddit Configuration
REDDIT_SCRAPE_LIMIT = 30
REDDIT_SCRAPE_TIME_FILTER = "month"  # top posts from past month

# Rate Limiting
RATE_LIMIT_DELAY = 1  # seconds between API calls

def validate_config():
    """Validate required configuration"""
    errors = []

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required")

    # Database URL check (supports Supabase, Vercel Postgres, or any Postgres)
    db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('SUPABASE_DB_URL')
    if not db_url:
        errors.append("DATABASE_URL is required for database connection (get it from Supabase or other Postgres provider)")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True
