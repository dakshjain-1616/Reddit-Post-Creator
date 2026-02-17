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
                        "content": "You are an expert Reddit content creator specializing in AI/ML community engagement. You create authentic, engaging posts that provide value and spark discussion while following community guidelines."
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

        prompt = f"""You are creating a Reddit post for {subreddit_name}.

## PROJECT INFORMATION

**Repository:** {project_analysis.get('name') or ''}
**Description:** {project_analysis.get('description') or ''}
**GitHub URL:** {project_analysis.get('url') or ''}

**Top 3 Value Propositions:**
{self._format_list(analysis.get('top_3_values') or [])}

**Technical Synopsis:**
{analysis.get('synopsis') or ''}

**Key Features:**
{self._format_list(analysis.get('key_features') or [])}

**How to Build Further with NEO:**
{analysis.get('build_further_with_neo') or ''}

**Use Cases:**
{self._format_list(analysis.get('use_cases') or [])}

**Technical Stack:**
{', '.join(analysis.get('technical_stack') or [])}

**Innovation:**
{analysis.get('innovation_level') or ''}

## SUBREDDIT CONTEXT

**Community:** {subreddit_info.get('description') or ''}
**Tone:** {subreddit_info.get('tone') or ''}
**Audience Level:** {(subreddit_info.get('audience_level') or '').replace('_', ' ').title()}

**Posting Rules:**
{self._format_list(subreddit_info.get('posting_rules') or [])}

**Preferred Flairs:** {', '.join(subreddit_info.get('preferred_flairs') or [])}
"""

        if viral_examples:
            prompt += f"""

## VIRAL POST EXAMPLES FROM THIS SUBREDDIT

Study these successful posts to understand what resonates with this community:

{viral_examples[:4000]}  # Limit to avoid token limits
"""

        prompt += """

## INSTRUCTIONS

Generate a Reddit post that:

1. **Title Requirements:**
   - Under 300 characters
   - Engaging and attention-grabbing
   - Follows patterns from viral examples
   - Avoid clickbait; be authentic and descriptive
   - Consider using: questions, announcements, or "I built..." format

2. **Body Requirements:**
   - 300-500 words
   - Use markdown formatting
   - Structure: Hook → Context → Value Props → Technical Details → Demo/Usage → Call to Action
   - Emphasize the top 3 value propositions naturally
   - Explain NEO's role without being overly promotional
   - Include technical depth appropriate for audience level
   - Add relevant links (GitHub, demos if available)
   - Be authentic and conversational, not salesy
   - Match the subreddit's tone and culture

3. **Engagement Strategy:**
   - Ask questions to encourage discussion
   - Invite feedback and contributions
   - Share specific use cases
   - Be humble and open about limitations
   - Provide clear next steps for interested readers

4. **Compliance:**
   - Follow all subreddit rules
   - No spam or excessive self-promotion
   - Provide genuine value to the community
   - Use appropriate flair

## OUTPUT FORMAT

Return a JSON object with:

```json
{
  "title": "Your engaging title here",
  "body": "Full post body in markdown format",
  "flair": "Suggested flair from preferred list",
  "estimated_engagement": "high/medium/low with brief reasoning",
  "rationale": "1-2 sentences explaining your approach for this specific subreddit"
}
```

Make the post authentic, valuable, and engaging. This is a real project built with NEO that deserves community attention."""

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
