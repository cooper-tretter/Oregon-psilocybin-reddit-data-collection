# RedditOregon

A Python tool for collecting and analyzing Reddit posts about psilocybin therapy experiences in Oregon and Colorado. This project supports research into real-world outcomes of legal psilocybin-assisted therapy under Oregon's Measure 109 and Colorado's Natural Medicine Health Act.

## Overview

With legal psilocybin therapy now available in Oregon and Colorado, Reddit has become an important venue where individuals share first-person accounts of their therapeutic experiences. This tool systematically collects these naturalistic reports to complement clinical trial data, capturing perspectives on:

- Subjective acute experiences during sessions
- Perceived short and long-term outcomes
- Quality of service delivery and facilitator interactions
- Preparation and integration processes
- Challenges and adverse experiences

## Features

- **Multi-source data collection**: Uses both Reddit API (for recent posts) and PullPush API (for historical data)
- **Automated relevance detection**: Weighted keyword matching algorithm to identify relevant first-person experience reports
- **Location filtering**: Focuses on Oregon and Colorado-specific therapeutic experiences
- **Exclusion filters**: Automatically filters out news articles, cultivation posts, sourcing requests, and other non-experience content
- **PostgreSQL database**: Stores posts with metadata including relevance scores, detected substances, locations, and clinical indications
- **Interactive dashboard**: Dash-based visualization with filtering and drilldown capabilities
- **Data export**: Export to CSV and Excel formats

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Reddit API credentials (optional, for recent data)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cooper-tretter/Oregon-psilocybin-reddit-data-collection.git
   cd Oregon-psilocybin-reddit-data-collection
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your database and Reddit API credentials
   ```

4. Initialize the database:
   ```bash
   python main.py --init-db
   ```

## Usage

### Data Collection

```bash
# Full collection across all target subreddits
python main.py

# Scrape a specific subreddit
python main.py --subreddit oregon

# Search across Reddit
python main.py --search "psilocybin therapy"

# Limit posts per subreddit
python main.py --max-posts 100
```

### Data Export

```bash
# Export all posts to CSV
python main.py --export data/posts.csv

# Export only relevant posts
python main.py --export data/relevant.csv --export-relevant
```

### View Statistics

```bash
python main.py --stats
```

### Dashboard

```bash
python dashboard.py
# Access at http://localhost:8051
```

## Project Structure

```
RedditOregon/
├── main.py           # CLI entry point
├── scraper.py        # Reddit data collection
├── detector.py       # Relevance detection algorithm
├── database.py       # PostgreSQL operations
├── dashboard.py      # Dash visualization app
├── schema.sql        # Database schema
├── requirements.txt  # Python dependencies
└── .env.template     # Environment configuration template
```

## Target Subreddits

**Primary:**
- r/psychedelics, r/Psychonaut, r/PsilocybinMushrooms
- r/oregon, r/Colorado
- r/TherapeuticKetamine, r/ketamine, r/mdmatherapy
- r/Ayahuasca, r/microdosing, r/HPPD

**Secondary:**
- r/Portland, r/askportland
- r/depression, r/PTSD, r/mentalhealth
- r/Drugs, r/AustralianPsychedelics

## Relevance Criteria

Posts are included if they:
1. Explicitly mention Oregon or Colorado in a psilocybin therapy context
2. Discuss psilocybin/mushrooms specifically (not other substances)
3. Contain first-person experience reports
4. Include therapeutic context indicators

Posts are excluded if they are:
- News articles or policy discussions
- Cultivation or growing guides
- Sourcing requests
- Business advertisements
- Facilitator perspectives (rather than patient experiences)

## Research Context

This tool was developed to support academic research on real-world psilocybin therapy outcomes. The research aims to:

1. Characterize reported outcomes of legal psilocybin therapy
2. Identify treatment-level factors associated with outcomes
3. Describe the population seeking legal psilocybin services

## Author

Cooper Tretter
The New School for Social Research

## License

This project is for academic research purposes.
