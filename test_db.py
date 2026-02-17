"""
Quick database connection test
Run this to verify your database is set up correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("Database Connection Test")
    print("="*60 + "\n")

    # Check for database URL
    db_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

    if not db_url:
        print("❌ POSTGRES_URL not set!")
        print("\n   For local testing:")
        print("   1. Create .env file (or use existing)")
        print("   2. Add: POSTGRES_URL=your_database_url")
        print("\n   For Vercel:")
        print("   1. Create Vercel Postgres database")
        print("   2. It auto-adds POSTGRES_URL")
        return False

    print("✅ Database URL found")
    print(f"   URL: {db_url[:30]}...{db_url[-20:]}\n")

    # Try to connect
    try:
        from sqlalchemy import create_engine, text

        print("🔌 Attempting connection...")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"   PostgreSQL: {version.split(',')[0]}\n")

            # Check if tables exist
            print("📋 Checking tables...")
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('projects', 'generated_posts')
            """))
            tables = [row[0] for row in result]

            if 'projects' in tables:
                print("   ✅ projects table exists")
            else:
                print("   ❌ projects table NOT found")

            if 'generated_posts' in tables:
                print("   ✅ generated_posts table exists")
            else:
                print("   ❌ generated_posts table NOT found")

            if len(tables) == 0:
                print("\n   ⚠️  No tables found! Run init_db.py or SQL script")
            elif len(tables) < 2:
                print("\n   ⚠️  Missing tables! Run init_db.py or SQL script")
            else:
                print("\n   🎉 Database is fully set up!")

                # Count records
                result = conn.execute(text("SELECT COUNT(*) FROM projects"))
                project_count = result.fetchone()[0]
                print(f"   📊 Projects: {project_count}")

                result = conn.execute(text("SELECT COUNT(*) FROM generated_posts"))
                posts_count = result.fetchone()[0]
                print(f"   📊 Generated posts: {posts_count}")

        print("\n" + "="*60)
        print("✅ Database test PASSED")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"   Error: {str(e)}\n")
        print("   Troubleshooting:")
        print("   1. Verify POSTGRES_URL is correct")
        print("   2. Check database is running")
        print("   3. Verify network access\n")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
