-- LeadPrep AI Database Setup Script
-- Run this in your Supabase SQL Editor

-- Enable Row Level Security (RLS)
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    domain TEXT UNIQUE NOT NULL,
    name TEXT,
    industry TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create leaders table
CREATE TABLE IF NOT EXISTS leaders (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    title TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id BIGSERIAL PRIMARY KEY,
    leader_id BIGINT REFERENCES leaders(id) ON DELETE CASCADE,
    title TEXT,
    url TEXT,
    source_type TEXT CHECK (source_type IN ('youtube', 'podcast', 'article', 'other')),
    transcript TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create summaries table for storing AI-generated summaries
CREATE TABLE IF NOT EXISTS summaries (
    id BIGSERIAL PRIMARY KEY,
    interview_id BIGINT REFERENCES interviews(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    summary_type TEXT DEFAULT 'strategic_priorities',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_leaders_company_id ON leaders(company_id);
CREATE INDEX IF NOT EXISTS idx_leaders_name ON leaders(name);
CREATE INDEX IF NOT EXISTS idx_interviews_leader_id ON interviews(leader_id);
CREATE INDEX IF NOT EXISTS idx_interviews_source_type ON interviews(source_type);
CREATE INDEX IF NOT EXISTS idx_summaries_interview_id ON summaries(interview_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON companies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leaders_updated_at 
    BEFORE UPDATE ON leaders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - for future user authentication
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaders ENABLE ROW LEVEL SECURITY;
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (for now)
CREATE POLICY "Allow public read access to companies" ON companies
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to leaders" ON leaders
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to interviews" ON interviews
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to summaries" ON summaries
    FOR SELECT USING (true);

-- Create policies for insert/update (for now, allow all)
CREATE POLICY "Allow public insert to companies" ON companies
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public insert to leaders" ON leaders
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public insert to interviews" ON interviews
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public insert to summaries" ON summaries
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update to companies" ON companies
    FOR UPDATE USING (true);

CREATE POLICY "Allow public update to leaders" ON leaders
    FOR UPDATE USING (true);

-- Insert some sample data for testing
INSERT INTO companies (domain, name, industry) VALUES 
    ('apple.com', 'Apple Inc.', 'Technology'),
    ('microsoft.com', 'Microsoft Corporation', 'Technology'),
    ('google.com', 'Alphabet Inc.', 'Technology')
ON CONFLICT (domain) DO NOTHING;

-- Insert sample leaders
INSERT INTO leaders (company_id, name, title) VALUES 
    ((SELECT id FROM companies WHERE domain = 'apple.com'), 'Tim Cook', 'CEO'),
    ((SELECT id FROM companies WHERE domain = 'apple.com'), 'Jeff Williams', 'COO'),
    ((SELECT id FROM companies WHERE domain = 'microsoft.com'), 'Satya Nadella', 'CEO'),
    ((SELECT id FROM companies WHERE domain = 'microsoft.com'), 'Brad Smith', 'President'),
    ((SELECT id FROM companies WHERE domain = 'google.com'), 'Sundar Pichai', 'CEO'),
    ((SELECT id FROM companies WHERE domain = 'google.com'), 'Ruth Porat', 'CFO')
ON CONFLICT DO NOTHING;

-- Display table information
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Display sample data
SELECT 'Companies' as table_name, COUNT(*) as count FROM companies
UNION ALL
SELECT 'Leaders' as table_name, COUNT(*) as count FROM leaders
UNION ALL
SELECT 'Interviews' as table_name, COUNT(*) as count FROM interviews
UNION ALL
SELECT 'Summaries' as table_name, COUNT(*) as count FROM summaries; 