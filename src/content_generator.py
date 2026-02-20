"""Content Generator - Generate Reddit posts using OpenAI GPT-4"""

import json
from typing import Dict, Optional
from datetime import datetime
from openai import OpenAI

from .config import OPENAI_API_KEY, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENAI_MODEL, OPENAI_TEMPERATURE
from .reddit_scraper import RedditScraper
from .utils import rate_limit

class ContentGenerator:
    def __init__(self):
        """Initialize content generator"""
        api_key = OPENROUTER_API_KEY or OPENAI_API_KEY
        self.client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
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
                        "content": (
                            "You are a developer sharing a project you built on Reddit. "
                            "Write exactly like someone who ran into a real problem, built something to fix it, and is now sharing it with other developers. "
                            "Be specific about the pain — describe what was frustrating or broken before you built the tool. "
                            "Then explain what the tool does and list its concrete capabilities as bullet points. "
                            "Use plain English. No hype, no marketing fluff, no vague adjectives. "
                            "Avoid: 'excited to share', 'game-changer', 'powerful', 'robust', 'seamlessly', 'leverage', 'thrilled', 'innovative'. "
                            "Bullet points are encouraged when listing features or use cases — they help readers scan quickly. "
                            "Do not pad or summarize. Do not repeat yourself."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=OPENAI_TEMPERATURE,
                max_tokens=1200,
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

        features = analysis.get('key_features') or []
        use_cases = analysis.get('use_cases') or []
        pain_point = analysis.get('pain_point') or ''
        what_makes_it_different = analysis.get('what_makes_it_different') or ''

        prompt = f"""Write a Reddit post for {subreddit_name} sharing this project.

--- PROJECT INFO ---
Name: {project_analysis.get('name') or ''}
GitHub: {github_url}
What it does: {description}
The pain it solves: {pain_point}
Key features (use as-is in bullets): {', '.join(features)}
Use cases: {', '.join(use_cases)}
What makes it different: {what_makes_it_different}
Stack: {stack}

--- STYLE REFERENCE ---
Here is an example of the exact tone and structure to aim for:

"Working with embeddings (RAG, semantic search, clustering, recommendations, etc.), means:

Generate embeddings
Compute cosine similarity
Run retrieval
Hope it "works"

But I stumbled upon the issue of not being able to determine why my RAG responses felt off, retrieval quality being inconsistent and clustering results looked weird.

Debugging embeddings was painful.

To solve this issue, we built this Embedding evaluation CLI tool to audit embedding spaces, not just generate them.

Instead of guessing whether your vectors make sense, it:

- Detects semantic outliers
- Identifies cluster inconsistencies
- Flags global embedding collapse
- Highlights ambiguous boundary tokens
- Generates heatmaps and cluster visualizations
- Produces structured reports (JSON / Markdown)

Checkout the tool and feel free to share your feedback:
https://github.com/example/tool

This is especially useful for:
- RAG pipelines
- Vector DB systems
- Semantic search products
- Embedding model comparisons
- Fine-tuning experiments

It surfaces structural problems in the geometry of your embeddings before they break your system downstream."

--- WHAT MAKES THAT EXAMPLE WORK ---
- Opens with the normal workflow in that domain, written as short fragments — shows you understand the space
- Then hits the real frustration honestly ("felt off", "looked weird") — not a polished problem statement
- One short blunt sentence as its own line after describing the pain
- "To solve this, we built..." — simple pivot, no fanfare
- "Instead of guessing whether..." — frames the cognitive problem, not just the technical one
- Feature bullet points are action verbs: Detects, Identifies, Flags, Highlights, Generates, Produces
- Link line is plain, feedback invite is casual
- Use cases listed plainly under "This is especially useful for:"
- Closing line is a specific technical insight, not a summary

--- RULES ---
- Adapt the structure to the project — don't copy the example literally. The opening should reflect THIS project's domain and workflow.
- Vary sentence rhythm. Mix short punchy lines with slightly longer ones.
- Never start with "I built" or "I made" — open with the domain/workflow context first.
- No paragraph headers, no bold text, no markdown formatting in the body.
- No marketing words: powerful, robust, seamless, innovative, excited, thrilled, game-changer, leverage, cutting-edge.
- The GitHub link goes on its own line. Keep the feedback invite short and natural.
- Title: "Built a...", "We built a...", "I made a..." — short, describes what it does.
- Flair: pick from {', '.join(subreddit_info.get('preferred_flairs') or ['Project'])}

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
