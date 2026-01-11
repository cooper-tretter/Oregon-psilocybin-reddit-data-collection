"""
Reddit data scraper for psychedelic therapy experiences.
Uses PullPush API for historical data and Reddit API for recent data.
"""

import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Generator

import requests
from dotenv import load_dotenv

from detector import detect_relevance, DetectionResult
from database import insert_posts, start_collection_run, complete_collection_run

load_dotenv()

# Target subreddits from the spec
TARGET_SUBREDDITS = {
    # Primary subreddits
    'primary': [
        'psychedelics',
        'Psychonaut',
        'TherapeuticKetamine',
        'PsilocybinMushrooms',
        'mdmatherapy',
        'oregon',
        'Colorado',
        'ketamine',
        'Ayahuasca',
        'HPPD',
        'microdosing',
    ],
    # Secondary/regional subreddits
    'secondary': [
        'AustralianPsychedelics',
        'Drugs',
        'depression',
        'PTSD',
        'mentalhealth',
    ]
}

# Search keywords from the spec
SEARCH_KEYWORDS = [
    # Treatment settings
    'psilocybin therapy',
    'psychedelic therapy',
    'facilitated session',
    'licensed facilitator',
    'service center',
    'Oregon psilocybin',
    'Colorado psychedelic',
    'legal psilocybin',
    'legal psychedelic therapy',
    'measure 109',
    'ketamine therapy',
    'ketamine clinic',
    'MDMA therapy',
    'clinical trial',

    # Experience descriptors
    'my session',
    'therapy session',
    'integration',
    'preparation',
]

# API endpoints
PULLPUSH_API = 'https://api.pullpush.io/reddit'
REDDIT_OAUTH_API = 'https://oauth.reddit.com'
REDDIT_AUTH_URL = 'https://www.reddit.com/api/v1/access_token'

# Time range: January 2023 - present (per spec)
START_DATE = datetime(2023, 1, 1)


class PsychedelicTherapyScraper:
    """Scraper for Reddit psychedelic therapy posts."""

    def __init__(self):
        self.session = requests.Session()
        self.reddit_token = None
        self.reddit_token_expires = None
        self._setup_reddit_auth()

    def _setup_reddit_auth(self):
        """Set up Reddit API authentication."""
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'RedditOregon/1.0')

        self.session.headers['User-Agent'] = user_agent

        if client_id and client_secret:
            try:
                auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
                data = {'grant_type': 'client_credentials'}
                response = requests.post(
                    REDDIT_AUTH_URL,
                    auth=auth,
                    data=data,
                    headers={'User-Agent': user_agent}
                )
                if response.status_code == 200:
                    token_data = response.json()
                    self.reddit_token = token_data.get('access_token')
                    expires_in = token_data.get('expires_in', 3600)
                    self.reddit_token_expires = datetime.now() + timedelta(seconds=expires_in)
                    print("Reddit API authenticated successfully")
                else:
                    print(f"Reddit auth failed: {response.status_code}")
            except Exception as e:
                print(f"Reddit auth error: {e}")

    def _get_reddit_headers(self) -> dict:
        """Get headers for Reddit API requests."""
        headers = {'User-Agent': self.session.headers['User-Agent']}
        if self.reddit_token:
            headers['Authorization'] = f'Bearer {self.reddit_token}'
        return headers

    def _hash_username(self, username: str) -> str:
        """Hash username for anonymization."""
        if not username or username == '[deleted]':
            return username
        return hashlib.sha256(username.encode()).hexdigest()[:16]

    def _process_submission(self, data: dict, subreddit: str) -> dict:
        """Process a raw submission into a standardized post dict."""
        text = data.get('selftext', '') or ''
        title = data.get('title', '') or ''

        # Skip deleted/removed content
        if text in ['[deleted]', '[removed]']:
            text = ''

        # Run relevance detection
        detection = detect_relevance(text, title)

        created_utc = data.get('created_utc')
        if isinstance(created_utc, (int, float)):
            created_utc = datetime.utcfromtimestamp(created_utc)

        return {
            'reddit_id': data.get('id'),
            'subreddit': subreddit,
            'author': data.get('author'),
            'title': title,
            'content': text,
            'content_length': len(text),
            'is_comment': False,
            'parent_id': None,
            'is_relevant': detection.is_relevant,
            'relevance_score': detection.relevance_score,
            'category': detection.category,
            'location': detection.location,
            'substance': detection.substance,
            'treatment_setting': detection.treatment_setting,
            'clinical_indication': detection.clinical_indication,
            'outcome_sentiment': detection.outcome_sentiment,
            'mentions_cost': detection.mentions_cost,
            'mentions_facilitator': detection.mentions_facilitator,
            'mentions_integration': detection.mentions_integration,
            'mentions_preparation': detection.mentions_preparation,
            'is_legal_context': detection.is_legal_context,
            'detected_keywords': detection.detected_keywords,
            'external_links': detection.external_links,
            'score': data.get('score', 0),
            'num_comments': data.get('num_comments', 0),
            'post_flair': data.get('link_flair_text'),
            'url': data.get('url'),
            'created_utc': created_utc,
            'data_source': 'pullpush'
        }

    def _process_comment(self, data: dict, subreddit: str) -> dict:
        """Process a raw comment into a standardized post dict."""
        text = data.get('body', '') or ''

        if text in ['[deleted]', '[removed]']:
            text = ''

        detection = detect_relevance(text)

        created_utc = data.get('created_utc')
        if isinstance(created_utc, (int, float)):
            created_utc = datetime.utcfromtimestamp(created_utc)

        return {
            'reddit_id': data.get('id'),
            'subreddit': subreddit,
            'author': data.get('author'),
            'title': None,
            'content': text,
            'content_length': len(text),
            'is_comment': True,
            'parent_id': data.get('parent_id'),
            'is_relevant': detection.is_relevant,
            'relevance_score': detection.relevance_score,
            'category': detection.category,
            'location': detection.location,
            'substance': detection.substance,
            'treatment_setting': detection.treatment_setting,
            'clinical_indication': detection.clinical_indication,
            'outcome_sentiment': detection.outcome_sentiment,
            'mentions_cost': detection.mentions_cost,
            'mentions_facilitator': detection.mentions_facilitator,
            'mentions_integration': detection.mentions_integration,
            'mentions_preparation': detection.mentions_preparation,
            'is_legal_context': detection.is_legal_context,
            'detected_keywords': detection.detected_keywords,
            'external_links': detection.external_links,
            'score': data.get('score', 0),
            'num_comments': 0,
            'post_flair': None,
            'url': data.get('permalink'),
            'created_utc': created_utc,
            'data_source': 'pullpush'
        }

    def fetch_pullpush_submissions(
        self,
        subreddit: str,
        query: str = None,
        after: datetime = None,
        before: datetime = None,
        limit: int = 100
    ) -> Generator[dict, None, None]:
        """
        Fetch submissions from PullPush API.
        Yields processed post dicts.
        """
        params = {
            'subreddit': subreddit,
            'size': min(limit, 100),
            'sort': 'desc',
            'sort_type': 'created_utc'
        }

        if query:
            params['q'] = query

        if after:
            params['after'] = int(after.timestamp())

        if before:
            params['before'] = int(before.timestamp())

        url = f"{PULLPUSH_API}/search/submission/"

        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    submissions = data.get('data', [])

                    for submission in submissions:
                        yield self._process_submission(submission, subreddit)

                    return

                elif response.status_code == 429:
                    print(f"Rate limited, waiting 60s...")
                    time.sleep(60)
                    attempts += 1
                else:
                    print(f"PullPush error: {response.status_code}")
                    attempts += 1
                    time.sleep(5)

            except Exception as e:
                print(f"PullPush request error: {e}")
                attempts += 1
                time.sleep(5)

    def fetch_pullpush_comments(
        self,
        subreddit: str,
        query: str = None,
        after: datetime = None,
        before: datetime = None,
        limit: int = 100
    ) -> Generator[dict, None, None]:
        """
        Fetch comments from PullPush API.
        Yields processed post dicts.
        """
        params = {
            'subreddit': subreddit,
            'size': min(limit, 100),
            'sort': 'desc',
            'sort_type': 'created_utc'
        }

        if query:
            params['q'] = query

        if after:
            params['after'] = int(after.timestamp())

        if before:
            params['before'] = int(before.timestamp())

        url = f"{PULLPUSH_API}/search/comment/"

        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    comments = data.get('data', [])

                    for comment in comments:
                        yield self._process_comment(comment, subreddit)

                    return

                elif response.status_code == 429:
                    print(f"Rate limited, waiting 60s...")
                    time.sleep(60)
                    attempts += 1
                else:
                    print(f"PullPush error: {response.status_code}")
                    attempts += 1
                    time.sleep(5)

            except Exception as e:
                print(f"PullPush request error: {e}")
                attempts += 1
                time.sleep(5)

    def scrape_subreddit(
        self,
        subreddit: str,
        keywords: list[str] = None,
        include_comments: bool = True,
        max_posts: int = 1000
    ) -> tuple[int, int]:
        """
        Scrape a subreddit for relevant posts.
        Returns (posts_fetched, posts_stored).
        """
        print(f"\n{'='*60}")
        print(f"Scraping r/{subreddit}")
        print(f"{'='*60}")

        run_id = start_collection_run(subreddit, ','.join(keywords or []))

        all_posts = []
        fetched = 0
        relevant = 0

        # If keywords provided, search with each keyword
        search_queries = keywords if keywords else [None]

        for query in search_queries:
            if query:
                print(f"\nSearching for: '{query}'")

            # Fetch submissions
            for post in self.fetch_pullpush_submissions(
                subreddit=subreddit,
                query=query,
                after=START_DATE,
                limit=max_posts // len(search_queries)
            ):
                all_posts.append(post)
                fetched += 1
                if post['is_relevant']:
                    relevant += 1

                if fetched % 100 == 0:
                    print(f"  Fetched {fetched} posts ({relevant} relevant)")

            # Rate limiting
            time.sleep(1)

            # Fetch comments if requested
            if include_comments:
                for post in self.fetch_pullpush_comments(
                    subreddit=subreddit,
                    query=query,
                    after=START_DATE,
                    limit=max_posts // (2 * len(search_queries))
                ):
                    all_posts.append(post)
                    fetched += 1
                    if post['is_relevant']:
                        relevant += 1

                time.sleep(1)

        # Insert posts into database
        stored = insert_posts(all_posts)

        complete_collection_run(
            run_id=run_id,
            posts_fetched=fetched,
            posts_stored=stored,
            relevant_found=relevant
        )

        print(f"\nCompleted r/{subreddit}: {fetched} fetched, {stored} stored, {relevant} relevant")

        return fetched, stored

    def scrape_all_subreddits(
        self,
        use_keywords: bool = True,
        include_comments: bool = True,
        max_posts_per_sub: int = 500
    ) -> dict:
        """
        Scrape all target subreddits.
        Returns summary statistics.
        """
        results = {
            'total_fetched': 0,
            'total_stored': 0,
            'by_subreddit': {}
        }

        keywords = SEARCH_KEYWORDS if use_keywords else None

        # Primary subreddits (with keywords)
        for subreddit in TARGET_SUBREDDITS['primary']:
            try:
                fetched, stored = self.scrape_subreddit(
                    subreddit=subreddit,
                    keywords=keywords,
                    include_comments=include_comments,
                    max_posts=max_posts_per_sub
                )
                results['total_fetched'] += fetched
                results['total_stored'] += stored
                results['by_subreddit'][subreddit] = {
                    'fetched': fetched,
                    'stored': stored
                }
            except Exception as e:
                print(f"Error scraping r/{subreddit}: {e}")
                results['by_subreddit'][subreddit] = {'error': str(e)}

            # Rate limiting between subreddits
            time.sleep(2)

        # Secondary subreddits (keywords only, no full scrape)
        for subreddit in TARGET_SUBREDDITS['secondary']:
            try:
                fetched, stored = self.scrape_subreddit(
                    subreddit=subreddit,
                    keywords=keywords,  # Always use keywords for secondary
                    include_comments=False,  # Skip comments for secondary
                    max_posts=max_posts_per_sub // 2
                )
                results['total_fetched'] += fetched
                results['total_stored'] += stored
                results['by_subreddit'][subreddit] = {
                    'fetched': fetched,
                    'stored': stored
                }
            except Exception as e:
                print(f"Error scraping r/{subreddit}: {e}")
                results['by_subreddit'][subreddit] = {'error': str(e)}

            time.sleep(2)

        return results

    def search_across_reddit(
        self,
        query: str,
        max_results: int = 500
    ) -> tuple[int, int]:
        """
        Search across all of Reddit for a specific query.
        Returns (fetched, stored).
        """
        print(f"\nSearching all Reddit for: '{query}'")

        all_posts = []
        fetched = 0

        # PullPush doesn't require subreddit
        params = {
            'q': query,
            'size': min(max_results, 100),
            'sort': 'desc',
            'sort_type': 'created_utc',
            'after': int(START_DATE.timestamp())
        }

        url = f"{PULLPUSH_API}/search/submission/"

        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for submission in data.get('data', []):
                    subreddit = submission.get('subreddit', 'unknown')
                    post = self._process_submission(submission, subreddit)
                    all_posts.append(post)
                    fetched += 1
        except Exception as e:
            print(f"Search error: {e}")

        stored = insert_posts(all_posts)
        print(f"Search complete: {fetched} fetched, {stored} stored")

        return fetched, stored


if __name__ == '__main__':
    # Test scraper
    scraper = PsychedelicTherapyScraper()

    # Test with a single keyword search
    print("Testing scraper with 'oregon psilocybin' search...")
    fetched, stored = scraper.search_across_reddit('oregon psilocybin', max_results=50)
    print(f"Test complete: {fetched} posts fetched, {stored} stored")
