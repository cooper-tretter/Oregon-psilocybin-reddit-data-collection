"""
Database operations for RedditOregon psychedelic therapy data collection.
Handles PostgreSQL connections, queries, and data insertion.
"""

import os
import json
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import execute_values, Json
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create and return a database connection."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'reddit_oregon'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


def init_database():
    """Initialize database tables from schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("Database initialized successfully")
    finally:
        conn.close()


def insert_posts(posts: list[dict]) -> int:
    """
    Insert posts into the database, skipping duplicates.
    Returns number of posts inserted.
    """
    if not posts:
        return 0

    conn = get_connection()
    inserted = 0

    try:
        with conn.cursor() as cur:
            for post in posts:
                try:
                    cur.execute("""
                        INSERT INTO posts (
                            reddit_id, subreddit, author, title, content, content_length,
                            is_comment, parent_id, is_relevant, relevance_score, category,
                            location, substance, treatment_setting, clinical_indication,
                            outcome_sentiment, mentions_cost, mentions_facilitator,
                            mentions_integration, mentions_preparation, is_legal_context,
                            detected_keywords, external_links, score, num_comments,
                            post_flair, url, created_utc, data_source
                        ) VALUES (
                            %(reddit_id)s, %(subreddit)s, %(author)s, %(title)s, %(content)s,
                            %(content_length)s, %(is_comment)s, %(parent_id)s, %(is_relevant)s,
                            %(relevance_score)s, %(category)s, %(location)s, %(substance)s,
                            %(treatment_setting)s, %(clinical_indication)s, %(outcome_sentiment)s,
                            %(mentions_cost)s, %(mentions_facilitator)s, %(mentions_integration)s,
                            %(mentions_preparation)s, %(is_legal_context)s, %(detected_keywords)s,
                            %(external_links)s, %(score)s, %(num_comments)s, %(post_flair)s,
                            %(url)s, %(created_utc)s, %(data_source)s
                        )
                        ON CONFLICT (reddit_id) DO NOTHING
                    """, {
                        'reddit_id': post.get('reddit_id'),
                        'subreddit': post.get('subreddit'),
                        'author': post.get('author'),
                        'title': post.get('title'),
                        'content': post.get('content'),
                        'content_length': post.get('content_length', 0),
                        'is_comment': post.get('is_comment', False),
                        'parent_id': post.get('parent_id'),
                        'is_relevant': post.get('is_relevant', False),
                        'relevance_score': post.get('relevance_score', 0.0),
                        'category': post.get('category'),
                        'location': post.get('location'),
                        'substance': post.get('substance'),
                        'treatment_setting': post.get('treatment_setting'),
                        'clinical_indication': post.get('clinical_indication'),
                        'outcome_sentiment': post.get('outcome_sentiment'),
                        'mentions_cost': post.get('mentions_cost', False),
                        'mentions_facilitator': post.get('mentions_facilitator', False),
                        'mentions_integration': post.get('mentions_integration', False),
                        'mentions_preparation': post.get('mentions_preparation', False),
                        'is_legal_context': post.get('is_legal_context', False),
                        'detected_keywords': Json(post.get('detected_keywords', {})),
                        'external_links': post.get('external_links', []),
                        'score': post.get('score', 0),
                        'num_comments': post.get('num_comments', 0),
                        'post_flair': post.get('post_flair'),
                        'url': post.get('url'),
                        'created_utc': post.get('created_utc'),
                        'data_source': post.get('data_source', 'reddit')
                    })
                    if cur.rowcount > 0:
                        inserted += 1
                except psycopg2.Error as e:
                    print(f"Error inserting post {post.get('reddit_id')}: {e}")
                    conn.rollback()
                    continue

            conn.commit()
    finally:
        conn.close()

    return inserted


def insert_comments(comments: list[dict]) -> int:
    """Insert comments into the database."""
    if not comments:
        return 0

    conn = get_connection()
    inserted = 0

    try:
        with conn.cursor() as cur:
            for comment in comments:
                try:
                    cur.execute("""
                        INSERT INTO comments (
                            reddit_id, parent_post_id, author, content,
                            content_length, score, created_utc
                        ) VALUES (
                            %(reddit_id)s, %(parent_post_id)s, %(author)s,
                            %(content)s, %(content_length)s, %(score)s, %(created_utc)s
                        )
                        ON CONFLICT (reddit_id) DO NOTHING
                    """, comment)
                    if cur.rowcount > 0:
                        inserted += 1
                except psycopg2.Error as e:
                    print(f"Error inserting comment {comment.get('reddit_id')}: {e}")
                    conn.rollback()
                    continue

            conn.commit()
    finally:
        conn.close()

    return inserted


def start_collection_run(subreddit: str, search_query: str = None) -> int:
    """Start a new collection run and return its ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO collection_runs (subreddit, search_query, status)
                VALUES (%s, %s, 'running')
                RETURNING id
            """, (subreddit, search_query))
            run_id = cur.fetchone()[0]
            conn.commit()
            return run_id
    finally:
        conn.close()


def complete_collection_run(run_id: int, posts_fetched: int, posts_stored: int,
                           relevant_found: int, status: str = 'completed',
                           error_message: str = None):
    """Mark a collection run as complete."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE collection_runs
                SET completed_at = NOW(),
                    posts_fetched = %s,
                    posts_stored = %s,
                    relevant_found = %s,
                    status = %s,
                    error_message = %s
                WHERE id = %s
            """, (posts_fetched, posts_stored, relevant_found, status, error_message, run_id))
            conn.commit()
    finally:
        conn.close()


def update_author_stats():
    """Update aggregated author statistics."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO authors (username, total_posts, relevant_posts, relevance_rate,
                                    first_seen, last_seen, active_subreddits)
                SELECT
                    author,
                    COUNT(*) as total_posts,
                    COUNT(*) FILTER (WHERE is_relevant) as relevant_posts,
                    COALESCE(COUNT(*) FILTER (WHERE is_relevant)::float / NULLIF(COUNT(*), 0), 0) as relevance_rate,
                    MIN(created_utc) as first_seen,
                    MAX(created_utc) as last_seen,
                    ARRAY_AGG(DISTINCT subreddit) as active_subreddits
                FROM posts
                WHERE author IS NOT NULL AND author != '[deleted]'
                GROUP BY author
                ON CONFLICT (username) DO UPDATE SET
                    total_posts = EXCLUDED.total_posts,
                    relevant_posts = EXCLUDED.relevant_posts,
                    relevance_rate = EXCLUDED.relevance_rate,
                    last_seen = EXCLUDED.last_seen,
                    active_subreddits = EXCLUDED.active_subreddits,
                    updated_at = NOW()
            """)
            conn.commit()
    finally:
        conn.close()


def get_post_count() -> int:
    """Get total number of posts in database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM posts")
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_relevant_post_count() -> int:
    """Get number of relevant posts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM posts WHERE is_relevant = TRUE")
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_posts_by_subreddit() -> dict:
    """Get post counts grouped by subreddit."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT subreddit, COUNT(*), COUNT(*) FILTER (WHERE is_relevant)
                FROM posts
                GROUP BY subreddit
                ORDER BY COUNT(*) DESC
            """)
            return {row[0]: {'total': row[1], 'relevant': row[2]} for row in cur.fetchall()}
    finally:
        conn.close()


def get_posts_by_location() -> dict:
    """Get post counts grouped by location."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT location, COUNT(*)
                FROM posts
                WHERE location IS NOT NULL
                GROUP BY location
                ORDER BY COUNT(*) DESC
            """)
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()


def get_posts_by_substance() -> dict:
    """Get post counts grouped by substance."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT substance, COUNT(*)
                FROM posts
                WHERE substance IS NOT NULL
                GROUP BY substance
                ORDER BY COUNT(*) DESC
            """)
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()


def get_all_posts(limit: int = None, relevant_only: bool = False) -> list[dict]:
    """Retrieve all posts from the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = "SELECT * FROM posts"
            conditions = []

            if relevant_only:
                conditions.append("is_relevant = TRUE")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_utc DESC"

            if limit:
                query += f" LIMIT {limit}"

            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def export_to_csv(filepath: str, relevant_only: bool = False):
    """Export posts to CSV file."""
    import csv

    posts = get_all_posts(relevant_only=relevant_only)

    if not posts:
        print("No posts to export")
        return

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=posts[0].keys())
        writer.writeheader()
        writer.writerows(posts)

    print(f"Exported {len(posts)} posts to {filepath}")


if __name__ == '__main__':
    # Test database connection and initialization
    try:
        init_database()
        print(f"Total posts: {get_post_count()}")
        print(f"Relevant posts: {get_relevant_post_count()}")
    except Exception as e:
        print(f"Database error: {e}")
