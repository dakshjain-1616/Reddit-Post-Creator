"""Post-Publication Analytics Tracker"""

import praw
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass, asdict

from .config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, DATA_DIR
from .utils import save_json, load_json

@dataclass
class PostMetrics:
    """Data class for post metrics"""
    post_id: str
    reddit_url: str
    subreddit: str
    title: str
    upvotes: int
    upvote_ratio: float
    num_comments: int
    awards: int
    created_utc: float
    tracked_at: str
    hours_since_post: float

    def to_dict(self):
        return asdict(self)

class AnalyticsTracker:
    def __init__(self):
        """Initialize analytics tracker"""
        self.analytics_dir = DATA_DIR / "analytics"
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

        self.reddit = None
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            try:
                self.reddit = praw.Reddit(
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT
                )
            except Exception as e:
                print(f"Warning: Could not initialize Reddit API: {e}")

    def track_post(self, reddit_url: str, project_name: str, subreddit: str) -> Optional[PostMetrics]:
        """Track a published post's metrics"""

        if not self.reddit:
            print("Reddit API not configured. Cannot track post.")
            return None

        try:
            # Get post from Reddit
            submission = self.reddit.submission(url=reddit_url)

            # Create metrics object
            metrics = PostMetrics(
                post_id=submission.id,
                reddit_url=reddit_url,
                subreddit=subreddit,
                title=submission.title,
                upvotes=submission.score,
                upvote_ratio=submission.upvote_ratio,
                num_comments=submission.num_comments,
                awards=submission.total_awards_received,
                created_utc=submission.created_utc,
                tracked_at=datetime.now().isoformat(),
                hours_since_post=(datetime.now().timestamp() - submission.created_utc) / 3600
            )

            # Save metrics
            self._save_metrics(project_name, metrics)

            return metrics

        except Exception as e:
            print(f"Error tracking post: {e}")
            return None

    def track_post_manual(self, project_name: str, subreddit: str, reddit_url: str,
                         upvotes: int, comments: int, upvote_ratio: float = 0.9,
                         awards: int = 0) -> PostMetrics:
        """Manually add post metrics (when API not available)"""

        metrics = PostMetrics(
            post_id=reddit_url.split('/')[-3] if '/' in reddit_url else 'manual',
            reddit_url=reddit_url,
            subreddit=subreddit,
            title="Manual Entry",
            upvotes=upvotes,
            upvote_ratio=upvote_ratio,
            num_comments=comments,
            awards=awards,
            created_utc=datetime.now().timestamp(),
            tracked_at=datetime.now().isoformat(),
            hours_since_post=0
        )

        self._save_metrics(project_name, metrics)
        return metrics

    def _save_metrics(self, project_name: str, metrics: PostMetrics):
        """Save metrics to file"""

        # Load or create analytics file
        analytics_file = self.analytics_dir / f"{project_name}.json"

        if analytics_file.exists():
            data = load_json(analytics_file)
        else:
            data = {
                "project_name": project_name,
                "posts": [],
                "summary": {}
            }

        # Add or update metrics
        post_entry = {
            **metrics.to_dict(),
            "snapshots": [metrics.to_dict()]  # Track over time
        }

        # Check if post already exists
        existing_idx = None
        for idx, post in enumerate(data["posts"]):
            if post["post_id"] == metrics.post_id:
                existing_idx = idx
                break

        if existing_idx is not None:
            # Update existing post
            data["posts"][existing_idx]["snapshots"].append(metrics.to_dict())
            data["posts"][existing_idx].update(metrics.to_dict())
        else:
            # Add new post
            data["posts"].append(post_entry)

        # Update summary
        data["summary"] = self._calculate_summary(data["posts"])
        data["last_updated"] = datetime.now().isoformat()

        save_json(data, analytics_file)

    def _calculate_summary(self, posts: List[Dict]) -> Dict:
        """Calculate summary statistics"""

        if not posts:
            return {}

        total_upvotes = sum(p["upvotes"] for p in posts)
        total_comments = sum(p["num_comments"] for p in posts)
        total_awards = sum(p["awards"] for p in posts)
        avg_upvote_ratio = sum(p["upvote_ratio"] for p in posts) / len(posts)

        # Find best performing post
        best_post = max(posts, key=lambda p: p["upvotes"])

        # Subreddit breakdown
        subreddit_stats = {}
        for post in posts:
            sub = post["subreddit"]
            if sub not in subreddit_stats:
                subreddit_stats[sub] = {
                    "count": 0,
                    "total_upvotes": 0,
                    "total_comments": 0
                }
            subreddit_stats[sub]["count"] += 1
            subreddit_stats[sub]["total_upvotes"] += post["upvotes"]
            subreddit_stats[sub]["total_comments"] += post["num_comments"]

        return {
            "total_posts": len(posts),
            "total_upvotes": total_upvotes,
            "total_comments": total_comments,
            "total_awards": total_awards,
            "avg_upvotes_per_post": total_upvotes / len(posts),
            "avg_comments_per_post": total_comments / len(posts),
            "avg_upvote_ratio": avg_upvote_ratio,
            "best_post": {
                "subreddit": best_post["subreddit"],
                "upvotes": best_post["upvotes"],
                "comments": best_post["num_comments"],
                "url": best_post["reddit_url"]
            },
            "subreddit_breakdown": subreddit_stats
        }

    def get_project_analytics(self, project_name: str) -> Optional[Dict]:
        """Get analytics for a specific project"""

        analytics_file = self.analytics_dir / f"{project_name}.json"

        if not analytics_file.exists():
            return None

        return load_json(analytics_file)

    def get_all_analytics(self) -> List[Dict]:
        """Get analytics for all projects"""

        all_analytics = []

        for analytics_file in self.analytics_dir.glob("*.json"):
            data = load_json(analytics_file)
            all_analytics.append(data)

        return all_analytics

    def get_leaderboard(self, metric: str = "upvotes", limit: int = 10) -> List[Dict]:
        """Get leaderboard of top posts by metric"""

        all_posts = []

        for analytics_file in self.analytics_dir.glob("*.json"):
            data = load_json(analytics_file)
            for post in data.get("posts", []):
                post["project_name"] = data["project_name"]
                all_posts.append(post)

        # Sort by metric
        if metric in ["upvotes", "num_comments", "awards"]:
            sorted_posts = sorted(all_posts, key=lambda p: p.get(metric, 0), reverse=True)
        elif metric == "upvote_ratio":
            sorted_posts = sorted(all_posts, key=lambda p: p.get(metric, 0), reverse=True)
        else:
            sorted_posts = all_posts

        return sorted_posts[:limit]

    def get_subreddit_performance(self) -> Dict:
        """Get performance breakdown by subreddit"""

        subreddit_stats = {}

        for analytics_file in self.analytics_dir.glob("*.json"):
            data = load_json(analytics_file)
            for post in data.get("posts", []):
                sub = post["subreddit"]
                if sub not in subreddit_stats:
                    subreddit_stats[sub] = {
                        "posts": 0,
                        "total_upvotes": 0,
                        "total_comments": 0,
                        "total_awards": 0,
                        "avg_upvote_ratio": 0
                    }

                subreddit_stats[sub]["posts"] += 1
                subreddit_stats[sub]["total_upvotes"] += post["upvotes"]
                subreddit_stats[sub]["total_comments"] += post["num_comments"]
                subreddit_stats[sub]["total_awards"] += post.get("awards", 0)
                subreddit_stats[sub]["avg_upvote_ratio"] += post["upvote_ratio"]

        # Calculate averages
        for sub, stats in subreddit_stats.items():
            count = stats["posts"]
            stats["avg_upvotes"] = stats["total_upvotes"] / count
            stats["avg_comments"] = stats["total_comments"] / count
            stats["avg_upvote_ratio"] = stats["avg_upvote_ratio"] / count

        return subreddit_stats

    def generate_report(self, project_name: Optional[str] = None) -> str:
        """Generate a text report of analytics"""

        if project_name:
            data = self.get_project_analytics(project_name)
            if not data:
                return f"No analytics found for {project_name}"

            report = self._format_project_report(data)
        else:
            # Overall report
            all_analytics = self.get_all_analytics()
            report = self._format_overall_report(all_analytics)

        return report

    def _format_project_report(self, data: Dict) -> str:
        """Format project-specific report"""

        summary = data.get("summary", {})
        posts = data.get("posts", [])

        report = f"""
╔═══════════════════════════════════════════════════════════════
║ Analytics Report: {data['project_name']}
╚═══════════════════════════════════════════════════════════════

📊 SUMMARY
  Total Posts: {summary.get('total_posts', 0)}
  Total Upvotes: {summary.get('total_upvotes', 0)}
  Total Comments: {summary.get('total_comments', 0)}
  Total Awards: {summary.get('total_awards', 0)}

  Avg Upvotes/Post: {summary.get('avg_upvotes_per_post', 0):.1f}
  Avg Comments/Post: {summary.get('avg_comments_per_post', 0):.1f}
  Avg Upvote Ratio: {summary.get('avg_upvote_ratio', 0):.2%}

🏆 BEST PERFORMING POST
"""
        if "best_post" in summary:
            bp = summary["best_post"]
            report += f"  Subreddit: {bp['subreddit']}\n"
            report += f"  Upvotes: {bp['upvotes']}\n"
            report += f"  Comments: {bp['comments']}\n"
            report += f"  URL: {bp['url']}\n"

        report += "\n📍 SUBREDDIT BREAKDOWN\n"
        for sub, stats in summary.get('subreddit_breakdown', {}).items():
            report += f"  {sub}:\n"
            report += f"    Posts: {stats['count']}\n"
            report += f"    Total Upvotes: {stats['total_upvotes']}\n"
            report += f"    Total Comments: {stats['total_comments']}\n"
            report += f"    Avg Upvotes: {stats['total_upvotes']/stats['count']:.1f}\n\n"

        report += f"\nLast Updated: {data.get('last_updated', 'Unknown')}\n"

        return report

    def _format_overall_report(self, all_analytics: List[Dict]) -> str:
        """Format overall report across all projects"""

        total_posts = sum(a.get('summary', {}).get('total_posts', 0) for a in all_analytics)
        total_upvotes = sum(a.get('summary', {}).get('total_upvotes', 0) for a in all_analytics)
        total_comments = sum(a.get('summary', {}).get('total_comments', 0) for a in all_analytics)

        report = f"""
╔═══════════════════════════════════════════════════════════════
║ Overall Analytics Report
╚═══════════════════════════════════════════════════════════════

📊 GLOBAL SUMMARY
  Total Projects Tracked: {len(all_analytics)}
  Total Posts: {total_posts}
  Total Upvotes: {total_upvotes}
  Total Comments: {total_comments}

🏆 TOP POSTS (by upvotes)
"""

        leaderboard = self.get_leaderboard(metric="upvotes", limit=5)
        for i, post in enumerate(leaderboard, 1):
            report += f"  {i}. {post['project_name']} @ {post['subreddit']}\n"
            report += f"     ⬆ {post['upvotes']} upvotes | 💬 {post['num_comments']} comments\n\n"

        report += "\n📍 SUBREDDIT PERFORMANCE\n"
        subreddit_perf = self.get_subreddit_performance()

        # Sort by avg upvotes
        sorted_subs = sorted(
            subreddit_perf.items(),
            key=lambda x: x[1]['avg_upvotes'],
            reverse=True
        )

        for sub, stats in sorted_subs:
            report += f"  {sub}:\n"
            report += f"    Posts: {stats['posts']}\n"
            report += f"    Avg Upvotes: {stats['avg_upvotes']:.1f}\n"
            report += f"    Avg Comments: {stats['avg_comments']:.1f}\n"
            report += f"    Avg Upvote Ratio: {stats['avg_upvote_ratio']:.1%}\n\n"

        return report
