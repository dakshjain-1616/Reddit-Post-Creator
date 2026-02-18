"""
Sync CSV data to database — upserts all rows (insert new, update existing).
"""
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.database import get_session, close_session, Project
from src.config import CSV_FILE_PATH

def sync():
    csv_path = Path(CSV_FILE_PATH)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} rows in CSV")

    session = get_session()
    try:
        inserted = updated = 0
        for _, row in df.iterrows():
            github_repo = str(row.get('Github Repo', '')).strip()
            if not github_repo or github_repo == 'nan':
                continue

            content_title = str(row.get('Content Title', '')).strip()
            s3_link = str(row.get('s3 link/drive Link', '')).strip()
            youtube_link = str(row.get('Youtube Link', '')).strip()
            blog_created = str(row.get('Blog created on docs', '')).strip()
            readme_updated = str(row.get('README updated', '')).strip()

            existing = session.query(Project).filter_by(github_repo=github_repo).first()
            if existing:
                existing.content_title = content_title
                existing.s3_link = s3_link
                existing.youtube_link = youtube_link
                existing.blog_created = blog_created
                existing.readme_updated = readme_updated
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                session.add(Project(
                    content_title=content_title,
                    github_repo=github_repo,
                    s3_link=s3_link,
                    youtube_link=youtube_link,
                    blog_created=blog_created,
                    readme_updated=readme_updated,
                ))
                inserted += 1

        session.commit()
        print(f"Done — {inserted} inserted, {updated} updated")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        close_session(session)

if __name__ == '__main__':
    sync()
