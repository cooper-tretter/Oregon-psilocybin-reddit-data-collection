"""
Relevance detection for psychedelic therapy experience posts.
Focuses on identifying first-person Oregon psilocybin trip/session reports.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DetectionResult:
    """Result of relevance detection on a post."""
    relevance_score: float = 0.0
    is_relevant: bool = False
    is_trip_report: bool = False  # New: specifically a trip/session report
    category: Optional[str] = None
    location: Optional[str] = None
    substance: Optional[str] = None
    treatment_setting: Optional[str] = None
    clinical_indication: Optional[str] = None
    outcome_sentiment: Optional[str] = None
    mentions_cost: bool = False
    mentions_facilitator: bool = False
    mentions_integration: bool = False
    mentions_preparation: bool = False
    is_legal_context: bool = False
    detected_keywords: dict = field(default_factory=dict)
    external_links: list = field(default_factory=list)
    exclusion_reason: Optional[str] = None


# TRIP REPORT indicators - HIGHEST priority
# These indicate someone is describing their actual experience
TRIP_REPORT_INDICATORS = {
    'weight': 0.25,
    'terms': [
        # First-person experience language
        'i took', 'i experienced', 'i felt', 'i saw', 'i realized',
        'during my trip', 'during my session', 'during the session',
        'my journey', 'the journey began', 'journey started',
        'came up for me', 'came to me', 'showed me',
        'i was shown', 'i understood', 'i learned',
        'the medicine', 'the mushrooms', 'the psilocybin',
        'peak of', 'coming down', 'afterglow',
        'wore off', 'started to feel', 'began to feel',
        'i cried', 'i laughed', 'i let go',
        'visuals', 'closed eye', 'open eye',
        'body sensations', 'waves of', 'energy',
        'surrendered', 'ego dissolution', 'ego death',
        'one with', 'connected to', 'unity',
        'profound', 'intense', 'beautiful', 'terrifying',
        'hours later', 'next day', 'days after',
        'my first session', 'my second session', 'my third',
        'session report', 'trip report', 'experience report',
        'here is my experience', 'wanted to share my experience',
        'writing this', 'reflecting on', 'processing',
    ]
}

# Oregon psilocybin specific terms - HIGH priority
OREGON_PSILOCYBIN_TERMS = {
    'weight': 0.20,
    'terms': [
        'oregon psilocybin', 'oregon service center', 'oregon facilitator',
        'measure 109', 'oha', 'oregon health authority',
        'psilocybin services act', 'licensed facilitator',
        'service center in oregon', 'session in oregon',
        'portland psilocybin', 'eugene psilocybin', 'bend psilocybin',
        'beaverton', 'salem psilocybin', 'oregon program',
        'legal psilocybin session', 'legal mushroom session',
        'fractal soul', 'innertrek', 'epic healing',  # Known Oregon centers
        'oregon coast', 'willamette',
    ]
}

# Treatment/therapy context
RELEVANCE_KEYWORDS = {
    'treatment_settings': {
        'weight': 0.12,
        'terms': [
            'psilocybin therapy', 'psychedelic therapy', 'facilitated session',
            'guided session', 'therapy session', 'therapeutic session',
            'service center', 'therapy center', 'healing center',
            'ketamine clinic', 'ketamine therapy', 'ketamine infusion',
            'mdma therapy', 'mdma-assisted', 'clinical trial',
            'retreat center', 'ceremony',
        ]
    },
    'experience_descriptors': {
        'weight': 0.10,
        'terms': [
            'my session', 'my experience', 'just completed', 'just finished',
            'had my first', 'went to', 'visited', 'session went',
            'dose was', 'dosage', 'grams', 'my therapist',
            'my facilitator', 'my guide', 'sitter',
            'preparation session', 'integration session',
        ]
    },
    'therapeutic_context': {
        'weight': 0.08,
        'terms': [
            'therapeutic', 'healing', 'medicine', 'medicinal',
            'set and setting', 'intention', 'breakthrough',
            'mystical experience', 'integration work', 'processing',
        ]
    },
    'legal_indicators': {
        'weight': 0.08,
        'terms': [
            'legal', 'licensed', 'regulated', 'approved', 'certified',
            'legitimate', 'state program',
        ]
    }
}

# Location patterns - prioritize Oregon
LOCATIONS = {
    'oregon': ['oregon', 'portland', 'eugene', 'bend', 'beaverton', 'salem', 'measure 109', 'oha', 'willamette'],
    'colorado': ['colorado', 'denver', 'boulder', 'proposition 122', 'natural medicine'],
    'australia': ['australia', 'australian', 'melbourne', 'sydney', 'tga'],
    'canada': ['canada', 'canadian', 'vancouver', 'toronto'],
    'jamaica': ['jamaica', 'jamaican'],
    'netherlands': ['netherlands', 'dutch', 'amsterdam', 'truffle'],
    'costa_rica': ['costa rica'],
    'mexico': ['mexico', 'mexican'],
    'peru': ['peru', 'peruvian']
}

# Substance patterns - prioritize psilocybin
SUBSTANCES = {
    'psilocybin': ['psilocybin', 'mushroom', 'shroom', 'magic mushroom', 'psilo', 'cubes', 'cubensis'],
    'ketamine': ['ketamine', 'ket', 'k therapy', 'infusion', 'troches', 'spravato'],
    'mdma': ['mdma', 'molly', 'ecstasy', 'mdma-assisted'],
    'lsd': ['lsd', 'acid', 'lysergic'],
    'ayahuasca': ['ayahuasca', 'aya', 'dmt', 'huasca'],
    'ibogaine': ['ibogaine', 'iboga'],
    '5-meo-dmt': ['5-meo', '5meo', 'bufo', 'toad']
}

# Treatment settings
TREATMENT_SETTINGS = {
    'service_center': ['service center', 'psilocybin service', 'measure 109', 'oregon program', 'licensed center'],
    'clinical_trial': ['clinical trial', 'research study', 'maps', 'fda', 'phase 2', 'phase 3'],
    'ketamine_clinic': ['ketamine clinic', 'infusion center', 'iv ketamine', 'spravato'],
    'retreat': ['retreat', 'retreat center', 'ceremony', 'ceremonial'],
    'therapeutic': ['therapist', 'psychiatrist', 'psychologist', 'therapy office'],
    'underground': ['underground', 'gray market']
}

# Clinical indications
CLINICAL_INDICATIONS = {
    'depression': ['depression', 'depressed', 'mdd', 'treatment-resistant', 'trd', 'suicidal'],
    'ptsd': ['ptsd', 'trauma', 'traumatic', 'cptsd', 'post-traumatic'],
    'anxiety': ['anxiety', 'anxious', 'gad', 'panic', 'social anxiety', 'ocd'],
    'addiction': ['addiction', 'addict', 'substance use', 'alcoholism', 'opioid'],
    'end_of_life': ['end of life', 'terminal', 'cancer', 'dying', 'death anxiety'],
    'eating_disorder': ['eating disorder', 'anorexia', 'bulimia', 'binge'],
    'chronic_pain': ['chronic pain', 'fibromyalgia', 'pain management']
}

# EXCLUDED SUBREDDITS - never relevant regardless of content
EXCLUDED_SUBREDDITS = {
    # Fiction/creative writing
    'hfy', 'writingprompts', 'nosleep', 'shortscarystories', 'creepypasta',
    # Personal ads/dating
    'dirtyr4r', 'r4r', 'femdompersonals', 'randomactsofblowjob', 'randomactsofmuffdive',
    # Gaming/entertainment
    'u_proletlariet', 'whowouldwin', 'respectthreads', 'characterrant',
    # Investment/stocks (we want experiences, not stock analysis)
    'shroomstocks', 'wallstreetbets', 'stocks', 'investing',
    'numinusinvestorsclub', 'psychedelicinvesting',
    # News aggregators (we want first-person experiences)
    'breakingbadforum', 'news', 'worldnews', 'politics',
    # Cultivation subreddits - we want trip reports, not growing guides
    'unclebens', 'mushroomgrowers', 'shroomery', 'mushroomgrowcanada',
    'magicmushroomsbayarea', 'magicmushroomusa', 'sporetraders', 'sporeswap',
    # Relocation/moving subreddits
    'samegrassbutgreener', 'iwantout', 'expats',
    # General subreddits (too broad, rarely have specific trip reports)
    'conspiracy', 'drugs', 'popcornpundits', 'nutraceuticalscience',
    # More personals subreddits
    'rolereversedpersonals', 'momforaminute', 'dadforaminute',
    'hypnohookup', 'hypnopersonals', 'gentlefemdomr4r', 'femdomcommunity',
    # More investment/stocks
    '10xpennystocks', 'pennystocks', 'weedstocks',
    # News/futurism/aggregators
    'futurology', 'technology', 'science', 'pbsauto', 'gulfcity',
    'newsfromthecrypt', 'autotldr',
    # Travel
    'travelagents', 'travel', 'solotravel',
    # Other state subreddits (not Oregon/Colorado)
    'newmexico', 'arizona', 'california', 'nevada', 'utah', 'washington',
    'texas', 'florida', 'newyork', 'massachusetts',
    # Founder/startup subreddits (business posts, not experiences)
    'femalefounders', 'entrepreneur',
    # State cannabis subreddits (news posts, not experiences)
    'newjerseyents', 'bostontrees', 'chicagotrees', 'oilpen', 'trees',
    # Other therapy/medical subreddits (not psilocybin-focused)
    'ketamine', 'therapeuticketamine', 'tmstherapy', 'rtms', 'fibromyalgia',
    'chronicpain', 'depression', 'anxiety', 'ptsd', 'mentalhealth',
    # More personals
    'dirtyr4r30plus', 'dirtyr4rco', 'colorador4r',
    # Investment subreddits
    'angelinvestors', 'venturecapital', 'startups',
    # Cannabis subreddits (off-topic)
    'medicalcannabis_ni', 'uktrees', 'canadients',
    # City subreddits not Oregon/Colorado (just passing mentions)
    'neworleans', 'sanfrancisco', 'losangeles', 'seattle', 'nyc', 'austin',
    'chicago', 'boston', 'miami', 'phoenix', 'atlanta',
    # Politics/debate (we want experiences, not debates)
    'askpolitics', 'politicaldiscussion', 'changemyview', 'unpopularopinion',
    # Mental health research recruiting subreddits
    'schizophrenia', 'paranoidschizophrenia', 'antipsychiatry',
}

# EXCLUSION patterns - things we DON'T want
EXCLUSION_PATTERNS = {
    'news_article': {
        'weight': -0.35,
        'terms': [
            'according to this article', 'according to the article',
            'news:', 'breaking:', 'study shows', 'research shows',
            'scientists found', 'researchers found',
            'the article states', 'the study found',
            'published in', 'peer-reviewed',
            'oregonians have', 'clients have', 'over 700',  # statistics language
            'the state has', 'the program has', 'milestone',
            '#drugnews', 'drug news',
        ]
    },
    'policy_discussion': {
        'weight': -0.20,
        'terms': [
            'should be legal', 'should legalize', 'legalization effort',
            'ballot measure', 'vote for', 'vote against',
            'the bill', 'lawmakers', 'legislation',
            'policy', 'regulation changes', 'decriminalize',
            'how to help legalize', 'help legalization',
        ]
    },
    'questions_requests': {
        'weight': -0.25,
        'terms': [
            'share your recommendations', 'any recommendations',
            'looking for recommendations', 'recommend a',
            'has anyone tried', 'does anyone know',
            'where can i find', 'looking for a facilitator',
            'kindly share', 'please share',
            'curious how', 'wondering if',
            'can anyone recommend', 'seeking recommendations',
        ]
    },
    'research_recruitment': {
        'weight': -0.40,
        'terms': [
            '[research study]', 'research study:', 'mod approved',
            'take this survey', 'fill out this survey', 'participate in',
            'recruiting participants', 'looking for participants',
            'phd research', 'dissertation research', 'academic study',
        ]
    },
    'advertisement_promo': {
        'weight': -0.50,
        'terms': [
            'we offer', 'our services', 'we provide', 'our center',
            'schedule today', 'book now', 'no waitlist', 'starting at $',
            'all-inclusive', 'we can accommodate', 'check out our',
            'visit our website', 'www.', '.com', 'contact us',
            'we are passionate', 'made affordability a priority',
            'discounts for veterans', 'first responders',
            'would love to hear', 'has anyone here tried',
            'open to both', 'out-of-state visitors',
            'served over', 'clients to date',
        ]
    },
    'business_intro': {
        'weight': -0.50,
        'terms': [
            'i co-founded', 'i founded', 'my company', 'our company',
            'i am the ceo', 'i am the founder', 'chief operating',
            'business owner', 'business update', 'new offerings',
            'vertically integrated', 'licensed manufacturer',
            'we are one of only', 'market impact',
            'purpose of this reddit', 'welcome to the community',
            'fellow business owners', 'open source model',
            'i personally have facilitated', 'we have seen close to',
        ]
    },
    'informational_guide': {
        'weight': -0.40,
        'terms': [
            'ultimate guide', 'complete guide', 'beginner guide',
            'what you need to know', 'here\'s what you need',
            'introduction to', 'overview of', 'considerations for use',
            'supporting research', 'recent studies', 'a 2022 study',
            'benefits reported by users include', 'potential benefits',
        ]
    },
    'facilitator_perspective': {
        'weight': -0.35,
        'terms': [
            'as a licensed facilitator', 'becoming a licensed facilitator',
            'i guide clients', 'guiding clients', 'facilitating clients',
            'as a facilitator', 'i have facilitated',
            'effective sitters', 'being a sitter', 'trip sitter',
            'traits could be effective', 'level of comfort with people',
        ]
    },
    'real_estate_business': {
        'weight': -0.50,
        'terms': [
            'looking for commercial', 'looking for industrial',
            'commercial space', 'industrial space', 'warehouse space',
            'real estate', 'lease', 'rent space', 'square feet',
            'manufacturing facility', 'been searching on craigslist',
        ]
    },
    'drug_identification': {
        'weight': -1.0,  # Instant disqualifier
        'terms': [
            'iding what i', 'identifying what', 'what did i take',
            'what i may have consumed', 'figure out if the',
            'sketchy connections', 'bought from strangers',
            'contain something else', 'laced with',
            'chocolate bar', 'mushroom bar', 'shroom bar',
            'bought through', 'typical sketchy',
        ]
    },
    'announcement_news': {
        'weight': -0.50,
        'terms': [
            'announces its launch', 'launches as', 'is now open',
            'grand opening', 'officially opens', 'first licensed',
            'issued license', 'receives license', 'approved by',
            'regulatory update', 'new regulations',
            'oha anticipates', 'oha hopes', 'service center openings',
            'anticipates service center', 'hopes to see',
        ]
    },
    'opinion_oped': {
        'weight': -0.50,
        'terms': [
            'opinion:', 'op-ed', 'commentary piece', 'sketchy framework',
            'portends', 'implementation disaster', 'forensic psychiatrist',
            'journal of the american academy', 'oregonlive.com',
            'i recently published', 'i wrote about',
        ]
    },
    'legislative_policy': {
        'weight': -0.45,
        'terms': [
            'amending', 'legislators', 'sponsor bills', 'criminal penalties',
            'legislative proposal', 'house bill', 'senate bill',
            'overturn measure', 'new restrictions', 'advocates for',
            'coloradans are concerned', 'proposition 122',
        ]
    },
    'food_restaurant': {
        'weight': -0.50,
        'terms': [
            'best place for good eats', 'good snackos', 'good food',
            'restaurant', 'where to eat', 'food recommendations',
            'weirdo bars', 'eclectic, weird', 'curio/oddities',
            'not going to make me go broke', 'vibes in mind',
        ]
    },
    'sitter_advice': {
        'weight': -0.50,
        'terms': [
            'effective sitters', 'most people who have these traits',
            'could be effective sitters', 'compassionate, place strong',
            'level of comfort with people', 'intense emotional distress',
            'without necessarily trying to', 'let them feel',
        ]
    },
    'investment_stock': {
        'weight': -0.40,
        'terms': [
            'stock', 'invest', 'thesis', 'bull case', 'bear case',
            'share price', 'market cap', 'ticker', 'trading',
            'shareholders', 'portfolio', 'dividend',
        ]
    },
    'fiction_roleplay': {
        'weight': -0.50,
        'terms': [
            'the galaxy', 'star systems', 'intergalactic',
            'villain', 'hero', 'gwahahaha', 'mario', 'bowser',
            'once upon a time', 'in a world where',
            'doctor [your', 'hello, doctor',
            'take me on as a patient',  # hypnotherapy personals
        ]
    },
    'cultivation': {
        'weight': -1.0,  # Instant disqualifier
        'terms': [
            'grow kit', 'growing your own', 'grow your own', 'spore', 'substrate',
            'fruiting', 'colonization', 'mycelium', 'monotub', 'bulk substrate',
            'flush', 'tek', 'agar', 'grain spawn', 'grain bag',
            'inoculate', 'colonize', 'pinning', 'canopy', 'fruiting chamber',
            'how to grow', 'guide to growing', 'practical guide',
        ]
    },
    'sourcing': {
        'weight': -1.0,  # Instant disqualifier
        'terms': [
            'dealer', 'plug', 'connect', 'scored', 'copped',
            'where can i buy', 'where to buy', 'how to get',
            'where to get', 'where do i get', 'how do i get',
            'black market', 'dark web', 'dnm',
            'dm me', 'message me', 'wickr', 'telegram',
            'for sale', 'selling', 'vendor', 'shop',
        ]
    },
    'recreational_only': {
        'weight': -0.15,
        'terms': [
            'party', 'festival', 'rave', 'just for fun',
            'getting high', 'stoned', 'baked',
            'candy flip', 'hippie flip',
        ]
    },
}

# URL pattern
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    return URL_PATTERN.findall(text)


def detect_location(text: str) -> Optional[str]:
    """Detect geographic location mentioned in text. Prioritizes Oregon."""
    text_lower = text.lower()
    # Check Oregon first (priority)
    for pattern in LOCATIONS['oregon']:
        if pattern in text_lower:
            return 'oregon'
    # Then check others
    for location, patterns in LOCATIONS.items():
        if location == 'oregon':
            continue
        for pattern in patterns:
            if pattern in text_lower:
                return location
    return None


def is_location_in_psilocybin_context(text: str, location: str) -> bool:
    """
    Check if the location is mentioned in context of psilocybin/therapy.
    Returns True if location appears near psilocybin-related terms.
    """
    if not location:
        return False

    text_lower = text.lower()

    # Get location patterns
    if location == 'oregon':
        loc_patterns = LOCATIONS['oregon']
    elif location == 'colorado':
        loc_patterns = LOCATIONS['colorado']
    else:
        return True  # For other locations, don't apply this filter

    # Context words that should appear near the location
    context_words = [
        'psilocybin', 'mushroom', 'shroom', 'therapy', 'session', 'facilitator',
        'service center', 'measure 109', 'proposition 122', 'natural medicine',
        'trip', 'journey', 'experience', 'healing', 'psychedelic'
    ]

    # Check if any location pattern appears within 200 chars of context words
    for loc_pattern in loc_patterns:
        loc_pos = text_lower.find(loc_pattern)
        if loc_pos == -1:
            continue

        # Get surrounding text (200 chars before and after)
        start = max(0, loc_pos - 200)
        end = min(len(text_lower), loc_pos + len(loc_pattern) + 200)
        surrounding = text_lower[start:end]

        # Check if any context word is in the surrounding text
        for ctx_word in context_words:
            if ctx_word in surrounding:
                return True

    return False


def detect_substance(text: str) -> Optional[str]:
    """Detect substance mentioned in text. Prioritizes psilocybin."""
    text_lower = text.lower()
    # Check psilocybin first (priority)
    for pattern in SUBSTANCES['psilocybin']:
        if pattern in text_lower:
            return 'psilocybin'
    # Then check others
    for substance, patterns in SUBSTANCES.items():
        if substance == 'psilocybin':
            continue
        for pattern in patterns:
            if pattern in text_lower:
                return substance
    return None


def detect_treatment_setting(text: str) -> Optional[str]:
    """Detect treatment setting mentioned in text."""
    text_lower = text.lower()
    for setting, patterns in TREATMENT_SETTINGS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return setting
    return None


def detect_clinical_indication(text: str) -> Optional[str]:
    """Detect clinical indication mentioned in text."""
    text_lower = text.lower()
    for indication, patterns in CLINICAL_INDICATIONS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return indication
    return None


def detect_outcome_sentiment(text: str) -> Optional[str]:
    """Sentiment detection for outcomes."""
    text_lower = text.lower()

    positive_terms = [
        'helped', 'healing', 'healed', 'better', 'improved', 'life-changing',
        'transformative', 'breakthrough', 'grateful', 'amazing', 'wonderful',
        'incredible', 'best decision', 'recommend', 'worth it', 'cured',
        'remission', 'resolved', 'finally free', 'changed my life',
        'profound', 'beautiful', 'peaceful', 'clarity', 'insight',
        'love', 'connected', 'unity', 'one with',
    ]

    negative_terms = [
        'worse', 'bad experience', 'traumatic', 'scary', 'terrifying',
        'horrible', 'awful', 'regret', 'warning', 'be careful', 'dont do',
        "don't do", 'waste of money', 'scam', 'didn\'t help', 'no effect',
        'made things worse', 'damaged', 'harmed', 'nightmare', 'hell',
    ]

    positive_count = sum(1 for term in positive_terms if term in text_lower)
    negative_count = sum(1 for term in negative_terms if term in text_lower)

    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    elif positive_count > 0 and negative_count > 0:
        return 'mixed'
    return 'neutral'


def is_trip_report(text: str, title: str = '') -> tuple[bool, list[str]]:
    """
    Determine if this is a first-person trip/session report.
    Returns (is_report, matched_terms).
    """
    combined = f"{title} {text}".lower()
    matches = []

    for term in TRIP_REPORT_INDICATORS['terms']:
        if term in combined:
            matches.append(term)

    # Need at least 2 trip report indicators to qualify
    return len(matches) >= 2, matches


def detect_relevance(text: str, title: str = '', subreddit: str = '') -> DetectionResult:
    """
    Detect if a post is relevant to psychedelic therapy experiences.
    Prioritizes Oregon/Colorado psilocybin trip reports.
    Returns a DetectionResult with extracted variables.
    """
    result = DetectionResult()
    combined_text = f"{title} {text}".lower()
    content_length = len(text)
    subreddit_lower = subreddit.lower() if subreddit else ''

    # EARLY EXIT: Check if subreddit is excluded
    if subreddit_lower in EXCLUDED_SUBREDDITS:
        result.exclusion_reason = f'excluded_subreddit_{subreddit_lower}'
        result.is_relevant = False
        return result

    # Extract URLs
    result.external_links = extract_urls(text)

    # Check if it's a trip report FIRST (highest priority)
    is_report, report_matches = is_trip_report(text, title)
    result.is_trip_report = is_report
    if is_report:
        result.detected_keywords['trip_report'] = report_matches
        result.relevance_score += TRIP_REPORT_INDICATORS['weight'] * min(len(report_matches), 4)

    # Check for Oregon psilocybin specific terms
    oregon_matches = []
    for term in OREGON_PSILOCYBIN_TERMS['terms']:
        if term in combined_text:
            oregon_matches.append(term)
    if oregon_matches:
        result.detected_keywords['oregon_psilocybin'] = oregon_matches
        result.relevance_score += OREGON_PSILOCYBIN_TERMS['weight'] * min(len(oregon_matches), 3)

    # Check exclusion patterns
    for category, data in EXCLUSION_PATTERNS.items():
        if category == 'short_response':
            continue  # Handle separately
        matches = []
        for term in data['terms']:
            if term in combined_text:
                matches.append(term)
        if matches:
            result.detected_keywords[f'exclusion_{category}'] = matches
            result.relevance_score += data['weight']

            # If strongly excluded, mark and potentially return early
            if data['weight'] <= -0.25 and len(matches) >= 2:
                result.exclusion_reason = category
                # Don't return early if it's also a trip report
                if not is_report:
                    result.is_relevant = False
                    return result

    # Penalize very short content (likely just a reply/comment, not a report)
    if content_length < 200:
        result.relevance_score -= 0.10
    elif content_length < 100:
        result.relevance_score -= 0.20

    # Bonus for longer content (trip reports are usually detailed)
    if content_length > 1000:
        result.relevance_score += 0.10
    elif content_length > 500:
        result.relevance_score += 0.05

    # Check relevance patterns
    for category, data in RELEVANCE_KEYWORDS.items():
        matches = []
        for term in data['terms']:
            if term in combined_text:
                matches.append(term)
        if matches:
            result.detected_keywords[category] = matches
            result.relevance_score += data['weight'] * min(len(matches), 3)

    # Extract content variables
    result.location = detect_location(combined_text)
    result.substance = detect_substance(combined_text)
    result.treatment_setting = detect_treatment_setting(combined_text)
    result.clinical_indication = detect_clinical_indication(combined_text)
    result.outcome_sentiment = detect_outcome_sentiment(combined_text)

    # Check for specific mentions
    result.mentions_cost = any(term in combined_text for term in ['cost', 'price', 'paid', 'expensive', 'affordable', 'insurance', '$'])
    result.mentions_facilitator = any(term in combined_text for term in ['facilitator', 'guide', 'sitter', 'therapist', 'practitioner'])
    result.mentions_integration = 'integration' in combined_text
    result.mentions_preparation = any(term in combined_text for term in ['preparation', 'prep session', 'preparing', 'beforehand'])
    result.is_legal_context = any(term in combined_text for term in ['legal', 'licensed', 'regulated', 'measure 109', 'approved', 'service center'])

    # MAJOR BONUS: Oregon + Psilocybin + Trip Report = exactly what we want
    if result.location == 'oregon' and result.substance == 'psilocybin':
        result.relevance_score += 0.15
        if result.is_trip_report:
            result.relevance_score += 0.20  # Big bonus for the trifecta

    # Bonus for psilocybin (main focus)
    if result.substance == 'psilocybin':
        result.relevance_score += 0.05

    # Bonus for service center setting
    if result.treatment_setting == 'service_center':
        result.relevance_score += 0.10

    # Bonus for legal context
    if result.is_legal_context:
        result.relevance_score += 0.05

    # Clamp score between 0 and 1
    result.relevance_score = max(0.0, min(1.0, result.relevance_score))

    # STRICT REQUIREMENTS: Must be Oregon/Colorado AND psilocybin
    is_target_location = result.location in ('oregon', 'colorado')
    is_psilocybin = result.substance == 'psilocybin'

    # Determine if relevant - MUST meet location and substance requirements
    if not is_target_location or not is_psilocybin:
        result.is_relevant = False
        result.category = None
        return result

    # CONTEXTUAL CHECK: Location must be mentioned near psilocybin context
    # This prevents false positives from posts that just mention Oregon/Colorado in passing
    if not is_location_in_psilocybin_context(combined_text, result.location):
        result.is_relevant = False
        result.category = None
        result.exclusion_reason = 'location_not_in_context'
        return result

    # If location and substance match AND are in context, apply score thresholds
    if result.is_trip_report:
        result.is_relevant = result.relevance_score >= 0.25  # Slightly higher threshold
    else:
        result.is_relevant = result.relevance_score >= 0.35  # Higher threshold for non-trip-reports

    # Categorize the post
    if result.is_relevant:
        if result.is_trip_report:
            result.category = 'trip_report'
        elif 'experience_descriptors' in result.detected_keywords:
            result.category = 'experience_report'
        elif result.outcome_sentiment in ['positive', 'negative']:
            result.category = 'outcome_report'
        else:
            result.category = 'discussion'

    return result


def categorize_post(text: str, title: str = '') -> str:
    """
    Categorize a post based on its content.
    Returns one of: trip_report, experience_report, question, discussion, resource, other
    """
    combined = f"{title} {text}".lower()

    # Trip report indicators (first-person detailed experience)
    is_report, _ = is_trip_report(text, title)
    if is_report:
        return 'trip_report'

    # Experience report indicators
    experience_indicators = [
        'my experience', 'my session', 'i went', 'i had', 'i tried',
        'experience report', 'just finished', 'completed my'
    ]
    if any(ind in combined for ind in experience_indicators):
        return 'experience_report'

    # Question indicators
    question_indicators = ['?', 'has anyone', 'does anyone', 'should i', 'advice', 'recommendations']
    if any(ind in combined for ind in question_indicators):
        return 'question'

    # Resource/information
    resource_indicators = ['guide', 'resource', 'list of', 'information about', 'research shows']
    if any(ind in combined for ind in resource_indicators):
        return 'resource'

    return 'discussion'


if __name__ == '__main__':
    # Test detection with examples
    test_texts = [
        # Should be HIGH relevance (Oregon psilocybin trip report)
        ("I took the second dose... 10g Mushroom Tea Guided Therapy Session in Oregon",
         "Just completed my first session at a licensed service center in Oregon. The facilitator was amazing. During my trip, I felt waves of emotion and saw beautiful patterns. The psilocybin showed me things about myself I had been hiding. I cried, I laughed, I let go. This was life-changing for my depression."),

        # Should be HIGH relevance (Oregon psilocybin experience)
        ("My Oregon psilocybin experience",
         "I went to Fractal Soul in Beaverton for my session. The preparation session helped set my intention. During the journey, I experienced profound ego dissolution and felt connected to everything. The integration work after helped me process what came up."),

        # Should be MEDIUM relevance (psilocybin experience, not Oregon)
        ("First mushroom therapy session",
         "Had my first facilitated psilocybin session yesterday. The medicine showed me so much. I felt waves of energy and saw beautiful visuals. Still processing everything."),

        # Should be LOW relevance (news/policy discussion)
        ("Oregon's psilocybin industry, a year old, seeks customers",
         "According to this article, a year in, Oregon's experiment with regulated psilocybin is short on customers. I supported this ballot measure but the costs are too high."),

        # Should be EXCLUDED (cultivation)
        ("My monotub is finally fruiting!",
         "First flush coming in nicely. The mycelium colonized the substrate perfectly. Expecting a good harvest."),

        # Should be EXCLUDED (sourcing)
        ("Anyone know where I can get shrooms?",
         "Looking for a connect in the Portland area. DM me if you know someone."),
    ]

    for title, text in test_texts:
        result = detect_relevance(text, title)
        print(f"\n{'='*60}")
        print(f"Title: {title[:60]}...")
        print(f"Is Trip Report: {result.is_trip_report}")
        print(f"Relevant: {result.is_relevant} (score: {result.relevance_score:.2f})")
        print(f"Category: {result.category}")
        print(f"Location: {result.location}, Substance: {result.substance}")
        print(f"Setting: {result.treatment_setting}")
        if result.exclusion_reason:
            print(f"Excluded: {result.exclusion_reason}")
        print(f"Keywords: {list(result.detected_keywords.keys())}")
