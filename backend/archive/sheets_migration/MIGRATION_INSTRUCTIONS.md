# Supabase Migration Instructions

## Current Status

We have successfully:
1. Set up the `.env` file with Supabase credentials
2. Created the necessary SQL scripts for table setup
3. Implemented the Supabase DB client class
4. Created migration scripts
5. Implemented test scripts for validation

However, we encountered an issue: **The Supabase table must be created manually.**

## Step 1: Create the Table in Supabase

1. Log in to your Supabase dashboard: https://app.supabase.com
2. Navigate to your project (iiowsdbaiojdbazxuqwj)
3. Click on "SQL Editor" in the left sidebar
4. Create a new query
5. Paste the following SQL and execute it:

```sql
-- Create papers table
CREATE TABLE IF NOT EXISTS papers (
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

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS papers_highlight_idx ON papers (highlight);
CREATE INDEX IF NOT EXISTS papers_include_on_website_idx ON papers (include_on_website);

-- Enable row-level security
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow anonymous read access" ON papers
    FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "Allow authenticated full access" ON papers
    FOR ALL
    TO authenticated
    USING (true);
```

## Step 2: Verify the Table was Created

Run the following script to check if the table was created successfully:

```bash
cd /Users/alex/Desktop/playground/ai-safety-papers/backend && python src/check_table_exists.py
```

You should see a success message indicating that the table exists and is accessible.

## Step 3: Run the Migration Script

Once the table is verified, run the migration script to transfer data from Google Sheets to Supabase:

```bash
cd /Users/alex/Desktop/playground/ai-safety-papers/backend && python src/migrate_to_supabase.py --url $(grep SUPABASE_URL .env | cut -d= -f2) --key $(grep SUPABASE_KEY .env | cut -d= -f2)
```

## Step 4: Verify the Migration

Run a test to ensure the data was migrated successfully:

```bash
cd /Users/alex/Desktop/playground/ai-safety-papers/backend && python src/test_supabase.py
```

## Step 5: Update the API to Use Supabase

The code has been updated to use Supabase for all data operations. Once the migration is complete, the API will automatically use the new database.

## Troubleshooting

If you encounter issues with the migration:

1. Check the Supabase logs in the dashboard for any errors
2. Ensure your Supabase API key has the correct permissions
3. Check the migration.log file for detailed error information
4. Try running the test_insert_paper.py script to test basic functionality

## Next Steps

After successful migration:

1. Test the API endpoints to ensure they're working with Supabase
2. Update any documentation to reflect the new database
3. Consider setting up database backups
4. Remove the Google Sheets integration if no longer needed