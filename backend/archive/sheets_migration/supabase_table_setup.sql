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