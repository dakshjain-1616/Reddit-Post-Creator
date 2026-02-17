# Vercel Deployment Guide

This guide will help you deploy PostAgent to Vercel with Postgres database support.

## 🆓 Looking for FREE deployment?

**→ See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for 100% free deployment with Supabase!**

This guide covers Vercel Postgres (has free tier but may require verification).

## Prerequisites

- A Vercel account
- Your GitHub repository connected to Vercel
- A Postgres database (Vercel Postgres, Supabase, or any Postgres provider)

## Step 1: Set up Vercel Postgres

1. Go to your Vercel project dashboard
2. Click on the **Storage** tab
3. Click **Create Database**
4. Select **Postgres** (powered by Neon)
5. Choose a database name (e.g., `postagent-db`)
6. Select a region (same as your deployment region for best performance)
7. Click **Create**

**Important:** Vercel will automatically add the `POSTGRES_URL` environment variable to your project.

## Step 2: Configure Environment Variables

Go to **Settings** → **Environment Variables** and add:

### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key for content generation |
| `POSTGRES_URL` | (auto-set) | Database connection string (automatically set by Vercel) |

### Optional Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `GITHUB_TOKEN` | `github_pat_...` | GitHub personal access token (for private repos) |
| `REDDIT_CLIENT_ID` | Your Reddit app ID | For Reddit API features |
| `REDDIT_CLIENT_SECRET` | Your Reddit secret | For Reddit API features |
| `SECRET_KEY` | Random string | Flask session secret (auto-generated if not set) |

## Step 3: Initialize the Database

After deploying, you need to initialize the database schema. You have two options:

### Option A: Using Vercel CLI (Recommended)

```bash
# Install Vercel CLI if you haven't
npm i -g vercel

# Pull environment variables
vercel env pull

# Initialize database
python init_db.py
```

### Option B: Using Vercel Postgres Dashboard

1. Go to your database in the Vercel dashboard
2. Click on the **Query** tab
3. Run this SQL:

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    content_title VARCHAR(500) NOT NULL,
    github_repo VARCHAR(500) NOT NULL UNIQUE,
    s3_link VARCHAR(500) DEFAULT '',
    youtube_link VARCHAR(500) DEFAULT '',
    blog_created VARCHAR(500) DEFAULT '',
    readme_updated VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE generated_posts (
    id SERIAL PRIMARY KEY,
    project_slug VARCHAR(500) NOT NULL,
    project_title VARCHAR(500) NOT NULL,
    github_url VARCHAR(500) NOT NULL,
    subreddit VARCHAR(200) NOT NULL,
    title VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    flair VARCHAR(200),
    estimated_engagement VARCHAR(200),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_slug ON generated_posts(project_slug);
```

## Step 4: Deploy

### Auto-deployment (GitHub)

If your repository is connected to Vercel:
1. Push your code to GitHub
2. Vercel will automatically deploy

### Manual deployment

```bash
vercel --prod
```

## Step 5: Migrate Existing Data (Optional)

If you have existing projects in the CSV file, you can migrate them:

```bash
# Pull environment variables
vercel env pull

# Run migration
python init_db.py
```

The script will:
- ✅ Check database connection
- ✅ Create tables if needed
- ✅ Offer to migrate CSV data

## Troubleshooting

### "Database URL not configured"

Make sure you've created a Vercel Postgres database and it's linked to your project. Check **Storage** tab in Vercel dashboard.

### "Function invocation failed"

1. Check the **Functions** logs in Vercel dashboard
2. Verify all environment variables are set correctly
3. Make sure the database is initialized with tables

### "Table doesn't exist"

Run the database initialization (Step 3) to create the required tables.

### Connection errors

- Ensure your database is in the same region as your deployment
- Check that `POSTGRES_URL` is set in environment variables
- Verify the database is active (not paused)

## Features After Migration

✅ **Working features:**
- View all projects
- Add new projects
- Analyze GitHub repositories
- Generate Reddit posts
- View generated posts
- Delete projects
- Health check endpoint

✅ **Database benefits:**
- No filesystem limitations
- Persistent storage
- Fast queries
- Automatic backups (via Vercel)
- Scalable for growth

## Need Help?

- [Vercel Postgres Documentation](https://vercel.com/docs/storage/vercel-postgres)
- [Vercel Deployment Docs](https://vercel.com/docs)
- Check the GitHub repository issues

---

**Ready to deploy?** Follow the steps above and you'll have a fully functional PostAgent on Vercel! 🚀
