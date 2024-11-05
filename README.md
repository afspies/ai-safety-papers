# AI-Safety Reading List

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Anthropic Claude](https://img.shields.io/badge/AI-Claude%203.5-green)](https://www.anthropic.com/)
[![Hugo](https://img.shields.io/badge/Hugo-%5E0.123.0-ff4088)](https://gohugo.io/)
[![Netlify Status](https://api.netlify.com/api/v1/badges/c4ffd274-3e6c-4243-b022-94c47e8a5442/deploy-status)](https://app.netlify.com/sites/aisafetypapers/deploys)

> 🌐 **Live Site**: Check out the running instance at [pages.unsearch.org](https://pages.unsearch.org)

An automated system that creates and maintains a curated list of AI safety research papers, including summaries and multi-channel distribution. The system automatically fetches papers from Semantic Scholar, generates summaries using Claude, and distributes content through a static website, with planned support for Telegram and Twitter distribution.

## Features

- 🤖 Automated paper discovery using Semantic Scholar API
- 📝 AI-powered paper summarization using Claude
- 🖼️ Automatic figure extraction and analysis
- 📊 Google Sheets integration for paper tracking and management
- 🌐 Static website generation using Hugo
- 🔄 Continuous deployment with Netlify
- 📱 Planned support for Telegram and Twitter distribution

## Components

1. **Backend**
   - Paper discovery and fetching via Semantic Scholar API
   - Paper caching and management
   - Google Sheets integration for tracking
   - Claude-powered summarization
   - Figure extraction and processing

2. **Static Website**
   - Hugo-based static site
   - Automatic deployment via Netlify
   - Responsive design for all devices
   - Full paper archive with summaries

3. **Planned Features**
   - Telegram bot for paper notifications
   - Twitter bot for sharing summaries
   - User feedback mechanism
   - Paper categorization system

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/ai-safety-reading-list.git
   cd ai-safety-reading-list
   ```

2. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   pip install -r ai-safety-site/site-requirements.txt
   ```

3. Configure API keys and settings:
   - Create `secrets/config.yaml` with your API keys:
     ```yaml
     semantic_scholar:
       api_key: "your_api_key"
     
     google_sheets:
       credentials_file: "your_credentials.json"
       spreadsheet_id: "your_spreadsheet_id"
       range_name: "Sheet1!A1:K"
     
     anthropic:
       api_key: "your_claude_api_key"
     ```

4. Set up Google Sheets:
   - Create a service account and download credentials
   - Share your tracking spreadsheet with the service account email
   - Place credentials JSON in the secrets directory

## Usage

1. Run the backend processor:
   ```bash
   cd backend/src
   python main.py
   ```


2. Build the Hugo site:
   ```bash
   cd ai-safety-site
   hugo server
   ```

## Repurposing for Other Topics

This system can be easily adapted for tracking research papers on any topic. To repurpose:

1. Update the search queries in `main.py`:
   ```python
   queries = ["Your Topic 1", "Your Topic 2"]
   ```

2. Modify the Claude prompts in `paper_summarizer.py` to focus on your topic

3. Update the website configuration in `ai-safety-site/config.toml`

4. Adjust the Google Sheets structure if needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](LICENSE)

## Acknowledgments

- [Semantic Scholar](https://www.semanticscholar.org/) for their API (and for providing a free API key!)
- [Anthropic](https://www.anthropic.com/) for Claude API (unfortunately no free API key usage for us yet 😢)
- [Hugo](https://gohugo.io/) for static site generation
- [Netlify](https://www.netlify.com/) for hosting
- [Monochrome](https://github.com/kaiiiz/hugo-theme-monochrome) - A clean, fast and responsive Hugo theme by [@kaiiiz](https://github.com/kaiiiz)
