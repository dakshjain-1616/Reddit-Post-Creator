"""
Database module for PostAgent
Handles all database operations using Vercel Postgres
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional

Base = declarative_base()


class Project(Base):
    """Project model - replaces CSV storage"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_title = Column(String(500), nullable=False)
    github_repo = Column(String(500), nullable=False, unique=True)
    s3_link = Column(String(500), default='')
    youtube_link = Column(String(500), default='')
    blog_created = Column(String(500), default='')
    readme_updated = Column(String(500), default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedPost(Base):
    """Generated posts model - replaces filesystem storage"""
    __tablename__ = 'generated_posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_slug = Column(String(500), nullable=False, index=True)
    project_title = Column(String(500), nullable=False)
    github_url = Column(String(500), nullable=False)
    subreddit = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    flair = Column(String(200))
    estimated_engagement = Column(String(200))
    post_metadata = Column(JSON)  # Store analysis and subreddit info (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database connection
def get_database_url():
    """Get database URL from environment (supports Supabase, Vercel Postgres, or any Postgres)"""
    # Try multiple environment variable names
    # Supabase uses DATABASE_URL, Vercel uses POSTGRES_URL
    return (
        os.getenv('DATABASE_URL') or
        os.getenv('POSTGRES_URL') or
        os.getenv('SUPABASE_DB_URL')
    )


def init_db():
    """Initialize database connection and create tables"""
    db_url = get_database_url()

    if not db_url:
        raise ValueError("Database URL not configured. Set POSTGRES_URL or DATABASE_URL environment variable.")

    # Create engine
    engine = create_engine(db_url)

    # Create tables
    Base.metadata.create_all(engine)

    # Create session factory
    Session = sessionmaker(bind=engine)

    return engine, Session


# Session management
_engine = None
_SessionLocal = None


def get_session():
    """Get a database session"""
    global _engine, _SessionLocal

    if _SessionLocal is None:
        _engine, _SessionLocal = init_db()

    return _SessionLocal()


def close_session(session):
    """Close a database session"""
    if session:
        session.close()


# CRUD Operations for Projects
def get_all_projects() -> List[Dict]:
    """Get all projects (replaces load_projects from CSV)"""
    session = get_session()
    try:
        projects = session.query(Project).order_by(Project.created_at).all()
        return [
            {
                'index': idx + 1,
                'Content Title': p.content_title,
                'Github Repo': p.github_repo,
                's3 link/drive Link': p.s3_link,
                'Youtube Link': p.youtube_link,
                'Blog created on docs': p.blog_created,
                'README updated': p.readme_updated
            }
            for idx, p in enumerate(projects)
        ]
    finally:
        close_session(session)


def get_project_by_id(row_id: int) -> Optional[Dict]:
    """Get project by row ID"""
    session = get_session()
    try:
        project = session.query(Project).offset(row_id - 1).first()
        if project:
            return {
                'Content Title': project.content_title,
                'Github Repo': project.github_repo,
                's3 link/drive Link': project.s3_link,
                'Youtube Link': project.youtube_link,
                'Blog created on docs': project.blog_created,
                'README updated': project.readme_updated
            }
        return None
    finally:
        close_session(session)


def add_project(title: str, github_url: str) -> bool:
    """Add a new project"""
    session = get_session()
    try:
        # Check if URL already exists
        existing = session.query(Project).filter_by(github_repo=github_url).first()
        if existing:
            return False

        # Create new project
        project = Project(
            content_title=title,
            github_repo=github_url
        )
        session.add(project)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_session(session)


def delete_project(row_id: int) -> Optional[str]:
    """Delete a project by row ID, returns project title if successful"""
    session = get_session()
    try:
        # Get all projects to find the one at row_id
        projects = session.query(Project).order_by(Project.created_at).all()
        if row_id < 1 or row_id > len(projects):
            return None

        project = projects[row_id - 1]
        title = project.content_title

        session.delete(project)
        session.commit()
        return title
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_session(session)


def project_exists(github_url: str) -> bool:
    """Check if a project with the given GitHub URL already exists"""
    session = get_session()
    try:
        project = session.query(Project).filter_by(github_repo=github_url).first()
        return project is not None
    finally:
        close_session(session)


# CRUD Operations for Generated Posts
def save_generated_posts(project_slug: str, project_title: str, github_url: str,
                        posts: List[Dict], metadata: Dict) -> int:
    """Save generated posts to database"""
    session = get_session()
    try:
        saved_count = 0
        for post_data in posts:
            post = GeneratedPost(
                project_slug=project_slug,
                project_title=project_title,
                github_url=github_url,
                subreddit=post_data.get('subreddit', ''),
                title=post_data.get('title', ''),
                body=post_data.get('body', ''),
                flair=post_data.get('flair', ''),
                estimated_engagement=post_data.get('estimated_engagement', ''),
                metadata=metadata
            )
            session.add(post)
            saved_count += 1

        session.commit()
        return saved_count
    except Exception as e:
        session.rollback()
        raise e
    finally:
        close_session(session)


def get_all_generated_posts() -> List[Dict]:
    """Get all generated posts grouped by project"""
    session = get_session()
    try:
        # Get distinct project slugs with their latest post
        from sqlalchemy import func

        subquery = session.query(
            GeneratedPost.project_slug,
            func.max(GeneratedPost.created_at).label('latest')
        ).group_by(GeneratedPost.project_slug).subquery()

        posts = session.query(GeneratedPost).join(
            subquery,
            (GeneratedPost.project_slug == subquery.c.project_slug) &
            (GeneratedPost.created_at == subquery.c.latest)
        ).all()

        result = []
        for post in posts:
            # Count total posts for this project
            post_count = session.query(GeneratedPost).filter_by(
                project_slug=post.project_slug
            ).count()

            result.append({
                'project_name': post.project_slug,
                'project_title': post.project_title,
                'github_url': post.github_url,
                'generated_at': post.created_at.isoformat(),
                'post_count': post_count,
                'subreddit_matches': post.post_metadata.get('subreddit_matches', []) if post.post_metadata else []
            })

        # Sort by generation time (newest first)
        result.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        return result
    finally:
        close_session(session)


def get_project_posts(project_slug: str) -> Dict:
    """Get all posts for a specific project"""
    session = get_session()
    try:
        posts = session.query(GeneratedPost).filter_by(
            project_slug=project_slug
        ).order_by(GeneratedPost.created_at).all()

        if not posts:
            return None

        # Get metadata from first post
        metadata = posts[0].post_metadata or {}

        post_list = []
        for post in posts:
            post_list.append({
                'filename': f"{project_slug}-{post.subreddit.lower().replace('r/', '').replace('/', '-')}.md",
                'subreddit': post.subreddit,
                'title': post.title,
                'body': post.body,
                'flair': post.flair,
                'estimated_engagement': post.estimated_engagement
            })

        return {
            'project_title': posts[0].project_title,
            'github_url': posts[0].github_url,
            'generated_at': posts[0].created_at.isoformat(),
            'metadata': metadata,
            'posts': post_list
        }
    finally:
        close_session(session)


def get_projects_count() -> int:
    """Get total number of projects"""
    session = get_session()
    try:
        return session.query(Project).count()
    finally:
        close_session(session)


def get_generated_posts_count() -> int:
    """Get total number of unique projects with generated posts"""
    session = get_session()
    try:
        from sqlalchemy import func
        return session.query(func.count(func.distinct(GeneratedPost.project_slug))).scalar()
    finally:
        close_session(session)
