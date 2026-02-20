"""GitHub Repository Analyzer using OpenAI GPT-4"""

import requests
import json
import time
from typing import Dict, Optional
from openai import OpenAI

from .config import OPENAI_API_KEY, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, GITHUB_TOKEN, GITHUB_API_BASE, OPENAI_MODEL
from .utils import extract_repo_info, rate_limit

class GitHubAnalyzer:
    def __init__(self):
        api_key = OPENROUTER_API_KEY or OPENAI_API_KEY
        self.client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {GITHUB_TOKEN}"

    def _make_github_request(self, url: str, max_retries: int = 3) -> requests.Response:
        """Make GitHub API request with retry logic"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)

                # If successful, return immediately
                if response.ok:
                    return response

                # If 502/503/504, retry
                if response.status_code in [502, 503, 504]:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        print(f"GitHub API {response.status_code}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue

                # For other errors, raise immediately
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    print(f"Request timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise Exception(f"GitHub API request timed out after {max_retries} attempts")

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    print(f"Request error: {e}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise

        # If we get here, all retries failed
        response.raise_for_status()
        return response

    @rate_limit(1)
    def fetch_repo_data(self, repo_url: str) -> Dict:
        """Fetch repository data from GitHub API"""
        try:
            repo_info = extract_repo_info(repo_url)
            owner = repo_info['owner']
            repo = repo_info['repo']

            # Fetch repository metadata
            repo_api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
            response = self._make_github_request(repo_api_url)
            repo_data = response.json()

            # Fetch README
            readme_content = self._fetch_readme(owner, repo)

            # Fetch languages
            languages_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
            lang_response = self._make_github_request(languages_url)
            languages = list(lang_response.json().keys()) if lang_response.ok else []

            return {
                "name": repo_data.get("name") or "",
                "full_name": repo_data.get("full_name") or "",
                "description": repo_data.get("description") or "",
                "stars": repo_data.get("stargazers_count") or 0,
                "forks": repo_data.get("forks_count") or 0,
                "url": repo_url,
                "homepage": repo_data.get("homepage") or "",
                "topics": repo_data.get("topics") or [],
                "languages": languages or [],
                "readme": readme_content or "",
                "created_at": repo_data.get("created_at") or "",
                "updated_at": repo_data.get("updated_at") or ""
            }

        except Exception as e:
            raise Exception(f"Failed to fetch GitHub data: {str(e)}")

    def _fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README content"""
        readme_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
        try:
            response = self._make_github_request(readme_url)
            if response.ok:
                readme_data = response.json()
                # Decode base64 content
                import base64
                content = base64.b64decode(readme_data['content']).decode('utf-8')
                return content
        except Exception as e:
            print(f"Warning: Could not fetch README: {str(e)}")

        return ""

    def analyze_with_llm(self, repo_data: Dict) -> Dict:
        """Analyze repository using OpenAI GPT-4"""
        prompt = self._build_analysis_prompt(repo_data)

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a developer reading another developer's GitHub repo. Your job is to understand what problem it solves, what pain it targets, and how a real developer would explain it to a colleague — not what a marketer would say about it. Be specific and technical. Avoid hype words."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)

            # Ensure all expected fields exist with defaults
            default_analysis = {
                "top_3_values": [],
                "build_further_with_neo": "",
                "synopsis": "",
                "pain_point": "",
                "key_features": [],
                "technical_stack": [],
                "use_cases": [],
                "target_audience": "",
                "what_makes_it_different": ""
            }

            # Merge with defaults
            analysis = {**default_analysis, **analysis}

            # Combine with repo metadata
            return {
                **repo_data,
                "analysis": analysis
            }

        except Exception as e:
            raise Exception(f"Failed to analyze with LLM: {str(e)}")

    def _build_analysis_prompt(self, repo_data: Dict) -> str:
        """Build prompt for LLM analysis"""
        languages = ', '.join(repo_data.get('languages') or [])
        topics = ', '.join(repo_data.get('topics') or [])

        return f"""Read this GitHub repository and extract information that would help a developer explain it naturally to other developers.

REPOSITORY: {repo_data.get('name', 'Unknown')}
DESCRIPTION: {repo_data.get('description', 'No description available')}
LANGUAGES: {languages}
TOPICS: {topics}

README CONTENT:
{repo_data['readme'][:8000]}

Answer these questions as JSON:

{{
  "top_3_values": ["Specific thing 1 this does that others don't", "Specific thing 2", "Specific thing 3"],
  "build_further_with_neo": "How developers could extend this project further",
  "synopsis": "2-3 sentences explaining what it does and what problem it solves — written like a developer explaining it to a colleague",
  "pain_point": "The specific frustration or gap this tool addresses — what was broken or missing before it existed",
  "key_features": ["Concrete action/capability 1", "Concrete action/capability 2", "Concrete action/capability 3"],
  "technical_stack": ["Tech 1", "Tech 2", "Tech 3"],
  "use_cases": ["Specific scenario where this is useful 1", "Specific scenario 2", "Specific scenario 3"],
  "target_audience": "What kind of developer or workflow this is built for",
  "what_makes_it_different": "One specific technical thing that separates this from the obvious alternative"
}}

Rules:
- key_features must be action verbs describing what the tool does: "Detects X", "Outputs Y", "Runs Z" — not adjectives
- pain_point should describe what was painful/missing before this tool existed
- synopsis must not use marketing words like powerful, robust, seamless, innovative
- all fields must be grounded in what the README actually says, not inferred generically"""

    def analyze_repository(self, repo_url: str, force_refresh: bool = False) -> Dict:
        """Complete workflow: fetch data and analyze. Uses DB cache to skip repeat work."""
        from .database import get_cached_analysis, save_analysis_cache

        if not force_refresh:
            cached = get_cached_analysis(repo_url)
            if cached:
                print(f"Using cached analysis for {repo_url}")
                return cached

        print(f"Fetching data from {repo_url}...")
        repo_data = self.fetch_repo_data(repo_url)

        print(f"Analyzing with {OPENAI_MODEL}...")
        analysis = self.analyze_with_llm(repo_data)

        save_analysis_cache(repo_url, analysis)
        print("Analysis cached.")

        return analysis
