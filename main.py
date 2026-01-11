#!/usr/bin/env python3
"""
RedditOregon: Reddit Psychedelic Therapy Data Collection
CLI entry point for data collection operations.

Usage:
    python main.py                    # Full collection (all subreddits)
    python main.py --subreddit oregon # Single subreddit
    python main.py --search "psilocybin therapy"  # Search query
    python main.py --export data/posts.csv  # Export to CSV
    python main.py --stats            # Show statistics
"""

import argparse
import sys
from datetime import datetime

from database import init_database, get_post_count, get_relevant_post_count
from database import get_posts_by_subreddit, get_posts_by_location, get_posts_by_substance
from database import export_to_csv, update_author_stats
from scraper import PsychedelicTherapyScraper, TARGET_SUBREDDITS, SEARCH_KEYWORDS


def print_banner():
    """Print application banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║  RedditOregon: Psychedelic Therapy Experience Data Collector  ║
║  Collecting real-world experiences from Reddit                ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def show_stats():
    """Display current database statistics."""
    print("\n📊 Database Statistics")
    print("=" * 50)

    total = get_post_count()
    relevant = get_relevant_post_count()

    print(f"Total posts:    {total:,}")
    print(f"Relevant posts: {relevant:,}")
    if total > 0:
        print(f"Relevance rate: {relevant/total*100:.1f}%")

    print("\n📍 By Subreddit:")
    by_sub = get_posts_by_subreddit()
    for sub, counts in list(by_sub.items())[:15]:
        print(f"  r/{sub}: {counts['total']:,} total, {counts['relevant']:,} relevant")

    print("\n🌍 By Location:")
    by_loc = get_posts_by_location()
    for loc, count in list(by_loc.items())[:10]:
        print(f"  {loc}: {count:,}")

    print("\n💊 By Substance:")
    by_sub = get_posts_by_substance()
    for sub, count in list(by_sub.items())[:10]:
        print(f"  {sub}: {count:,}")


def run_collection(args):
    """Run data collection based on arguments."""
    scraper = PsychedelicTherapyScraper()

    if args.search:
        # Search across all of Reddit
        print(f"\n🔍 Searching Reddit for: '{args.search}'")
        fetched, stored = scraper.search_across_reddit(
            query=args.search,
            max_results=args.max_posts
        )
        print(f"\nSearch complete: {fetched} posts found, {stored} new posts stored")

    elif args.subreddit:
        # Single subreddit
        print(f"\n📥 Scraping r/{args.subreddit}")
        keywords = SEARCH_KEYWORDS if args.use_keywords else None
        fetched, stored = scraper.scrape_subreddit(
            subreddit=args.subreddit,
            keywords=keywords,
            include_comments=args.include_comments,
            max_posts=args.max_posts
        )
        print(f"\nComplete: {fetched} posts fetched, {stored} stored")

    else:
        # Full collection
        print("\n📥 Starting full collection across all target subreddits")
        print(f"Primary subreddits: {', '.join(TARGET_SUBREDDITS['primary'])}")
        print(f"Secondary subreddits: {', '.join(TARGET_SUBREDDITS['secondary'])}")

        results = scraper.scrape_all_subreddits(
            use_keywords=args.use_keywords,
            include_comments=args.include_comments,
            max_posts_per_sub=args.max_posts
        )

        print("\n" + "=" * 60)
        print("📊 Collection Summary")
        print("=" * 60)
        print(f"Total fetched: {results['total_fetched']:,}")
        print(f"Total stored:  {results['total_stored']:,}")
        print("\nBy subreddit:")
        for sub, data in results['by_subreddit'].items():
            if 'error' in data:
                print(f"  r/{sub}: ERROR - {data['error']}")
            else:
                print(f"  r/{sub}: {data['fetched']} fetched, {data['stored']} stored")

    # Update author stats after collection
    print("\n🔄 Updating author statistics...")
    update_author_stats()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='RedditOregon: Psychedelic Therapy Experience Data Collector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           Full collection
  python main.py --subreddit oregon        Single subreddit
  python main.py --search "ketamine clinic"  Search query
  python main.py --export posts.csv        Export data
  python main.py --stats                   Show statistics
  python main.py --init-db                 Initialize database
        """
    )

    parser.add_argument(
        '--subreddit', '-s',
        help='Scrape a specific subreddit'
    )
    parser.add_argument(
        '--search', '-q',
        help='Search query across all of Reddit'
    )
    parser.add_argument(
        '--max-posts', '-m',
        type=int,
        default=500,
        help='Maximum posts per subreddit/search (default: 500)'
    )
    parser.add_argument(
        '--no-keywords',
        dest='use_keywords',
        action='store_false',
        help='Disable keyword filtering'
    )
    parser.add_argument(
        '--no-comments',
        dest='include_comments',
        action='store_false',
        help='Skip collecting comments'
    )
    parser.add_argument(
        '--export', '-e',
        help='Export posts to CSV file'
    )
    parser.add_argument(
        '--export-relevant',
        action='store_true',
        help='Only export relevant posts'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database tables'
    )

    args = parser.parse_args()

    print_banner()
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Initialize database if requested
        if args.init_db:
            print("\n🔧 Initializing database...")
            init_database()
            print("Database initialized successfully")
            if not any([args.stats, args.export, args.subreddit, args.search]):
                return

        # Show statistics
        if args.stats:
            show_stats()
            return

        # Export data
        if args.export:
            print(f"\n📤 Exporting posts to {args.export}")
            export_to_csv(args.export, relevant_only=args.export_relevant)
            return

        # Run collection
        run_collection(args)

    except KeyboardInterrupt:
        print("\n\n⚠️ Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
