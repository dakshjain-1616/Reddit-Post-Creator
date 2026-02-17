"""CLI Interface for PostAgent"""

import click
import pandas as pd
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
import json

from .config import CSV_FILE_PATH, GENERATED_POSTS_DIR, validate_config
from .github_analyzer import GitHubAnalyzer
from .subreddit_matcher import SubredditMatcher
from .content_generator import ContentGenerator
from .preview_generator import PreviewGenerator
from .analytics import AnalyticsTracker
from .utils import sanitize_filename, save_json, load_json

console = Console()


@click.group()
def cli():
    """PostAgent: Automated Reddit Post Generator for NEO Projects"""
    pass


@cli.command()
@click.argument('repo_url')
def analyze(repo_url):
    """Analyze a single GitHub repository"""
    try:
        validate_config()

        analyzer = GitHubAnalyzer()

        with console.status("[bold green]Analyzing repository..."):
            analysis = analyzer.analyze_repository(repo_url)

        console.print("\n[bold green]✓ Analysis Complete![/bold green]\n")

        # Display results
        console.print(Panel.fit(f"[bold]{analysis['name']}[/bold]\n{analysis['description']}"))

        console.print("\n[bold cyan]Repository Stats:[/bold cyan]")
        console.print(f"  ⭐ Stars: {analysis['stars']}")
        console.print(f"  🔱 Forks: {analysis['forks']}")
        console.print(f"  💻 Languages: {', '.join(analysis['languages'][:5])}")

        analysis_data = analysis['analysis']

        console.print("\n[bold cyan]Top 3 Value Propositions:[/bold cyan]")
        for i, value in enumerate(analysis_data['top_3_values'], 1):
            console.print(f"  {i}. {value}")

        console.print(f"\n[bold cyan]Synopsis:[/bold cyan]\n{analysis_data['synopsis']}")

        console.print("\n[bold cyan]Key Features:[/bold cyan]")
        for feature in analysis_data['key_features']:
            console.print(f"  • {feature}")

        console.print(f"\n[bold cyan]Build Further with NEO:[/bold cyan]\n{analysis_data['build_further_with_neo']}")

        # Save analysis
        output_dir = GENERATED_POSTS_DIR / sanitize_filename(analysis['name'])
        output_dir.mkdir(parents=True, exist_ok=True)

        analysis_file = output_dir / "analysis.json"
        save_json(analysis, analysis_file)

        console.print(f"\n[dim]Analysis saved to: {analysis_file}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
@click.option('--all', 'process_all', is_flag=True, help='Process all repos from CSV')
@click.option('--row', type=int, help='Process specific CSV row number (1-indexed)')
@click.option('--limit', type=int, default=5, help='Max number of repos to process')
def generate(process_all, row, limit):
    """Generate Reddit posts from CSV"""
    try:
        validate_config()

        # Load CSV
        df = pd.read_csv(CSV_FILE_PATH)

        if row:
            # Process specific row
            if row < 1 or row > len(df):
                console.print(f"[bold red]Error:[/bold red] Row {row} out of range (1-{len(df)})")
                raise click.Abort()

            repos_to_process = df.iloc[[row - 1]]
            console.print(f"[bold]Processing row {row}...[/bold]\n")

        elif process_all:
            repos_to_process = df.head(limit)
            console.print(f"[bold]Processing {len(repos_to_process)} repositories...[/bold]\n")

        else:
            console.print("[yellow]Please specify --all or --row N[/yellow]")
            console.print("Example: postagent generate --row 1")
            raise click.Abort()

        # Initialize components
        analyzer = GitHubAnalyzer()
        matcher = SubredditMatcher()
        generator = ContentGenerator()

        for idx, repo_row in repos_to_process.iterrows():
            repo_url = repo_row['Github Repo']
            title = repo_row['Content Title']

            console.print(f"\n{'='*80}")
            console.print(f"[bold cyan]Processing:[/bold cyan] {title}")
            console.print(f"[dim]{repo_url}[/dim]")
            console.print('='*80)

            try:
                # Step 1: Analyze
                with console.status("[bold green]Analyzing repository..."):
                    analysis = analyzer.analyze_repository(repo_url)

                console.print("[green]✓[/green] Analysis complete")

                # Step 2: Match subreddits
                with console.status("[bold green]Matching subreddits..."):
                    matches = matcher.match_subreddits(analysis, top_n=5)

                console.print(f"[green]✓[/green] Found {len(matches)} relevant subreddits\n")

                # Display matches
                table = Table(title="Subreddit Matches")
                table.add_column("Rank", style="cyan")
                table.add_column("Subreddit", style="green")
                table.add_column("Score", style="yellow")
                table.add_column("Description", style="white")

                for i, (sub_name, score, sub_info) in enumerate(matches, 1):
                    table.add_row(
                        str(i),
                        sub_name,
                        f"{score:.1f}",
                        sub_info['description'][:50] + "..."
                    )

                console.print(table)

                # Ask user if they want to continue
                if not Confirm.ask("\n[bold]Generate posts for these subreddits?[/bold]", default=True):
                    console.print("[yellow]Skipped[/yellow]")
                    continue

                # Step 3: Generate posts
                console.print("\n[bold]Generating posts...[/bold]")
                posts = generator.generate_multiple_posts(analysis, matches)

                # Step 4: Save and display
                project_dir = GENERATED_POSTS_DIR / sanitize_filename(analysis['name'])
                project_dir.mkdir(parents=True, exist_ok=True)

                # Save metadata
                metadata = {
                    "project_name": analysis['name'],
                    "github_url": repo_url,
                    "generated_at": datetime.now().isoformat(),
                    "subreddits": [sub_name for sub_name, _, _ in matches],
                    "posts": {}
                }

                for subreddit_name, post_data in posts.items():
                    if "error" in post_data:
                        console.print(f"[red]✗[/red] Failed to generate post for {subreddit_name}")
                        continue

                    console.print(f"[green]✓[/green] Generated post for {subreddit_name}")

                    # Save post
                    safe_name = sanitize_filename(subreddit_name)
                    post_file = project_dir / f"{safe_name}.md"

                    post_content = f"""# {post_data['title']}

**Subreddit:** {subreddit_name}
**Flair:** {post_data['flair']}
**Estimated Engagement:** {post_data['estimated_engagement']}
**Generated:** {post_data['generated_at']}

---

{post_data['body']}

---

**Rationale:** {post_data['rationale']}
"""

                    with open(post_file, 'w', encoding='utf-8') as f:
                        f.write(post_content)

                    metadata["posts"][subreddit_name] = {
                        "file": str(post_file),
                        "published": False,
                        "title": post_data['title']
                    }

                # Save metadata
                metadata_file = project_dir / "metadata.json"
                save_json(metadata, metadata_file)

                console.print(f"\n[bold green]✓ Posts saved to:[/bold green] {project_dir}")

                # Generate previews
                console.print("\n[bold]Generating HTML previews...[/bold]")
                try:
                    preview_gen = PreviewGenerator()
                    previews = preview_gen.generate_all_previews(project_dir)
                    if previews:
                        console.print(f"[green]✓[/green] Generated {len(previews)} preview(s)")
                        console.print(f"[dim]Open preview files in browser to see Reddit-style renders[/dim]")
                except Exception as preview_err:
                    console.print(f"[yellow]⚠[/yellow] Preview generation failed: {preview_err}")

            except Exception as e:
                console.print(f"[bold red]Error processing {title}:[/bold red] {str(e)}")
                continue

        console.print(f"\n[bold green]{'='*80}")
        console.print("Generation complete!")
        console.print(f"{'='*80}[/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
def review():
    """Review generated posts"""
    try:
        # Find all generated projects
        projects = [d for d in GENERATED_POSTS_DIR.iterdir() if d.is_dir()]

        if not projects:
            console.print("[yellow]No generated posts found.[/yellow]")
            console.print(f"Generate posts first with: [cyan]postagent generate --all[/cyan]")
            return

        console.print(f"[bold]Found {len(projects)} projects with generated posts[/bold]\n")

        for project_dir in sorted(projects):
            metadata_file = project_dir / "metadata.json"

            if not metadata_file.exists():
                continue

            metadata = load_json(metadata_file)

            console.print(f"\n{'='*80}")
            console.print(f"[bold cyan]Project:[/bold cyan] {metadata['project_name']}")
            console.print(f"[dim]{metadata['github_url']}[/dim]")
            console.print('='*80)

            # Display posts
            for subreddit, post_info in metadata['posts'].items():
                post_file = Path(post_info['file'])

                if not post_file.exists():
                    continue

                status = "✓ Published" if post_info.get('published') else "○ Not Published"
                console.print(f"\n[bold]{subreddit}[/bold] [{('green' if post_info.get('published') else 'yellow')}]{status}[/]")
                console.print(f"[dim]File: {post_file.name}[/dim]")

                # Show preview
                if Confirm.ask("Show post preview?", default=False):
                    with open(post_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    console.print(Panel(Markdown(content), title=subreddit, border_style="cyan"))

                    # Options
                    action = Prompt.ask(
                        "Action",
                        choices=["next", "edit", "mark_published", "quit"],
                        default="next"
                    )

                    if action == "edit":
                        console.print(f"[cyan]Edit file at:[/cyan] {post_file}")
                        console.print("[dim]Press Enter when done...[/dim]")
                        input()

                    elif action == "mark_published":
                        publisher = Prompt.ask("Your name")
                        post_info['published'] = True
                        post_info['published_by'] = publisher
                        post_info['published_at'] = datetime.now().isoformat()
                        save_json(metadata, metadata_file)
                        console.print("[green]✓ Marked as published[/green]")

                    elif action == "quit":
                        return

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
@click.argument('post_path')
@click.option('--publisher', prompt='Your name', help='Name of person publishing')
def publish(post_path, publisher):
    """Mark a post as published"""
    try:
        post_file = Path(post_path)

        if not post_file.is_absolute():
            post_file = GENERATED_POSTS_DIR / post_path

        if not post_file.exists():
            console.print(f"[bold red]Error:[/bold red] Post file not found: {post_file}")
            raise click.Abort()

        # Find metadata
        project_dir = post_file.parent
        metadata_file = project_dir / "metadata.json"

        if not metadata_file.exists():
            console.print(f"[bold red]Error:[/bold red] Metadata file not found")
            raise click.Abort()

        metadata = load_json(metadata_file)

        # Update status
        post_filename = str(post_file)
        for subreddit, post_info in metadata['posts'].items():
            if post_info['file'] == post_filename or post_file.name in post_info['file']:
                post_info['published'] = True
                post_info['published_by'] = publisher
                post_info['published_at'] = datetime.now().isoformat()

                save_json(metadata, metadata_file)

                console.print(f"[bold green]✓ Marked as published by {publisher}[/bold green]")
                console.print(f"Subreddit: {subreddit}")
                console.print(f"Time: {post_info['published_at']}")
                return

        console.print(f"[yellow]Warning:[/yellow] Post not found in metadata")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
def list_projects():
    """List all projects in CSV"""
    try:
        df = pd.read_csv(CSV_FILE_PATH)

        table = Table(title="NEO Projects")
        table.add_column("#", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("GitHub URL", style="blue")
        table.add_column("Status", style="yellow")

        for idx, row in df.iterrows():
            # Check if posts exist
            project_name = sanitize_filename(row['Content Title'])
            project_dir = GENERATED_POSTS_DIR / project_name
            status = "Generated" if project_dir.exists() else "Not Generated"

            table.add_row(
                str(idx + 1),
                row['Content Title'][:40],
                row['Github Repo'][:50],
                status
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(df)} projects[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
def status():
    """Show generation status"""
    try:
        df = pd.read_csv(CSV_FILE_PATH)

        generated_count = 0
        published_count = 0
        total_posts = 0

        for project_dir in GENERATED_POSTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue

            metadata_file = project_dir / "metadata.json"
            if metadata_file.exists():
                generated_count += 1
                metadata = load_json(metadata_file)

                for post_info in metadata['posts'].values():
                    total_posts += 1
                    if post_info.get('published'):
                        published_count += 1

        console.print("\n[bold]PostAgent Status[/bold]\n")
        console.print(f"Total Projects: {len(df)}")
        console.print(f"Generated: {generated_count}")
        console.print(f"Remaining: {len(df) - generated_count}")
        console.print(f"\nTotal Posts: {total_posts}")
        console.print(f"Published: {published_count}")
        console.print(f"Unpublished: {total_posts - published_count}\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
@click.option('--project', help='Project name/directory')
@click.option('--all', 'preview_all', is_flag=True, help='Generate previews for all posts')
def preview(project, preview_all):
    """Generate HTML previews of posts"""
    try:
        generator = PreviewGenerator()

        if preview_all:
            # Generate previews for all projects
            projects = [d for d in GENERATED_POSTS_DIR.iterdir() if d.is_dir()]

            console.print(f"[bold]Generating previews for {len(projects)} projects...[/bold]\n")

            for project_dir in projects:
                console.print(f"\n[cyan]{project_dir.name}[/cyan]")
                previews = generator.generate_all_previews(project_dir)

                if previews:
                    console.print(f"[green]✓[/green] Generated {len(previews)} preview(s)")

        elif project:
            # Generate previews for specific project
            project_dir = GENERATED_POSTS_DIR / sanitize_filename(project)

            if not project_dir.exists():
                console.print(f"[red]Error:[/red] Project directory not found: {project_dir}")
                raise click.Abort()

            console.print(f"[bold]Generating previews for {project}...[/bold]\n")
            previews = generator.generate_all_previews(project_dir)

            if previews:
                console.print(f"\n[green]✓ Generated {len(previews)} preview(s)[/green]")
                console.print("\n[bold]Preview files:[/bold]")
                for preview_file in previews:
                    console.print(f"  📄 {preview_file}")
                    console.print(f"     file://{preview_file.absolute()}")

                console.print("\n[dim]Open these HTML files in your browser to see Reddit-style previews[/dim]")
        else:
            console.print("[yellow]Please specify --project NAME or --all[/yellow]")
            console.print("Example: postagent preview --project multi-model-invoice-ocr")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
@click.argument('reddit_url')
@click.option('--project', required=True, help='Project name')
@click.option('--subreddit', required=True, help='Subreddit name (e.g., r/MachineLearning)')
@click.option('--manual', is_flag=True, help='Manually enter metrics')
@click.option('--upvotes', type=int, help='Manual upvotes count')
@click.option('--comments', type=int, help='Manual comments count')
def track(reddit_url, project, subreddit, manual, upvotes, comments):
    """Track a published post's performance"""
    try:
        tracker = AnalyticsTracker()

        console.print(f"\n[bold]Tracking post on {subreddit}...[/bold]")

        if manual:
            # Manual entry
            if upvotes is None:
                upvotes = int(Prompt.ask("Upvotes"))
            if comments is None:
                comments = int(Prompt.ask("Comments"))

            upvote_ratio = float(Prompt.ask("Upvote ratio (0.0-1.0)", default="0.90"))
            awards = int(Prompt.ask("Awards", default="0"))

            metrics = tracker.track_post_manual(
                project_name=sanitize_filename(project),
                subreddit=subreddit,
                reddit_url=reddit_url,
                upvotes=upvotes,
                comments=comments,
                upvote_ratio=upvote_ratio,
                awards=awards
            )

            console.print("\n[green]✓ Metrics saved (manual entry)[/green]")

        else:
            # Automatic tracking via API
            metrics = tracker.track_post(
                reddit_url=reddit_url,
                project_name=sanitize_filename(project),
                subreddit=subreddit
            )

            if not metrics:
                console.print("\n[yellow]Automatic tracking failed. Try --manual flag[/yellow]")
                return

            console.print("\n[green]✓ Metrics tracked automatically[/green]")

        # Display metrics
        console.print(f"\n[bold cyan]Post Metrics:[/bold cyan]")
        console.print(f"  ⬆️  Upvotes: {metrics.upvotes}")
        console.print(f"  💬 Comments: {metrics.num_comments}")
        console.print(f"  📊 Upvote Ratio: {metrics.upvote_ratio:.1%}")
        console.print(f"  🏆 Awards: {metrics.awards}")
        console.print(f"  ⏱️  Hours since post: {metrics.hours_since_post:.1f}")

        console.print(f"\n[dim]Tracked at: {metrics.tracked_at}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


@cli.command()
@click.option('--project', help='Show analytics for specific project')
@click.option('--leaderboard', is_flag=True, help='Show top performing posts')
@click.option('--subreddits', is_flag=True, help='Show subreddit performance')
def analytics(project, leaderboard, subreddits):
    """View post performance analytics"""
    try:
        tracker = AnalyticsTracker()

        if project:
            # Project-specific analytics
            report = tracker.generate_report(sanitize_filename(project))
            console.print(report)

        elif leaderboard:
            # Show leaderboard
            console.print("\n[bold]🏆 Top Performing Posts[/bold]\n")

            top_posts = tracker.get_leaderboard(metric="upvotes", limit=10)

            if not top_posts:
                console.print("[yellow]No tracked posts yet[/yellow]")
                return

            table = Table(title="Leaderboard (by upvotes)")
            table.add_column("Rank", style="cyan", width=6)
            table.add_column("Project", style="green")
            table.add_column("Subreddit", style="blue")
            table.add_column("Upvotes", style="yellow", justify="right")
            table.add_column("Comments", style="magenta", justify="right")
            table.add_column("Ratio", style="white", justify="right")

            for i, post in enumerate(top_posts, 1):
                table.add_row(
                    f"#{i}",
                    post.get('project_name', 'Unknown')[:25],
                    post.get('subreddit', 'Unknown'),
                    str(post.get('upvotes', 0)),
                    str(post.get('num_comments', 0)),
                    f"{post.get('upvote_ratio', 0):.0%}"
                )

            console.print(table)

        elif subreddits:
            # Subreddit performance
            console.print("\n[bold]📍 Subreddit Performance Analysis[/bold]\n")

            subreddit_perf = tracker.get_subreddit_performance()

            if not subreddit_perf:
                console.print("[yellow]No tracked posts yet[/yellow]")
                return

            table = Table(title="Performance by Subreddit")
            table.add_column("Subreddit", style="cyan")
            table.add_column("Posts", style="white", justify="right")
            table.add_column("Avg Upvotes", style="yellow", justify="right")
            table.add_column("Avg Comments", style="magenta", justify="right")
            table.add_column("Avg Ratio", style="green", justify="right")

            # Sort by avg upvotes
            sorted_subs = sorted(
                subreddit_perf.items(),
                key=lambda x: x[1]['avg_upvotes'],
                reverse=True
            )

            for sub, stats in sorted_subs:
                table.add_row(
                    sub,
                    str(stats['posts']),
                    f"{stats['avg_upvotes']:.0f}",
                    f"{stats['avg_comments']:.0f}",
                    f"{stats['avg_upvote_ratio']:.0%}"
                )

            console.print(table)

        else:
            # Overall analytics
            report = tracker.generate_report()
            console.print(report)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


if __name__ == '__main__':
    cli()
