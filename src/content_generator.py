"""Content Generator - Generate Reddit posts using OpenAI GPT-4"""

import json
from typing import Dict, Optional
from datetime import datetime
from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from .reddit_scraper import RedditScraper
from .utils import rate_limit

class ContentGenerator:
    def __init__(self):
        """Initialize content generator"""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.reddit_scraper = RedditScraper()

    @rate_limit(1)
    def generate_post(
        self,
        project_analysis: Dict,
        subreddit_name: str,
        subreddit_info: Dict,
        viral_examples: Optional[str] = None
    ) -> Dict:
        """Generate a Reddit post for a specific subreddit"""

        # Get viral examples if not provided
        if not viral_examples:
            viral_examples = self.reddit_scraper.get_examples_for_subreddit(
                subreddit_name.replace("r/", "")
            )

        prompt = self._build_generation_prompt(
            project_analysis,
            subreddit_name,
            subreddit_info,
            viral_examples
        )

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a developer sharing your own project on Reddit. Write like a real person — short, casual, no hype. No bullet points, no bold headers, no marketing speak. Just a developer talking to other developers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=OPENAI_TEMPERATURE,
                response_format={"type": "json_object"}
            )

            generated = json.loads(response.choices[0].message.content)

            return {
                "subreddit": subreddit_name,
                "title": generated.get("title") or "",
                "body": generated.get("body") or "",
                "flair": generated.get("flair") or "",
                "estimated_engagement": generated.get("estimated_engagement") or "medium",
                "rationale": generated.get("rationale") or "",
                "generated_at": datetime.now().isoformat(),
                "model": OPENAI_MODEL
            }

        except Exception as e:
            raise Exception(f"Failed to generate content: {str(e)}")

    def _build_generation_prompt(
        self,
        project_analysis: Dict,
        subreddit_name: str,
        subreddit_info: Dict,
        viral_examples: Optional[str]
    ) -> str:
        """Build prompt for content generation"""

        analysis = project_analysis.get("analysis", {})
        github_url = project_analysis.get('url') or ''
        description = analysis.get('synopsis') or project_analysis.get('description') or ''
        stack = ', '.join(analysis.get('technical_stack') or [])

        prompt = f"""Write a Reddit post for {subreddit_name} sharing this project.

Project: {project_analysis.get('name') or ''}
GitHub: {github_url}
What it does: {description}
Stack: {stack}

Rules:
- Title: short, starts with "Built a..." or "I built a..." or similar natural opener. No hype.
- Body: 2-3 sentences MAX. Plain prose, no bullet points, no headers, no bold text.
  Explain what it does in plain developer language. End with the GitHub link.
- Sound like a developer casually sharing something they made, not a product launch.
- No phrases like "excited to share", "game-changer", "powerful", "robust", "seamlessly", "leverage".
- Flair: pick the most appropriate from {', '.join(subreddit_info.get('preferred_flairs') or ['Project'])}

Return JSON:
{{
  "title": "...",
  "body": "...",
  "flair": "...",
  "estimated_engagement": "high/medium/low",
  "rationale": "one sentence"
}}"""

        return prompt

    def _format_list(self, items: list) -> str:
        """Format list items for prompt"""
        return "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))

    def generate_multiple_posts(
        self,
        project_analysis: Dict,
        subreddit_matches: list
    ) -> Dict[str, Dict]:
        """Generate posts for multiple subreddits"""

        posts = {}

        for subreddit_name, score, subreddit_info in subreddit_matches:
            print(f"Generating post for {subreddit_name}...")

            try:
                post = self.generate_post(
                    project_analysis,
                    subreddit_name,
                    subreddit_info
                )
                posts[subreddit_name] = post

            except Exception as e:
                print(f"Error generating post for {subreddit_name}: {str(e)}")
                posts[subreddit_name] = {"error": str(e)}

        return posts

    def customize_for_subreddit(
        self,
        base_post: Dict,
        subreddit_name: str,
        subreddit_info: Dict
    ) -> Dict:
        """Customize an existing post for a different subreddit"""

        # For now, this generates a fresh post
        # Could be enhanced to take base_post and adapt it
        return self.generate_post(base_post, subreddit_name, subreddit_info)
