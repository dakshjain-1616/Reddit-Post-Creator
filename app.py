"""
PostAgent Web Interface
Lightweight Flask frontend for managing GitHub repositories and generating Reddit posts
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
from pathlib import Path
from datetime import datetime
from src.config import validate_config
from src.github_analyzer import GitHubAnalyzer
from src.subreddit_matcher import SubredditMatcher
from src.content_generator import ContentGenerator
from src.database import (
    get_all_projects, get_project_by_id, add_project as db_add_project,
    delete_project as db_delete_project, project_exists,
    save_generated_posts as db_save_posts, get_all_generated_posts,
    get_project_posts, get_projects_count, get_generated_posts_count
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# Production configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_SORT_KEYS'] = False

# Initialize components
try:
    analyzer = GitHubAnalyzer()
    matcher = SubredditMatcher()
    generator = ContentGenerator()
except Exception as e:
    print(f"Warning: Failed to initialize components: {e}")
    analyzer = None
    matcher = None
    generator = None


# Database-backed functions (no more CSV/filesystem)
# All data is now stored in Vercel Postgres


@app.route('/')
def index():
    """Home page - list all projects"""
    try:
        projects = get_all_projects()
        return render_template('index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'error')
        return render_template('index.html', projects=[])


@app.route('/add', methods=['GET', 'POST'])
def add_project():
    """Add new GitHub repository"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        github_url = request.form.get('github_url', '').strip()

        if not github_url:
            flash('GitHub URL is required', 'error')
            return redirect(url_for('add_project'))

        if not title:
            # Extract title from GitHub URL
            parts = github_url.rstrip('/').split('/')
            title = parts[-1] if parts else 'Untitled Project'

        # Check if URL already exists
        try:
            if project_exists(github_url):
                flash('This GitHub repository is already in the list', 'warning')
                return redirect(url_for('index'))

            # Add new project to database
            db_add_project(title, github_url)
            flash(f'Successfully added: {title}', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding project: {str(e)}', 'error')
            return redirect(url_for('add_project'))

    return render_template('add_project.html')


@app.route('/analyze/<int:row_id>')
def analyze_project(row_id):
    """Analyze a specific project"""
    try:
        project = get_project_by_id(row_id)

        if not project:
            return jsonify({'error': 'Invalid project ID'}), 404

        github_url = project['Github Repo']

        # Analyze repository
        analysis = analyzer.analyze_repository(github_url)

        # Match subreddits
        matches = matcher.match_subreddits(analysis)
        subreddit_matches = [
            {'name': name, 'score': score, 'info': info}
            for name, score, info in matches
        ]

        return jsonify({
            'success': True,
            'analysis': analysis,
            'subreddit_matches': subreddit_matches
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/generate/<int:row_id>', methods=['POST'])
def generate_posts(row_id):
    """Generate Reddit posts for a project"""
    try:
        project = get_project_by_id(row_id)

        if not project:
            return jsonify({'error': 'Invalid project ID'}), 404

        github_url = project['Github Repo']
        project_title = project['Content Title']

        # Analyze repository
        analysis = analyzer.analyze_repository(github_url)

        # Match subreddits
        matches = matcher.match_subreddits(analysis)

        # Generate posts
        project_slug = project_title.lower().replace(' ', '-').replace('/', '-')

        # Prepare metadata
        metadata = {
            'analysis': analysis,
            'subreddit_matches': [name for name, _, _ in matches]
        }

        # Generate posts for each subreddit
        posts_generated = []
        for subreddit_name, score, subreddit_info in matches[:5]:  # Top 5 subreddits
            post = generator.generate_post(analysis, subreddit_name, subreddit_info)

            subreddit_clean = subreddit_name.lower().replace('r/', '').replace('/', '-')
            post_filename = f"{project_slug}-{subreddit_clean}.md"

            posts_generated.append({
                'subreddit': subreddit_name,
                'filename': post_filename,
                'title': post['title'],
                'body': post.get('body', ''),
                'flair': post.get('flair', 'N/A'),
                'estimated_engagement': post.get('estimated_engagement', 'N/A')
            })

        # Save all posts to database
        db_save_posts(project_slug, project_title, github_url, posts_generated, metadata)

        flash(f'Successfully generated {len(posts_generated)} posts for {project_title}', 'success')
        return jsonify({
            'success': True,
            'posts': posts_generated,
            'project_slug': project_slug
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/posts')
def view_posts():
    """View all generated posts"""
    try:
        posts = get_all_generated_posts()
        return render_template('posts.html', posts=posts)
    except Exception as e:
        flash(f'Error loading posts: {str(e)}', 'error')
        return render_template('posts.html', posts=[])


@app.route('/posts/<project_slug>')
def view_project_posts(project_slug):
    """View posts for a specific project"""
    try:
        project_data = get_project_posts(project_slug)

        if not project_data:
            flash('Project not found', 'error')
            return redirect(url_for('view_posts'))

        # Format posts for display
        posts = []
        for post in project_data['posts']:
            # Recreate markdown format for display
            content = f"# {post['title']}\n\n"
            content += f"**Subreddit:** {post['subreddit']}\n"
            content += f"**Suggested Flair:** {post.get('flair', 'N/A')}\n"
            content += f"**Engagement Estimate:** {post.get('estimated_engagement', 'N/A')}\n\n"
            content += "---\n\n"
            content += post['body']

            posts.append({
                'filename': post['filename'],
                'subreddit': post['subreddit'],
                'content': content
            })

        return render_template('project_posts.html',
                              project_slug=project_slug,
                              metadata=project_data['metadata'],
                              posts=posts)
    except Exception as e:
        flash(f'Error loading project posts: {str(e)}', 'error')
        return redirect(url_for('view_posts'))


@app.route('/delete/<int:row_id>', methods=['POST'])
def delete_project(row_id):
    """Delete a project from the list"""
    try:
        project_title = db_delete_project(row_id)

        if not project_title:
            return jsonify({'error': 'Invalid project ID'}), 404

        flash(f'Successfully deleted: {project_title}', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        validate_config()
        return jsonify({
            'status': 'healthy',
            'projects_count': get_projects_count(),
            'generated_posts_count': get_generated_posts_count()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Validate configuration (but don't exit if it fails)
    try:
        validate_config()
        config_valid = True
    except ValueError as e:
        print(f"\n⚠️  Configuration Warning:\n{e}\n")
        print("You can still browse the interface, but you'll need to fix")
        print("the configuration to generate posts.\n")
        config_valid = False

    # Check if running in production
    is_production = os.getenv('VERCEL') or os.getenv('FLASK_ENV') == 'production'

    if not is_production:
        print("\n" + "="*60)
        print("PostAgent Web Interface")
        print("="*60)
        print("\nStarting server at http://0.0.0.0:5000")
        print("Access from:")
        print("  - This machine: http://localhost:5000")
        print("  - Other machines: http://<your-ip>:5000")
        print("\nPress Ctrl+C to stop\n")

    app.run(debug=not is_production, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
