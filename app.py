"""
PostAgent Web Interface
Lightweight Flask frontend for managing GitHub repositories and generating Reddit posts
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from src.config import CSV_FILE_PATH, GENERATED_POSTS_DIR, validate_config
from src.github_analyzer import GitHubAnalyzer
from src.subreddit_matcher import SubredditMatcher
from src.content_generator import ContentGenerator

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


def load_projects():
    """Load projects from CSV"""
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        # Ensure required columns exist
        if 'Content Title' not in df.columns or 'Github Repo' not in df.columns:
            return pd.DataFrame(columns=['Content Title', 'Github Repo', 's3 link/drive Link',
                                        'Youtube Link', 'Blog created on docs', 'README updated'])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['Content Title', 'Github Repo', 's3 link/drive Link',
                                    'Youtube Link', 'Blog created on docs', 'README updated'])


def save_projects(df):
    """Save projects to CSV"""
    df.to_csv(CSV_FILE_PATH, index=False)


def get_generated_posts():
    """Get all generated posts with metadata"""
    posts = []
    if GENERATED_POSTS_DIR.exists():
        for project_dir in GENERATED_POSTS_DIR.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    # Count post files
                    post_files = list(project_dir.glob("r-*.md"))
                    metadata['post_count'] = len(post_files)
                    metadata['project_name'] = project_dir.name
                    posts.append(metadata)

    # Sort by generation time (newest first)
    posts.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
    return posts


@app.route('/')
def index():
    """Home page - list all projects"""
    df = load_projects()
    projects = df.to_dict('records')

    # Add index for each project
    for idx, project in enumerate(projects):
        project['index'] = idx + 1

    return render_template('index.html', projects=projects)


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

        # Load existing projects
        df = load_projects()

        # Check if URL already exists
        if github_url in df['Github Repo'].values:
            flash('This GitHub repository is already in the list', 'warning')
            return redirect(url_for('index'))

        # Add new project
        new_row = {
            'Content Title': title,
            'Github Repo': github_url,
            's3 link/drive Link': '',
            'Youtube Link': '',
            'Blog created on docs': '',
            'README updated': ''
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_projects(df)

        flash(f'Successfully added: {title}', 'success')
        return redirect(url_for('index'))

    return render_template('add_project.html')


@app.route('/analyze/<int:row_id>')
def analyze_project(row_id):
    """Analyze a specific project"""
    df = load_projects()

    if row_id < 1 or row_id > len(df):
        return jsonify({'error': 'Invalid project ID'}), 404

    project = df.iloc[row_id - 1]
    github_url = project['Github Repo']

    try:
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
    df = load_projects()

    if row_id < 1 or row_id > len(df):
        return jsonify({'error': 'Invalid project ID'}), 404

    project = df.iloc[row_id - 1]
    github_url = project['Github Repo']
    project_title = project['Content Title']

    try:
        # Analyze repository
        analysis = analyzer.analyze_repository(github_url)

        # Match subreddits
        matches = matcher.match_subreddits(analysis)

        # Generate posts
        project_slug = project_title.lower().replace(' ', '-').replace('/', '-')
        project_dir = GENERATED_POSTS_DIR / project_slug
        project_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            'project_title': project_title,
            'github_url': github_url,
            'generated_at': datetime.now().isoformat(),
            'analysis': analysis,
            'subreddit_matches': [name for name, _, _ in matches]
        }

        with open(project_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        # Generate posts for each subreddit
        posts_generated = []
        for subreddit_name, score, subreddit_info in matches[:5]:  # Top 5 subreddits
            post = generator.generate_post(analysis, subreddit_name, subreddit_info)

            # Save post with project name in filename
            subreddit_clean = subreddit_name.lower().replace('r/', '').replace('/', '-')
            post_filename = f"{project_slug}-{subreddit_clean}.md"
            post_path = project_dir / post_filename

            with open(post_path, 'w') as f:
                f.write(f"# {post['title']}\n\n")
                f.write(f"**Subreddit:** {subreddit_name}\n")
                f.write(f"**Suggested Flair:** {post.get('flair', 'N/A')}\n")
                f.write(f"**Engagement Estimate:** {post.get('estimated_engagement', 'N/A')}\n\n")
                f.write("---\n\n")
                f.write(post.get('body', ''))

            posts_generated.append({
                'subreddit': subreddit_name,
                'filename': post_filename,
                'title': post['title']
            })

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
    posts = get_generated_posts()
    return render_template('posts.html', posts=posts)


@app.route('/posts/<project_slug>')
def view_project_posts(project_slug):
    """View posts for a specific project"""
    project_dir = GENERATED_POSTS_DIR / project_slug

    if not project_dir.exists():
        flash('Project not found', 'error')
        return redirect(url_for('view_posts'))

    # Load metadata
    metadata_file = project_dir / 'metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # Load all posts
    posts = []
    for post_file in project_dir.glob('r-*.md'):
        with open(post_file, 'r') as f:
            content = f.read()

        posts.append({
            'filename': post_file.name,
            'subreddit': post_file.stem,
            'content': content
        })

    return render_template('project_posts.html',
                          project_slug=project_slug,
                          metadata=metadata,
                          posts=posts)


@app.route('/delete/<int:row_id>', methods=['POST'])
def delete_project(row_id):
    """Delete a project from the list"""
    df = load_projects()

    if row_id < 1 or row_id > len(df):
        return jsonify({'error': 'Invalid project ID'}), 404

    project_title = df.iloc[row_id - 1]['Content Title']
    df = df.drop(row_id - 1).reset_index(drop=True)
    save_projects(df)

    flash(f'Successfully deleted: {project_title}', 'success')
    return jsonify({'success': True})


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        validate_config()
        return jsonify({
            'status': 'healthy',
            'projects_count': len(load_projects()),
            'generated_posts_count': len(get_generated_posts())
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
