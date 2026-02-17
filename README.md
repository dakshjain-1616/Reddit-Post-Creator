# PostAgent - AI-Powered Reddit Post Generator

Transform your GitHub projects into engaging Reddit posts automatically using AI.

## 🚀 Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/postagent)

### One-Click Deployment

1. Click the "Deploy with Vercel" button above
2. Connect your GitHub account
3. Add these environment variables:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `GITHUB_TOKEN` - Your GitHub personal access token
   - `SECRET_KEY` - Random secret key for Flask sessions
4. Click "Deploy"
5. Done! Your app is live 🎉

## 📋 Prerequisites

- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- GitHub Personal Access Token ([Create one here](https://github.com/settings/tokens))

## 🔧 Environment Variables

Create a `.env` file or set these in Vercel:

```env
# Required
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
SECRET_KEY=your-random-secret-key

# Optional
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=PostAgent/1.0
CSV_FILE_PATH=./Content Organiser - Sheet1.csv
```

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
# Edit .env with your API keys

# 5. Run the app
python app.py
```

Visit http://localhost:5000

## 📁 Project Structure

```
postagent/
├── app.py                 # Main Flask application
├── src/                   # Core functionality
│   ├── config.py         # Configuration management
│   ├── github_analyzer.py # GitHub API integration
│   ├── subreddit_matcher.py # Subreddit matching logic
│   └── content_generator.py # Post generation
├── templates/            # HTML templates
├── static/              # Static assets
├── data/                # Data storage
│   └── subreddit_db.json # Subreddit database
├── vercel.json          # Vercel configuration
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
