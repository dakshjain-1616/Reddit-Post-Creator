"""Subreddit Matcher - Match projects to relevant subreddits"""

from typing import List, Dict, Tuple
from pathlib import Path
import json

from .config import SUBREDDIT_DB_PATH
from .utils import load_json

class SubredditMatcher:
    def __init__(self):
        """Initialize with subreddit database"""
        if SUBREDDIT_DB_PATH.exists():
            self.subreddit_db = load_json(SUBREDDIT_DB_PATH)
        else:
            raise FileNotFoundError(f"Subreddit database not found at {SUBREDDIT_DB_PATH}")

    def match_subreddits(self, project_analysis: Dict, top_n: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        Match project to relevant subreddits
        Returns list of (subreddit_name, relevance_score, subreddit_info)
        """
        scores = []

        for subreddit_name, subreddit_info in self.subreddit_db.items():
            score = self._calculate_relevance_score(project_analysis, subreddit_info)
            scores.append((subreddit_name, score, subreddit_info))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_n]

    def _calculate_relevance_score(self, project_analysis: Dict, subreddit_info: Dict) -> float:
        """Calculate relevance score between project and subreddit"""
        score = 0.0

        # Extract project details
        analysis = project_analysis.get("analysis", {})
        repo_data = {
            "name": (project_analysis.get("name") or "").lower(),
            "description": (project_analysis.get("description") or "").lower(),
            "topics": [t.lower() for t in project_analysis.get("topics", []) if t],
            "languages": [l.lower() for l in project_analysis.get("languages", []) if l],
            "readme": (project_analysis.get("readme") or "").lower(),
        }

        analysis_data = {
            "synopsis": (analysis.get("synopsis") or "").lower(),
            "technical_stack": [t.lower() for t in analysis.get("technical_stack", []) if t],
            "use_cases": [u.lower() for u in analysis.get("use_cases", []) if u],
            "key_features": [f.lower() for f in analysis.get("key_features", []) if f],
        }

        # Combine all project text
        project_text = " ".join([
            repo_data["name"],
            repo_data["description"],
            " ".join(repo_data["topics"]),
            analysis_data["synopsis"],
            " ".join(analysis_data["technical_stack"]),
            " ".join(analysis_data["use_cases"]),
        ])

        # Score based on keyword matches
        subreddit_keywords = subreddit_info.get("keywords", [])
        for keyword in subreddit_keywords:
            if keyword.lower() in project_text:
                score += 2.0

        # Score based on topic matches
        subreddit_topics = subreddit_info.get("topics", [])
        for topic in subreddit_topics:
            topic_keywords = topic.replace("_", " ").split()
            if any(kw in project_text for kw in topic_keywords):
                score += 1.5

        # Bonus for direct matches
        if "llm" in project_text and "llm" in subreddit_info.get("name", "").lower():
            score += 5.0

        if "vision" in project_text or "ocr" in project_text or "image" in project_text:
            if "computervision" in subreddit_info.get("name", "").lower():
                score += 5.0

        if "agent" in project_text and "langchain" in subreddit_info.get("name", "").lower():
            score += 5.0

        if "rag" in project_text and "langchain" in subreddit_info.get("name", "").lower():
            score += 5.0

        # Project type specific matching
        if "ocr" in project_text or "document" in project_text:
            if subreddit_info.get("name") in ["r/MachineLearning", "r/computervision", "r/datascience"]:
                score += 3.0

        if "voice" in project_text or "audio" in project_text or "speech" in project_text:
            if subreddit_info.get("name") in ["r/MachineLearning", "r/learnmachinelearning"]:
                score += 3.0

        if "training" in project_text or "optimization" in project_text:
            if subreddit_info.get("name") in ["r/MLOps", "r/MachineLearning", "r/deeplearning"]:
                score += 3.0

        # Adjust for audience level
        technical_indicators = ["architecture", "optimization", "training", "model", "neural"]
        technical_count = sum(1 for ind in technical_indicators if ind in project_text)

        if technical_count > 3:  # Highly technical project
            if subreddit_info.get("audience_level") in ["advanced", "intermediate_to_advanced"]:
                score += 2.0
        else:  # More accessible project
            if subreddit_info.get("audience_level") in ["beginner", "beginner_to_intermediate"]:
                score += 1.0

        return score

    def get_subreddit_info(self, subreddit_name: str) -> Dict:
        """Get information about a specific subreddit"""
        return self.subreddit_db.get(subreddit_name, {})

    def get_all_subreddits(self) -> List[str]:
        """Get list of all available subreddits"""
        return list(self.subreddit_db.keys())

    def get_posting_guidelines(self, subreddit_name: str) -> str:
        """Get formatted posting guidelines for a subreddit"""
        info = self.get_subreddit_info(subreddit_name)

        if not info:
            return f"No information available for {subreddit_name}"

        guidelines = f"""
## {info['name']} Posting Guidelines

**Description:** {info['description']}
**Audience Level:** {info['audience_level'].replace('_', ' ').title()}
**Tone:** {info['tone']}

**Posting Rules:**
{chr(10).join(f"  - {rule}" for rule in info['posting_rules'])}

**Preferred Flairs:** {', '.join(info['preferred_flairs'])}

**Key Topics:** {', '.join(info['topics'])}
"""
        return guidelines.strip()
