"""
Database Initialization Script
Run this to set up the database and optionally migrate CSV data
"""

import os
import sys
import pandas as pd
from pathlib import Path
from src.database import init_db, get_session, close_session, Project
from src.config import CSV_FILE_PATH

def migrate_csv_to_db():
    """Migrate existing CSV data to database"""
    print("🔄 Migrating CSV data to database...")

    # Check if CSV exists
    if not Path(CSV_FILE_PATH).exists():
        print(f"⚠️  CSV file not found at {CSV_FILE_PATH}")
        print("   Skipping migration...")
        return

    # Load CSV
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        print(f"✅ Found {len(df)} projects in CSV")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # Get database session
    session = get_session()

    try:
        # Check if data already exists
        existing_count = session.query(Project).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} projects")
            response = input("   Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("   Skipping migration...")
                return
            # Clear existing data
            session.query(Project).delete()
            session.commit()

        # Migrate each row
        migrated = 0
        for _, row in df.iterrows():
            project = Project(
                content_title=str(row.get('Content Title', '')),
                github_repo=str(row.get('Github Repo', '')),
                s3_link=str(row.get('s3 link/drive Link', '')),
                youtube_link=str(row.get('Youtube Link', '')),
                blog_created=str(row.get('Blog created on docs', '')),
                readme_updated=str(row.get('README updated', ''))
            )
            session.add(project)
            migrated += 1

        session.commit()
        print(f"✅ Successfully migrated {migrated} projects to database")

    except Exception as e:
        session.rollback()
        print(f"❌ Error migrating data: {e}")
    finally:
        close_session(session)


def main():
    print("\n" + "="*60)
    print("PostAgent Database Setup")
    print("="*60 + "\n")

    # Check for database URL
    db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    if not db_url:
        print("❌ Database URL not configured!")
        print("\n   1. Go to https://console.neon.tech and create a free project")
        print("   2. Copy the connection string from the dashboard")
        print("   3. Add to .env: DATABASE_URL=postgresql://...")
        sys.exit(1)

    print(f"✅ Database URL configured")

    # Initialize database (create tables)
    try:
        print("\n🔧 Initializing database schema...")
        init_db()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

    # Ask about CSV migration
    print("\n" + "-"*60)
    response = input("Migrate existing CSV data to database? (Y/n): ").strip().lower()
    if response in ['', 'y', 'yes']:
        migrate_csv_to_db()

    print("\n" + "="*60)
    print("✅ Database setup complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
