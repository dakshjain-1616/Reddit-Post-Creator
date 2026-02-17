# 🚀 PostAgent Deployment Guide

Complete guide for deploying PostAgent to Vercel or any cloud platform.

## 📦 Vercel Deployment (Recommended)

### Method 1: Deploy from GitHub (Easiest)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/postagent.git
   git push -u origin main
   ```

2. **Deploy on Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will auto-detect the Flask app

3. **Configure Environment Variables**
   In Vercel dashboard, add:
   ```
   OPENAI_API_KEY=sk-...
   GITHUB_TOKEN=ghp_...
   SECRET_KEY=random-secret-here
   CSV_FILE_PATH=/tmp/projects.csv
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app is live! 🎉

### Method 2: Deploy with Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Add environment variables
vercel env add OPENAI_API_KEY
vercel env add GITHUB_TOKEN
vercel env add SECRET_KEY

# Deploy to production
vercel --prod
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t postagent .

# Run container
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your-key \
  -e GITHUB_TOKEN=your-token \
  -e SECRET_KEY=your-secret \
  postagent
```

## 🌐 Other Platforms

### Heroku

```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=your-key
heroku config:set GITHUB_TOKEN=your-token
heroku config:set SECRET_KEY=your-secret

# Deploy
git push heroku main
```

### Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Add environment variables
5. Deploy!

### Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add environment variables
6. Deploy!

## 🔐 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for GPT-4 |
| `GITHUB_TOKEN` | ✅ Yes | GitHub PAT for API access |
| `SECRET_KEY` | ✅ Yes | Flask secret key (random string) |
| `CSV_FILE_PATH` | ⚠️ Optional | Path to CSV file (default: `./Content Organiser - Sheet1.csv`) |
| `REDDIT_CLIENT_ID` | ❌ Optional | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | ❌ Optional | Reddit API secret |
| `REDDIT_USER_AGENT` | ❌ Optional | Reddit user agent |

## 📝 Post-Deployment Checklist

- [ ] All environment variables are set
- [ ] App loads without errors
- [ ] Can add projects
- [ ] Analysis works (test with a GitHub repo)
- [ ] Post generation works
- [ ] Posts are viewable
- [ ] No console errors in browser

## 🐛 Common Deployment Issues

### "Configuration errors"
**Solution:** Verify all required environment variables are set in your platform's dashboard.

### "Module not found"
**Solution:** Ensure `requirements.txt` is in the root directory and all dependencies are listed.

### "Internal Server Error"
**Solution:** Check application logs:
- Vercel: `vercel logs`
- Heroku: `heroku logs --tail`
- Railway/Render: Check logs in dashboard

### CSV File Issues
**Solution:** In production, the CSV file is created automatically if it doesn't exist. Make sure the path has write permissions.

## 📊 Monitoring & Logs

### Vercel
```bash
# View logs
vercel logs

# View specific deployment
vercel logs <deployment-url>
```

### Check Health
```bash
curl https://your-app.vercel.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "projects_count": 0,
  "generated_posts_count": 0
}
```

## 🔄 Updating Your Deployment

### Vercel (from GitHub)
Just push to main branch:
```bash
git add .
git commit -m "Update"
git push
```
Vercel auto-deploys on every push! ✨

### Manual Redeployment
```bash
vercel --prod
```

## 💡 Pro Tips

1. **Use Secrets**: Never commit API keys. Always use environment variables.

2. **Enable Analytics**: Vercel offers free analytics. Enable it in project settings.

3. **Custom Domain**: Add your custom domain in Vercel settings.

4. **Monitoring**: Set up uptime monitoring with services like:
   - Better Uptime
   - UptimeRobot
   - Pingdom

5. **Database**: For production at scale, consider moving from CSV to:
   - PostgreSQL (Supabase)
   - MongoDB (MongoDB Atlas)
   - SQLite (local)

## 🆘 Need Help?

- 📖 Check the main [README.md](./README.md)
- 🐛 Open an issue on GitHub
- 💬 Check Vercel documentation

---

**Happy Deploying! 🚀**
