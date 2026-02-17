# 🚀 Quick Deploy to Vercel

**5-minute deployment guide for PostAgent**

## Prerequisites

✅ GitHub account
✅ Vercel account (free)
✅ OpenAI API key
✅ GitHub Personal Access Token

## Step-by-Step Deployment

### 1️⃣ Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Production ready"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/postagent.git
git branch -M main
git push -u origin main
```

### 2️⃣ Deploy on Vercel

1. **Go to [vercel.com/new](https://vercel.com/new)**

2. **Import Repository**
   - Click "Import Git Repository"
   - Select your PostAgent repo
   - Click "Import"

3. **Configure Project**
   - Framework Preset: **Other**
   - Root Directory: `./` (default)
   - Build Command: Leave empty
   - Output Directory: Leave empty
   - Install Command: `pip install -r requirements.txt`

4. **Add Environment Variables**

   Click "Environment Variables" and add:

   ```
   OPENAI_API_KEY
   sk-your-openai-api-key-here
   ```

   ```
   GITHUB_TOKEN
   ghp_your-github-token-here
   ```

   ```
   SECRET_KEY
   your-random-secret-key-123456
   ```

   Optional:
   ```
   CSV_FILE_PATH
   /tmp/projects.csv
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes ⏳
   - Done! 🎉

### 3️⃣ Verify Deployment

Visit your deployment URL and check:

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

✅ **You're live!**

## Getting Your API Keys

### OpenAI API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)
4. Add billing info if needed

### GitHub Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Name: `PostAgent`
4. Scopes: Check `repo` (all repo permissions)
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)

### Secret Key

Generate a random string:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Or use any random string (min 32 characters)

## Updating Your App

Just push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push
```

Vercel automatically deploys! ✨

## Custom Domain (Optional)

1. Go to your Vercel project dashboard
2. Click "Settings" → "Domains"
3. Add your domain
4. Update DNS records as shown
5. Done!

## Need Help?

- 📖 Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- 📋 See [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)
- 🐛 Open an issue on GitHub

---

**Total Time: ~5 minutes** ⚡
