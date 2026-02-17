# PostAgent: Automated Reddit Post Generator for NEO Projects

PostAgent is an intelligent automation tool that generates engaging, customized Reddit posts for AI/ML projects built with NEO. It analyzes GitHub repositories, matches them to relevant subreddits, and creates viral-pattern-optimized content.

## Features

- **🔍 GitHub Repository Analysis**: Automatically extracts key value propositions, technical details, and use cases using GPT-4
- **🎯 Smart Subreddit Matching**: Identifies 3-5 most relevant Reddit communities based on project characteristics
- **📝 AI-Powered Content Generation**: Creates customized posts following viral patterns for each subreddit
- **🎨 Community-Aware Formatting**: Adapts tone, technical depth, and style to match subreddit culture
- **📊 Batch Processing**: Process multiple repos from CSV file
- **✅ Publishing Workflow**: Review, edit, and track publication status
- **🔄 Team Collaboration**: Track who published which posts and when

## Architecture

```
PostAgent/
├── app.py                       # Flask web application
├── start_web.sh                 # Web interface startup script
├── templates/                   # HTML templates
│   ├── base.html               # Base template with navigation
│   ├── index.html              # Projects list page
│   ├── add_project.html        # Add project form
│   ├── posts.html              # Generated posts overview
│   └── project_posts.html      # Detailed post view
├── src/
│   ├── github_analyzer.py      # Repository analysis with GPT-4
│   ├── reddit_scraper.py        # Viral post pattern extraction
│   ├── subreddit_matcher.py     # Project-to-community matching
│   ├── content_generator.py     # AI post generation
│   ├── cli.py                   # Command-line interface
│   ├── config.py                # Configuration management
│   └── utils.py                 # Utility functions
├── data/
│   ├── viral_examples/          # Scraped viral posts
│   ├── generated_posts/         # Generated content
│   └── subreddit_db.json        # Community database
├── Content Organiser - Sheet1.csv
├── requirements.txt
└── .env
```

## Installation

### 1. Clone and Setup

```bash
cd /root/PostAgent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-your-openai-key-here
GITHUB_TOKEN=ghp_optional-for-higher-rate-limits
REDDIT_CLIENT_ID=optional-for-scraping
REDDIT_CLIENT_SECRET=optional-for-scraping
REDDIT_USER_AGENT=PostAgent/1.0
CSV_FILE_PATH=/root/PostAgent/Content Organiser - Sheet1.csv
```

**Required:**
- `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/)

**Optional:**
- `GITHUB_TOKEN`: [Create personal access token](https://github.com/settings/tokens) for higher API limits
- `REDDIT_CLIENT_ID/SECRET`: [Create app](https://www.reddit.com/prefs/apps) for viral post scraping

## Usage

PostAgent offers two interfaces:
1. **Web Interface** (Recommended for beginners): Easy-to-use browser interface
2. **Command Line Interface**: Powerful batch processing and automation

### Web Interface (Recommended)

The web interface provides an intuitive way to manage projects and generate posts.

#### Quick Start

```bash
# Start the web server
./start_web.sh

# Or directly with Python
python app.py
```

Then open http://localhost:5000 in your browser.

**Features:**
- Add GitHub repositories with a simple form
- One-click repository analysis
- Generate posts for multiple subreddits instantly
- View and copy all generated posts
- Clean, modern interface with real-time feedback

See [WEB_INTERFACE.md](WEB_INTERFACE.md) for detailed documentation.

### Command Line Interface

#### Basic Workflow

#### 1. List Available Projects

```bash
python -m src.cli list-projects
```

#### 2. Generate Posts for a Specific Project

```bash
# Generate for row 1 in CSV
python -m src.cli generate --row 1
```

This will:
- Analyze the GitHub repository
- Find 5 relevant subreddits
- Generate customized posts for each
- Save to `data/generated_posts/[project-name]/`

#### 3. Generate for Multiple Projects

```bash
# Process first 5 projects
python -m src.cli generate --all --limit 5
```

#### 4. Review Generated Posts

```bash
python -m src.cli review
```

Interactive review allows you to:
- Preview posts
- Edit content
- Mark as published
- Track publishing status

#### 5. Mark Post as Published

```bash
python -m src.cli publish project-name/r-machinelearning.md --publisher "John"
```

#### 6. Check Status

```bash
python -m src.cli status
```

### Advanced Usage

#### Analyze Single Repository

```bash
python -m src.cli analyze https://github.com/dakshjain-1616/Multi-Model-Invoice-OCR-Pipeline-By-NEO
```

#### Scrape Viral Examples (Optional)

If you have Reddit API credentials:

```bash
python -m src.reddit_scraper --subreddits MachineLearning,LocalLLaMA,artificial --limit 30
```

This scrapes top posts to inform content generation patterns.

## Output Format

Generated posts are saved as markdown files:

```
data/generated_posts/
├── multi-model-invoice-ocr/
│   ├── metadata.json                 # Project metadata
│   ├── r-machinelearning.md          # Post for r/MachineLearning
│   ├── r-computervision.md           # Post for r/computervision
│   └── r-datascience.md              # Post for r/datascience
└── table-extraction/
    └── ...
```

Each post includes:
- Title optimized for engagement
- Formatted body with value propositions
- Appropriate flair suggestion
- Engagement estimate
- Generation metadata

## Subreddit Database

PostAgent includes a curated database of 12 AI/ML subreddits:

- **r/MachineLearning** - Academic/research focus
- **r/artificial** - General AI discussions
- **r/LocalLLaMA** - Local LLM deployment
- **r/OpenAI** - OpenAI products
- **r/learnmachinelearning** - Educational content
- **r/datascience** - Data science practice
- **r/deeplearning** - Deep learning techniques
- **r/computervision** - CV and image processing
- **r/MLOps** - ML operations
- **r/LangChain** - LangChain framework
- **r/ChatGPT** - ChatGPT use cases
- **r/ArtificialIntelligence** - Broad AI community

Each entry includes posting rules, tone guidelines, and audience levels.

## How It Works

### 1. GitHub Analysis

The analyzer:
- Fetches repository metadata (stars, forks, languages)
- Reads README content
- Uses GPT-4 to extract:
  - Top 3 value propositions
  - Technical synopsis
  - Key features and use cases
  - How to build further with NEO
  - Innovation level

### 2. Subreddit Matching

The matcher:
- Scores each subreddit based on project characteristics
- Considers: keywords, topics, technical level, audience
- Returns ranked list of most relevant communities

### 3. Content Generation

The generator:
- Loads viral post examples (if available)
- Analyzes successful patterns
- Creates customized posts using GPT-4
- Adapts tone and technical depth per subreddit
- Follows community guidelines

### 4. Quality Assurance

- Posts are saved for review before publishing
- Team members can edit and approve
- Publishing tracking prevents duplicates
- Metadata preserves generation context

## Best Practices

### Content Quality

1. **Always Review**: AI-generated content should be reviewed and edited
2. **Add Context**: Include personal touches and project-specific details
3. **Be Authentic**: Avoid overly promotional language
4. **Follow Rules**: Check each subreddit's specific posting guidelines
5. **Engage**: Respond to comments and questions after posting

### Timing

- Post during peak hours for each subreddit
- Avoid posting same project to similar subreddits on same day
- Space out posts across different communities

### Community Guidelines

- Read subreddit rules before posting
- Use appropriate flairs
- Provide value, don't just promote
- Be transparent about your involvement
- Welcome feedback and criticism

## Troubleshooting

### "OPENAI_API_KEY is required"

Add your OpenAI API key to `.env` file.

### "CSV file not found"

Check that `Content Organiser - Sheet1.csv` exists in the project root, or update `CSV_FILE_PATH` in `.env`.

### Rate Limits

- GitHub API: 60 requests/hour without token, 5000 with token
- OpenAI API: Check your account limits
- Reddit API: ~60 requests/minute with authentication

Built-in rate limiting (1 second delay) helps prevent issues.

### Generated Posts Quality

If posts seem generic:
1. Scrape viral examples: `python -m src.reddit_scraper --subreddits [list]`
2. Ensure README is comprehensive
3. Increase `OPENAI_TEMPERATURE` for more creativity
4. Review and manually enhance generated content

## Development

### Running Tests

```bash
# Test single repo analysis
python -m src.cli analyze [github-url]

# Test subreddit matching
python -c "
from src.github_analyzer import GitHubAnalyzer
from src.subreddit_matcher import SubredditMatcher

analyzer = GitHubAnalyzer()
matcher = SubredditMatcher()

analysis = analyzer.analyze_repository('[repo-url]')
matches = matcher.match_subreddits(analysis)

for name, score, info in matches:
    print(f'{name}: {score}')
"
```

### Extending

**Add New Subreddits:**

Edit `data/subreddit_db.json`:

```json
{
  "r/YourSubreddit": {
    "name": "r/YourSubreddit",
    "description": "Community description",
    "posting_rules": ["Rule 1", "Rule 2"],
    "preferred_flairs": ["Flair1", "Flair2"],
    "tone": "professional, helpful",
    "audience_level": "intermediate",
    "topics": ["topic1", "topic2"],
    "keywords": ["keyword1", "keyword2"]
  }
}
```

**Customize Prompts:**

Edit prompt templates in `src/content_generator.py` to adjust output style.

## CSV Format

Expected CSV columns:

| Content Title | Github Repo | s3 link/drive Link | Youtube Link | Blog created on docs | README updated |
|--------------|-------------|--------------------|--------------|--------------------|----------------|
| Project Name | https://... | https://...        | https://...  | TRUE               | TRUE           |

Only `Content Title` and `Github Repo` are required for PostAgent.

## Limitations

- Requires OpenAI API access (costs apply)
- GitHub public repositories only
- Manual publishing to Reddit (no auto-post)
- English content only (currently)

## Future Enhancements

- [ ] Direct Reddit posting integration
- [ ] A/B testing for titles
- [ ] Post-publication engagement tracking
- [ ] Multi-language support
- [ ] Image/screenshot generation
- [ ] Scheduled posting
- [ ] Analytics dashboard

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: This README
- NEO Platform: [heyneo.com](https://heyneo.com)

---

Built with ❤️ for the NEO community
