# AI-Safety Reading List Project

## Backend
- [x] Set up project structure and environment
- [x] Implement arXiv API integration
  - [x] Create function to search for recent AI safety papers
  - [x] Implement filtering for papers from the last few days
  - [x] Increase the number of papers fetched per day
  - [x] Update search query to include multiple relevant keywords
  - [x] Expand search to cover more categories and a longer time range
- [ ] Develop caching mechanism for fetched articles
- [x] Set up Google Sheets integration
  - [x] Create a new sheet for storing article details
  - [x] Implement function to add new articles to the sheet
  - [x] Add informative header row to the Google Sheet
  - [x] Fix error handling in add_entry method
  - [x] Implement cleaning of old, unposted papers
- [x] Create secrets management system
  - [x] Implement YAML-based configuration
  - [x] Create utility function for loading configuration
- [x] Set up article download query for AI safety topics
- [ ] Integrate Anthropic API for article summarization
  - [ ] Create Claude prompt for effective summarization
  - [ ] Implement function to summarize articles using Claude
- [x] Develop main script to orchestrate the backend processes
  - [x] Fetch articles, add to Google Sheets
  - [x] Implement error handling for API calls
  - [ ] Implement caching mechanism
  - [ ] Implement summarization
  - [ ] Use the recommendations API endpoint to show recommended articles for each article we post
  - [ ] For each article marked for posting, scrape <= 3 recommended articles and include them in the posts
  - [ ] This can be implemented by adding a new method to the SemanticScholarAPI class and calling it here after processing each paper or in a separate function that runs after process_new_papers

## Telegram Bot
- [ ] Set up Telegram bot using BotFather
- [ ] Implement bot functionality
  - [ ] Create command to subscribe/unsubscribe users
  - [ ] Develop function to send summaries to subscribed users
- [ ] Integrate bot with backend to receive new summaries

## Twitter Bot
- [ ] Set up Twitter Developer account and create app
- [ ] Implement Twitter bot functionality
  - [ ] Create function to post summaries as tweets
  - [ ] Implement scheduling for regular posting
- [ ] Integrate bot with backend to receive new summaries

## Static Website
- [ ] Set up Hugo project structure
- [ ] Implement data fetching from Google Sheets
- [ ] Create Hugo templates for:
  - [ ] Home page listing all articles
  - [ ] Individual article pages with summaries
- [ ] Implement search functionality
- [ ] Set up automatic build and deployment process

## General Tasks
- [ ] Implement error handling and logging throughout the project
- [ ] Set up unit tests for critical functions
- [ ] Create documentation for each component
- [ ] Implement rate limiting for API calls
- [ ] Set up monitoring and alerts for the system

## Future Enhancements
- [ ] Implement user feedback mechanism for summaries
- [ ] Add categorization for articles
- [ ] Develop recommendation system based on user preferences
