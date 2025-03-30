# AI Safety Papers Backend

This is the backend for the AI Safety Papers project. It handles fetching, processing, and summarizing AI safety research papers.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the backend directory with your Supabase credentials (see `.env.example` for template)

3. Configure Supabase:
   - Create a new project in Supabase
   - Create a table called `papers` with the following schema:
   ```sql
   CREATE TABLE papers (
       id text PRIMARY KEY,
       title text NOT NULL,
       authors text[] DEFAULT '{}',
       year text,
       abstract text DEFAULT '',
       url text DEFAULT '',
       venue text DEFAULT '',
       tldr text DEFAULT '',
       submitted_date timestamp with time zone,
       highlight boolean DEFAULT false,
       include_on_website boolean DEFAULT false,
       post_to_bots boolean DEFAULT false,
       posted_date timestamp with time zone,
       ai_safety_relevance integer DEFAULT 0,
       mech_int_relevance integer DEFAULT 0,
       embedding_model text DEFAULT '',
       embedding_vector float[] DEFAULT '{}',
       tags text[] DEFAULT '{}'
   );

   -- Create index for faster queries
   CREATE INDEX papers_highlight_idx ON papers (highlight);
   CREATE INDEX papers_include_on_website_idx ON papers (include_on_website);
   ```

4. Migrate data from Google Sheets using the Supabase API client:
   ```bash
   python src/migrate_to_supabase.py --url "https://iiowsdbaiojdbazxuqwj.supabase.co" --key "your-supabase-anon-key"
   ```
   Replace the URL and key with your actual Supabase project URL and API key.

## Usage

### Server Management
Use the provided management script to control the backend server and Cloudflared tunnel:

```bash
# Start the backend server and Cloudflared tunnel
python manage.py start

# Stop the backend server and Cloudflared tunnel
python manage.py stop

# Restart the backend server and Cloudflared tunnel
python manage.py restart

# Check the status of the server and tunnel
python manage.py status
```

The management script:
- Properly tracks running processes with PID files
- Handles graceful shutdown of services
- Supports development mode with mock API clients
- Ensures consistent environment variables
- Provides clear logging and error handling

#### Development Mode
The server can run in development mode without requiring valid API keys or credentials:

```bash
# Set development mode environment variable
export DEVELOPMENT_MODE=true

# Start the server in development mode
python manage.py start
```

This mode uses mock clients for Supabase and other external services, allowing you to test the API endpoints without connecting to real services.

### Run API Server Manually
```bash
python src/main.py --api
```

### Process new papers
```bash
python src/main.py
```

### Reprocess specific parts
```bash
python src/main.py --reprocess figures
python src/main.py --reprocess summary
python src/main.py --reprocess markdown
python src/main.py --reprocess info
python src/main.py --reprocess all
```

### Process a specific paper
```bash
python src/main.py --paper-id <paper_id>
```

## API Endpoints

- `GET /api/papers`: Get all papers
- `GET /api/papers/highlighted`: Get highlighted papers
- `GET /api/papers/{paper_id}`: Get details for a specific paper