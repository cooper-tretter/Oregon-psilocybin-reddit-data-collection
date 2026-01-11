-- RedditOregon: Psychedelic Therapy Experience Database Schema
-- Tracks Reddit posts about legal psychedelic-assisted therapy experiences

-- Posts table: Core content storage
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(20) UNIQUE NOT NULL,
    subreddit VARCHAR(100) NOT NULL,
    author VARCHAR(50),
    title TEXT,
    content TEXT,
    content_length INTEGER,
    is_comment BOOLEAN DEFAULT FALSE,
    parent_id VARCHAR(20),

    -- Classification fields
    is_relevant BOOLEAN DEFAULT FALSE,
    relevance_score FLOAT DEFAULT 0.0,
    category VARCHAR(50),  -- experience_report, question, discussion, etc.

    -- Content variables (to be coded/extracted)
    location VARCHAR(100),  -- Oregon, Colorado, Australia, etc.
    substance VARCHAR(100),  -- psilocybin, MDMA, ketamine, etc.
    treatment_setting VARCHAR(100),  -- clinical_trial, service_center, therapeutic, other
    clinical_indication VARCHAR(100),  -- depression, PTSD, anxiety, etc.
    outcome_sentiment VARCHAR(50),  -- positive, negative, mixed, neutral
    mentions_cost BOOLEAN DEFAULT FALSE,
    mentions_facilitator BOOLEAN DEFAULT FALSE,
    mentions_integration BOOLEAN DEFAULT FALSE,
    mentions_preparation BOOLEAN DEFAULT FALSE,
    is_legal_context BOOLEAN DEFAULT FALSE,

    -- Extracted metadata
    detected_keywords JSONB DEFAULT '{}',
    external_links TEXT[],

    -- Reddit metadata
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    post_flair VARCHAR(200),
    url TEXT,
    created_utc TIMESTAMP,

    -- Collection metadata
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'reddit'
);

-- Authors table: Aggregated author statistics
CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    total_posts INTEGER DEFAULT 0,
    relevant_posts INTEGER DEFAULT 0,
    relevance_rate FLOAT DEFAULT 0.0,
    primary_subreddit VARCHAR(100),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    active_subreddits TEXT[],
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Collection runs table: Track scraping operations
CREATE TABLE IF NOT EXISTS collection_runs (
    id SERIAL PRIMARY KEY,
    subreddit VARCHAR(100) NOT NULL,
    search_query TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    posts_fetched INTEGER DEFAULT 0,
    posts_stored INTEGER DEFAULT 0,
    relevant_found INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'running',
    error_message TEXT
);

-- Comments table: Store top-level comments on relevant posts
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(20) UNIQUE NOT NULL,
    parent_post_id VARCHAR(20) REFERENCES posts(reddit_id),
    author VARCHAR(50),
    content TEXT,
    content_length INTEGER,
    score INTEGER DEFAULT 0,
    created_utc TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Summary statistics table: Pre-computed stats for reporting
CREATE TABLE IF NOT EXISTS summary_stats (
    id SERIAL PRIMARY KEY,
    stat_type VARCHAR(100) NOT NULL,
    stat_key VARCHAR(200),
    stat_value FLOAT,
    stat_count INTEGER,
    metadata JSONB DEFAULT '{}',
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_is_relevant ON posts(is_relevant);
CREATE INDEX IF NOT EXISTS idx_posts_location ON posts(location);
CREATE INDEX IF NOT EXISTS idx_posts_substance ON posts(substance);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author);
CREATE INDEX IF NOT EXISTS idx_posts_relevance_score ON posts(relevance_score);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_post_id);
CREATE INDEX IF NOT EXISTS idx_collection_runs_subreddit ON collection_runs(subreddit);
