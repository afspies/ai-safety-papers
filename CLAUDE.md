# AI Safety Papers Project Guidelines

## Build & Test Commands
- Python backend (using conda): `cd backend && conda activate ai-safety-papers && PYTHONPATH=/Users/alex/Desktop/playground/ai-safety-papers python src/main.py`
- Run server (using manage.py): `cd backend && conda activate ai-safety-papers && python manage.py start`
- Run Hugo site: `cd ai-safety-site && hugo server`
- Run specific test: `cd backend && conda activate ai-safety-papers && PYTHONPATH=/Users/alex/Desktop/playground/ai-safety-papers python -m pytest src/tests/test_filename.py::test_function -v`
- Install dependencies: `pip install -r backend/requirements.txt && pip install -r ai-safety-site/site-requirements.txt`
- Test API: `cd backend && conda activate ai-safety-papers && PYTHONPATH=/Users/alex/Desktop/playground/ai-safety-papers python test_api.py`
- Full pipeline test: `cd backend && conda activate ai-safety-papers && export DEVELOPMENT_MODE=true && PYTHONPATH=/Users/alex/Desktop/playground/ai-safety-papers python run_processing.py`

## API Endpoints
- Root: `GET /` - Returns API info and available endpoints
- Papers: `GET /api/papers` - Returns list of all papers
- Highlighted Papers: `GET /api/papers/highlighted` - Returns highlighted papers
- Paper Details: `GET /api/papers/{paper_id}` - Returns detailed info for specific paper
- Paper Figures: `GET /api/papers/{paper_id}/figures` - Returns figures for specific paper
- Figure: `GET /api/papers/{paper_id}/figures/{figure_id}` - Returns specific figure for a paper

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
- Data storage: Supabase database and Cloudflare R2 for figures

## Progress (March 2025)
- API server implementation successfully completed
- Mock database integration for testing is working
- Papers can be fetched from Semantic Scholar and stored in Supabase
- Real paper data is properly returned through the API endpoints
- Figure handling is implemented with Cloudflare R2 integration
- API now supports both sample test papers and real papers
- API can handle different paper formats and convert to standardized Article objects
- API endpoints include proper error handling and documentation

## Summary Pipeline Improvements (March 2025)
- Enhanced the paper summarizer prompt for Claude to generate more detailed, structured summaries
- Improved figure integration in post generation with better formatting and explanations
- Fixed issues with duplicate headings and figure references
- Added support for parsing both tagged (<FIGURE_ID>) and plain text (Figure N) figure references
- Made regex matching more robust for extracting summary and figure sections
- Added tracking to prevent duplicate figure insertions in the final markdown