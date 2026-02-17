"""Post Preview Generator - Generate Reddit-style previews of posts"""

import markdown
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import re

from .config import GENERATED_POSTS_DIR
from .utils import load_json

class PreviewGenerator:
    def __init__(self):
        """Initialize preview generator"""
        self.reddit_css = self._get_reddit_css()

    def generate_preview(self, post_file: Path, output_dir: Optional[Path] = None) -> Path:
        """Generate HTML preview of a Reddit post"""

        # Read post content
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse post metadata
        metadata = self._parse_post_metadata(content)

        # Extract title and body
        title = metadata.get('title', 'Untitled Post')
        body_md = self._extract_body(content)

        # Convert markdown to HTML
        body_html = self._markdown_to_reddit_html(body_md)

        # Generate preview HTML
        preview_html = self._generate_html(
            title=title,
            body=body_html,
            subreddit=metadata.get('subreddit', 'r/unknown'),
            flair=metadata.get('flair', ''),
            estimated_engagement=metadata.get('estimated_engagement', 'medium')
        )

        # Save preview
        if output_dir is None:
            output_dir = post_file.parent

        preview_file = output_dir / f"{post_file.stem}_preview.html"
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(preview_html)

        return preview_file

    def generate_all_previews(self, project_dir: Path):
        """Generate previews for all posts in a project"""
        previews = []

        for post_file in project_dir.glob("r-*.md"):
            try:
                preview_file = self.generate_preview(post_file)
                previews.append(preview_file)
                print(f"✓ Generated preview: {preview_file.name}")
            except Exception as e:
                print(f"✗ Failed to generate preview for {post_file.name}: {e}")

        return previews

    def _parse_post_metadata(self, content: str) -> Dict:
        """Parse metadata from post content"""
        metadata = {}

        # Extract title (first heading)
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1)

        # Extract metadata fields
        for field in ['Subreddit', 'Flair', 'Estimated Engagement', 'Generated']:
            pattern = rf'\*\*{field}:\*\* (.+)$'
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                metadata[field.lower().replace(' ', '_')] = match.group(1)

        return metadata

    def _extract_body(self, content: str) -> str:
        """Extract post body (between separators)"""
        # Find content between --- separators
        parts = content.split('---')
        if len(parts) >= 3:
            return parts[1].strip()
        return content

    def _markdown_to_reddit_html(self, md_text: str) -> str:
        """Convert markdown to HTML with Reddit-style formatting"""

        # Use python-markdown with extensions
        html = markdown.markdown(
            md_text,
            extensions=[
                'extra',
                'codehilite',
                'nl2br',
                'sane_lists'
            ]
        )

        return html

    def _generate_html(self, title: str, body: str, subreddit: str,
                       flair: str, estimated_engagement: str) -> str:
        """Generate complete HTML preview"""

        # Engagement color
        engagement_colors = {
            'high': '#46d160',
            'medium': '#ffa500',
            'low': '#ff4500'
        }
        engagement_key = (estimated_engagement or 'medium').lower().split()[0]
        engagement_color = engagement_colors.get(engagement_key, '#808080')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reddit Post Preview - {title[:50]}</title>
    <style>
        {self.reddit_css}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="preview-header">
            <h1>📱 Reddit Post Preview</h1>
            <p class="preview-note">This is how your post will appear on Reddit</p>
        </div>

        <div class="reddit-post">
            <div class="post-header">
                <div class="votes">
                    <div class="arrow up">▲</div>
                    <div class="score">•</div>
                    <div class="arrow down">▼</div>
                </div>

                <div class="post-content-wrapper">
                    <div class="post-meta">
                        <span class="subreddit">{subreddit}</span>
                        <span class="separator">•</span>
                        <span class="author">Posted by u/YourUsername</span>
                        <span class="separator">•</span>
                        <span class="time">just now</span>
                        {f'<span class="flair">{flair}</span>' if flair else ''}
                    </div>

                    <h2 class="post-title">{title}</h2>

                    <div class="post-body">
                        {body}
                    </div>

                    <div class="post-actions">
                        <button class="action-btn">💬 Comment</button>
                        <button class="action-btn">🔗 Share</button>
                        <button class="action-btn">🔖 Save</button>
                        <button class="action-btn">⋯</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="preview-footer">
            <div class="engagement-indicator">
                <span class="label">Estimated Engagement:</span>
                <span class="badge" style="background-color: {engagement_color};">
                    {estimated_engagement.upper()}
                </span>
            </div>
            <div class="tips">
                <h3>💡 Preview Tips:</h3>
                <ul>
                    <li>Check title length (should be under 300 chars)</li>
                    <li>Verify formatting renders correctly</li>
                    <li>Ensure links are working</li>
                    <li>Check if content fits mobile screens</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        // Add character count for title
        const title = document.querySelector('.post-title');
        if (title) {{
            const charCount = title.textContent.length;
            const badge = document.createElement('span');
            badge.className = 'char-count';
            badge.textContent = `${{charCount}}/300 chars`;
            badge.style.cssText = `
                display: inline-block;
                margin-left: 10px;
                padding: 2px 8px;
                background: ${{charCount > 300 ? '#ff4500' : '#46d160'}};
                color: white;
                border-radius: 3px;
                font-size: 11px;
                font-weight: normal;
            `;
            title.appendChild(badge);
        }}
    </script>
</body>
</html>"""

        return html

    def _get_reddit_css(self) -> str:
        """Return Reddit-style CSS"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #dae0e6;
            color: #1c1c1c;
            line-height: 1.5;
            padding: 20px;
        }

        .preview-container {
            max-width: 900px;
            margin: 0 auto;
        }

        .preview-header {
            background: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
            border-bottom: 2px solid #ff4500;
        }

        .preview-header h1 {
            color: #1c1c1c;
            font-size: 24px;
            margin-bottom: 5px;
        }

        .preview-note {
            color: #7c7c7c;
            font-size: 14px;
        }

        .reddit-post {
            background: white;
            border-radius: 0;
            overflow: hidden;
            margin-bottom: 0;
        }

        .post-header {
            display: flex;
            padding: 8px;
        }

        .votes {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px 4px;
            margin-right: 8px;
        }

        .arrow {
            color: #878a8c;
            cursor: pointer;
            font-size: 20px;
            user-select: none;
        }

        .arrow.up:hover {
            color: #ff4500;
        }

        .arrow.down:hover {
            color: #7193ff;
        }

        .score {
            font-weight: 700;
            font-size: 12px;
            margin: 4px 0;
            color: #1c1c1c;
        }

        .post-content-wrapper {
            flex: 1;
            padding: 8px;
        }

        .post-meta {
            font-size: 12px;
            color: #7c7c7c;
            margin-bottom: 8px;
        }

        .subreddit {
            font-weight: 700;
            color: #1c1c1c;
        }

        .separator {
            margin: 0 4px;
        }

        .flair {
            background: #0079d3;
            color: white;
            padding: 2px 8px;
            border-radius: 2px;
            font-size: 11px;
            font-weight: 500;
            margin-left: 8px;
        }

        .post-title {
            font-size: 18px;
            font-weight: 500;
            color: #1c1c1c;
            margin: 8px 0;
            line-height: 1.3;
        }

        .post-body {
            color: #1c1c1c;
            margin: 12px 0;
            font-size: 14px;
            line-height: 1.6;
        }

        .post-body h2 {
            font-size: 18px;
            margin: 16px 0 8px 0;
            font-weight: 600;
        }

        .post-body h3 {
            font-size: 16px;
            margin: 14px 0 6px 0;
            font-weight: 600;
        }

        .post-body p {
            margin: 8px 0;
        }

        .post-body ul, .post-body ol {
            margin: 8px 0;
            padding-left: 24px;
        }

        .post-body li {
            margin: 4px 0;
        }

        .post-body code {
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }

        .post-body pre {
            background: #f6f8fa;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 12px 0;
        }

        .post-body pre code {
            background: none;
            padding: 0;
        }

        .post-body a {
            color: #0079d3;
            text-decoration: none;
        }

        .post-body a:hover {
            text-decoration: underline;
        }

        .post-body blockquote {
            border-left: 4px solid #ccc;
            padding-left: 16px;
            margin: 12px 0;
            color: #555;
        }

        .post-actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #edeff1;
        }

        .action-btn {
            background: none;
            border: none;
            color: #878a8c;
            font-size: 12px;
            font-weight: 700;
            padding: 8px 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .action-btn:hover {
            background: #f6f7f8;
            border-radius: 2px;
        }

        .preview-footer {
            background: white;
            padding: 20px;
            border-radius: 0 0 8px 8px;
            border-top: 1px solid #edeff1;
        }

        .engagement-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f6f7f8;
            border-radius: 4px;
        }

        .engagement-indicator .label {
            font-weight: 600;
            color: #1c1c1c;
        }

        .engagement-indicator .badge {
            padding: 4px 12px;
            border-radius: 12px;
            color: white;
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 0.5px;
        }

        .tips {
            color: #1c1c1c;
        }

        .tips h3 {
            font-size: 16px;
            margin-bottom: 10px;
        }

        .tips ul {
            list-style: none;
            padding-left: 0;
        }

        .tips li {
            padding: 6px 0;
            padding-left: 24px;
            position: relative;
        }

        .tips li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #46d160;
            font-weight: bold;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }

            .post-title {
                font-size: 16px;
            }

            .post-body {
                font-size: 13px;
            }
        }
        """
