"""Reddit Pattern Scraper for analyzing viral posts"""

import praw
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    REDDIT_SCRAPE_LIMIT, VIRAL_EXAMPLES_DIR
)
from .utils import save_json, sanitize_filename

class RedditScraper:
    def __init__(self):
        """Initialize Reddit scraper"""
        self.reddit = None
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            try:
                self.reddit = praw.Reddit(
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT
                )
            except Exception as e:
                print(f"Warning: Reddit API not configured. Using fallback method. Error: {e}")

    def scrape_viral_posts(self, subreddit_name: str, limit: int = None) -> List[Dict]:
        """Scrape top posts from a subreddit"""
        if limit is None:
            limit = REDDIT_SCRAPE_LIMIT

        posts = []

        if not self.reddit:
            print(f"Reddit API not available. Please configure credentials to scrape {subreddit_name}")
            return posts

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Get top posts from the past month
            for submission in subreddit.top(time_filter="month", limit=limit):
                post_data = {
                    "id": submission.id,
                    "title": submission.title,
                    "body": submission.selftext,
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "author": str(submission.author),
                    "flair": submission.link_flair_text,
                    "url": submission.url,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "is_self": submission.is_self
                }
                posts.append(post_data)

            print(f"Scraped {len(posts)} posts from r/{subreddit_name}")

        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {str(e)}")

        return posts

    def analyze_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze patterns in viral posts"""
        if not posts:
            return {}

        patterns = {
            "avg_score": sum(p["score"] for p in posts) / len(posts),
            "avg_comments": sum(p["num_comments"] for p in posts) / len(posts),
            "common_flairs": self._get_common_flairs(posts),
            "title_patterns": self._analyze_titles(posts),
            "content_structure": self._analyze_content(posts),
            "engagement_metrics": {
                "high_engagement_threshold": sorted([p["score"] for p in posts], reverse=True)[int(len(posts)*0.1)] if posts else 0,
                "avg_title_length": sum(len(p["title"]) for p in posts) / len(posts),
                "self_post_ratio": sum(1 for p in posts if p["is_self"]) / len(posts)
            }
        }

        return patterns

    def _get_common_flairs(self, posts: List[Dict]) -> List[str]:
        """Extract common flairs used"""
        flair_counts = {}
        for post in posts:
            flair = post.get("flair")
            if flair:
                flair_counts[flair] = flair_counts.get(flair, 0) + 1

        # Return top 5 flairs
        sorted_flairs = sorted(flair_counts.items(), key=lambda x: x[1], reverse=True)
        return [flair for flair, _ in sorted_flairs[:5]]

    def _analyze_titles(self, posts: List[Dict]) -> Dict:
        """Analyze title patterns"""
        titles = [p["title"] for p in posts if p.get("title")]

        if not titles:
            return {}

        patterns = {
            "question_based": sum(1 for t in titles if "?" in t) / len(titles),
            "announcement_style": sum(1 for t in titles if any(word in t.lower() for word in ["introducing", "released", "announcing", "launched"])) / len(titles),
            "show_and_tell": sum(1 for t in titles if any(word in t.lower() for word in ["built", "made", "created", "developed"])) / len(titles),
            "problem_solution": sum(1 for t in titles if any(word in t.lower() for word in ["how to", "solution", "solved"])) / len(titles),
            "brackets_usage": sum(1 for t in titles if "[" in t and "]" in t) / len(titles)
        }

        return patterns

    def _analyze_content(self, posts: List[Dict]) -> List[str]:
        """Analyze common content structures"""
        structures = []

        for post in posts[:10]:  # Analyze top 10 posts
            body = post.get("body") or ""
            if not body:
                continue

            # Identify structure elements
            structure = []
            if "##" in body or "**" in body:
                structure.append("formatted_sections")
            if any(marker in body for marker in ["1.", "2.", "3.", "-", "*"]):
                structure.append("bullet_points_or_lists")
            if "github.com" in body.lower():
                structure.append("includes_github_link")
            if "demo" in body.lower() or "example" in body.lower():
                structure.append("includes_demo")
            if len(body.split("\n\n")) > 3:
                structure.append("multi_paragraph")

            if structure:
                structures.append(" + ".join(structure))

        return list(set(structures))

    def save_examples(self, posts: List[Dict], subreddit_name: str, patterns: Dict = None):
        """Save scraped examples to file"""
        if not posts:
            return

        subreddit_safe = sanitize_filename(subreddit_name)
        output_dir = VIRAL_EXAMPLES_DIR / subreddit_safe
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save raw posts
        posts_file = output_dir / "posts.json"
        save_json(posts, posts_file)

        # Save patterns
        if patterns:
            patterns_file = output_dir / "patterns.json"
            save_json(patterns, patterns_file)

        # Save formatted examples for LLM reference
        examples_md = output_dir / "examples.md"
        with open(examples_md, 'w', encoding='utf-8') as f:
            f.write(f"# Viral Post Examples from r/{subreddit_name}\n\n")
            f.write(f"Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

            for i, post in enumerate(posts[:10], 1):  # Top 10 posts
                f.write(f"## Example {i}\n\n")
                f.write(f"**Title:** {post['title']}\n\n")
                f.write(f"**Score:** {post['score']} | **Comments:** {post['num_comments']} | **Flair:** {post.get('flair', 'None')}\n\n")
                if post.get('body'):
                    f.write(f"**Content:**\n\n{post['body'][:1000]}\n\n")
                f.write(f"[View on Reddit]({post['permalink']})\n\n")
                f.write("---\n\n")

        print(f"Saved {len(posts)} examples to {output_dir}")

    def scrape_multiple_subreddits(self, subreddit_names: List[str], limit: int = None):
        """Scrape multiple subreddits"""
        for subreddit in subreddit_names:
            print(f"\nScraping r/{subreddit}...")
            posts = self.scrape_viral_posts(subreddit, limit)

            if posts:
                patterns = self.analyze_patterns(posts)
                self.save_examples(posts, subreddit, patterns)

    def get_examples_for_subreddit(self, subreddit_name: str) -> Optional[str]:
        """Load saved examples for a subreddit"""
        subreddit_safe = sanitize_filename(subreddit_name)
        examples_file = VIRAL_EXAMPLES_DIR / subreddit_safe / "examples.md"

        if examples_file.exists():
            with open(examples_file, 'r', encoding='utf-8') as f:
                return f.read()

        return None


# CLI function for standalone usage
def main():
    """CLI entry point for scraping"""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape viral posts from Reddit")
    parser.add_argument(
        "--subreddits",
        type=str,
        required=True,
        help="Comma-separated list of subreddits (e.g., 'MachineLearning,artificial')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=REDDIT_SCRAPE_LIMIT,
        help=f"Number of posts to scrape per subreddit (default: {REDDIT_SCRAPE_LIMIT})"
    )

    args = parser.parse_args()

    subreddits = [s.strip().replace("r/", "") for s in args.subreddits.split(",")]

    scraper = RedditScraper()
    scraper.scrape_multiple_subreddits(subreddits, args.limit)

if __name__ == "__main__":
    main()
