# 🆓 Free Deployment with Supabase

Deploy PostAgent for **FREE** using Supabase database (no credit card needed!)

## Why Supabase?

- ✅ **FREE tier**: 500MB database, 2GB bandwidth
- ✅ **No credit card required**
- ✅ **Postgres database** (works perfectly with our code)
- ✅ **Easy 5-minute setup**

---

## Step 1: Create Supabase Database (2 minutes)

1. Go to https://supabase.com
2. Click **Start your project** → Sign in with GitHub
3. Click **New Project**
4. Fill in:
   - **Name**: `postagent-db`
   - **Database Password**: (create a strong password - SAVE THIS!)
   - **Region**: Choose closest to you
   - **Plan**: Free (selected by default)
5. Click **Create new project**
6. Wait ~2 minutes for database to provision

## Step 2: Get Database URL (1 minute)

1. In your Supabase project, click **Settings** (gear icon in sidebar)
2. Click **Database** in the left menu
3. Scroll to **Connection string** section
4. Copy the **URI** (the one that starts with `postgresql://`)
5. Replace `[YOUR-PASSWORD]` in the URL with your actual database password

Example format:
```
postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

## Step 3: Initialize Database Tables (2 minutes)

1. In Supabase, click **SQL Editor** in the sidebar
2. Click **New query**
3. Paste this SQL and click **Run**:

```sql
-- Create projects table
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

-- Create generated_posts table
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

-- Create index for faster queries
CREATE INDEX idx_project_slug ON generated_posts(project_slug);
```

✅ You should see "Success. No rows returned"

## Step 4: Configure Vercel Environment Variables

1. Go to your Vercel project dashboard
2. Click **Settings** → **Environment Variables**
3. Add these variables:

| Variable | Value | Where to get it |
|----------|-------|-----------------|
| `DATABASE_URL` | `postgresql://postgres...` | From Step 2 (Supabase connection string) |
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key |
| `GITHUB_TOKEN` | `github_pat_...` | Optional: Your GitHub token |

**Important:** Make sure to use `DATABASE_URL` (not `POSTGRES_URL`)

## Step 5: Deploy to Vercel

### If connected to GitHub (auto-deploy):
1. Code is already pushed ✅
2. Vercel will auto-deploy in ~2 minutes
3. Check **Deployments** tab for status

### Manual deploy:
```bash
vercel --prod
```

## Step 6: Test It! 🎉

Visit your app:
```
https://your-app.vercel.app/health
```

Should show:
```json
{
  "status": "healthy",
  "projects_count": 0,
  "generated_posts_count": 0
}
```

✅ If you see this → **SUCCESS!** Your app is working!

---

## 🔧 Troubleshooting

### "DATABASE_URL is required"
- Make sure you added `DATABASE_URL` in Vercel environment variables
- Redeploy after adding env vars

### "Connection refused" or "Connection timeout"
- Check your Supabase password is correct in the DATABASE_URL
- Verify the connection string format is correct
- Make sure you copied the full URL with password

### "Table doesn't exist"
- Go back to Step 3 and run the SQL in Supabase SQL Editor

### "Function invocation failed"
- Check Vercel function logs for detailed error
- Verify all environment variables are set
- Make sure tables are created in Supabase

---

## 📦 Local Development (Optional)

Want to test locally?

1. Create `.env` file:
```bash
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@...
OPENAI_API_KEY=sk-proj-...
GITHUB_TOKEN=github_pat_...
```

2. Test database:
```bash
python test_db.py
```

3. Run app:
```bash
python app.py
```

---

## 💰 Free Tier Limits

Supabase free tier includes:
- ✅ 500MB database storage
- ✅ 2GB bandwidth per month
- ✅ 50MB file storage
- ✅ 2 GB file uploads

**This is more than enough to get started!** You can always upgrade later if needed.

---

## 🎯 Next Steps

After deployment:
1. ✅ Add your first project via the web interface
2. ✅ Analyze a GitHub repository
3. ✅ Generate Reddit posts
4. ✅ Share your deployed app!

**Need help?** Check the logs in Vercel dashboard or Supabase logs.

---

## 🔐 Security Tips

- ✅ Never commit your `DATABASE_URL` to GitHub
- ✅ Use environment variables in Vercel
- ✅ Keep your Supabase password secure
- ✅ Enable RLS (Row Level Security) in Supabase for production

---

**Ready to deploy?** Follow the steps above - takes less than 10 minutes! 🚀
