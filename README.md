# PostAgent - AI-Powered Reddit Post Generator

Transform your GitHub projects into engaging Reddit posts automatically using AI.

## 🚀 Quick Deploy (FREE!)

### 🆓 Deploy with Free Supabase Database (Recommended)

**See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for complete FREE deployment guide!**

Takes 10 minutes:
1. Create free Supabase database
2. Add environment variables to Vercel
3. Deploy automatically from GitHub
4. Done! 🎉

### 💳 Alternative: Vercel Postgres

See [DEPLOYMENT.md](DEPLOYMENT.md) for Vercel Postgres setup (may require verification)

## 📋 Prerequisites

- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- GitHub Personal Access Token ([Create one here](https://github.com/settings/tokens))

## 🔧 Environment Variables

Create a `.env` file or set these in Vercel:

```env
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@host:5432/database

# Optional
GITHUB_TOKEN=ghp_...
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=PostAgent/1.0
```

**Where to get DATABASE_URL:**
- Supabase: See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) (FREE)
- Vercel Postgres: Auto-set as `POSTGRES_URL`
- Local: `postgresql://postgres:password@localhost:5432/postagent`

## 🎯 Features

- **Smart Analysis**: AI analyzes your GitHub projects automatically
- **Subreddit Matching**: Finds the best Reddit communities for your project
- **Custom Posts**: Generates tailored content for each subreddit
- **User-Friendly**: Simple interface for non-technical users
- **Production Ready**: Optimized for Vercel deployment

## 🏗️ Local Development

```bash
# 1. Clone the repository
git clone <your-repo>
cd postagent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your API keys and database URL

# 5. Set up database (if needed)
python init_db.py

# 6. Test database connection
python test_db.py

# 7. Run the app
python app.py
```

Visit http://localhost:5000

## 📁 Project Structure

```
postagent/
├── app.py                 # Main Flask application
├── api/
│   └── index.py          # Vercel serverless entry point
├── src/                   # Core functionality
│   ├── config.py         # Configuration management
│   ├── database.py       # Database models and operations
│   ├── github_analyzer.py # GitHub API integration
│   ├── subreddit_matcher.py # Subreddit matching logic
│   └── content_generator.py # Post generation
├── templates/            # HTML templates
├── static/              # Static assets
├── data/                # Data storage
│   └── subreddit_db.json # Subreddit database
├── init_db.py           # Database initialization script
├── test_db.py           # Database connection test
├── vercel.json          # Vercel configuration
├── SUPABASE_SETUP.md    # Free deployment guide
├── DEPLOYMENT.md        # Vercel Postgres guide
└── requirements.txt     # Python dependencies
```

## 🔐 Security Notes

- Never commit `.env` file
- Use environment variables in production
- Rotate API keys regularly
- Keep dependencies updated

## 🐛 Troubleshooting

### Common Issues

**"Configuration errors"**
- Check that all required environment variables are set
- Verify API keys are valid

**"GitHub API 502 Error"**
- The app has automatic retry logic
- Usually resolves after 1-2 attempts

**"Module not found"**
- Make sure you've run `pip install -r requirements.txt`
- Activate your virtual environment

## 📝 License

MIT License - feel free to use for your projects!

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📧 Support

For issues or questions, please open a GitHub issue.
