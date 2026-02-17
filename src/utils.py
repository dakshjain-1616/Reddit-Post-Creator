"""Utility functions for PostAgent"""

import time
import json
from pathlib import Path
from typing import Any, Dict
import re

def sanitize_filename(name: str) -> str:
    """Convert string to safe filename"""
    if not name:
        return ""
    # Remove special characters, keep alphanumeric and hyphens
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with hyphens
    name = re.sub(r'[-\s]+', '-', name)
    return name.lower().strip('-')

def extract_repo_info(repo_url: str) -> Dict[str, str]:
    """Extract owner and repo name from GitHub URL"""
    # Handle various GitHub URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$',
        r'github\.com/([^/]+)/([^/]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, repo_url)
        if match:
            owner, repo = match.groups()
            return {
                'owner': owner,
                'repo': repo.replace('.git', ''),
                'full_name': f"{owner}/{repo.replace('.git', '')}"
            }

    raise ValueError(f"Invalid GitHub URL: {repo_url}")

def save_json(data: Any, filepath: Path):
    """Save data as JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(filepath: Path) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def rate_limit(delay: float):
    """Simple rate limiting decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            time.sleep(delay)
            return result
        return wrapper
    return decorator

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_list_for_display(items: list, prefix: str = "  - ") -> str:
    """Format list items for console display"""
    return "\n".join(f"{prefix}{item}" for item in items)
