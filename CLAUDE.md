# AI Safety Papers Project Guidelines

## Build & Test Commands
- Python backend: `cd backend/src && python main.py`
- Run Hugo site: `cd ai-safety-site && hugo server`
- Run specific test: `cd backend && python -m pytest src/tests/test_filename.py::test_function -v`
- Install dependencies: `pip install -r backend/requirements.txt && pip install -r ai-safety-site/site-requirements.txt`

## Code Style Guidelines
- Python: Follow PEP 8 guidelines
- Use type hints for all function parameters and return types
- Import order: stdlib → third-party → local modules
- Error handling: Use try/except blocks with specific exceptions
- Naming: snake_case for functions/variables, CamelCase for classes
- Documentation: Docstrings for all functions and classes
- Tests: Write pytest tests for all new functionality

## Project Organization
- Backend: Paper fetching, summarization, and figure extraction
- AI-Safety-Site: Hugo static site for displaying summaries
- Data storage: Google Sheets integration for paper tracking

## Summary Pipeline Improvements (March 2025)
- Enhanced the paper summarizer prompt for Claude to generate more detailed, structured summaries
- Improved figure integration in post generation with better formatting and explanations
- Fixed issues with duplicate headings and figure references
- Added support for parsing both tagged (<FIGURE_ID>) and plain text (Figure N) figure references
- Made regex matching more robust for extracting summary and figure sections
- Added tracking to prevent duplicate figure insertions in the final markdown