"""
Relevance detection for psychedelic therapy experience posts.
Classifies posts based on content, extracts key variables, and filters irrelevant content.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DetectionResult:
    """Result of relevance detection on a post."""
    relevance_score: float = 0.0
    is_relevant: bool = False
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


# Relevance keywords with weights
RELEVANCE_KEYWORDS = {
    # Treatment settings (high relevance)
    'treatment_settings': {
        'weight': 0.15,
        'terms': [
            'psilocybin therapy', 'psychedelic therapy', 'facilitated session',
            'licensed facilitator', 'service center', 'therapy center',
            'oregon psilocybin', 'colorado psychedelic', 'australian psychiatrist',
            'legal psilocybin', 'legal psychedelic therapy', 'measure 109',
            'psilocybin service', 'healing center', 'retreat center',
            'ketamine clinic', 'ketamine therapy', 'ketamine infusion',
            'mdma therapy', 'mdma-assisted', 'clinical trial'
        ]
    },
    # Experience descriptors (medium relevance)
    'experience_descriptors': {
        'weight': 0.10,
        'terms': [
            'my session', 'my experience with', 'just completed', 'therapy session',
            'integration session', 'preparation session', 'had my first',
            'went to', 'visited', 'treatment went', 'session went',
            'dose was', 'dosage', 'mg', 'grams', 'my therapist',
            'my facilitator', 'guide', 'sitter'
        ]
    },
    # Therapeutic context (medium relevance)
    'therapeutic_context': {
        'weight': 0.08,
        'terms': [
            'therapeutic', 'treatment', 'healing', 'medicine', 'medicinal',
            'clinical', 'protocol', 'set and setting', 'intention',
            'breakthrough', 'ego death', 'mystical experience',
            'afterglow', 'integration work', 'processing'
        ]
    },
    # Legal/licensed indicators (high relevance)
    'legal_indicators': {
        'weight': 0.12,
        'terms': [
            'legal', 'licensed', 'regulated', 'approved', 'certified',
            'legitimate', 'above board', 'state program', 'oha',
            'oregon health authority', 'psilocybin services',
            'natural medicine', 'proposition 122', 'tga approved'
        ]
    }
}

# Location patterns
LOCATIONS = {
    'oregon': ['oregon', 'portland', 'eugene', 'bend', 'measure 109', 'oha'],
    'colorado': ['colorado', 'denver', 'boulder', 'proposition 122', 'natural medicine'],
    'australia': ['australia', 'australian', 'melbourne', 'sydney', 'tga', 'psychiatrist'],
    'canada': ['canada', 'canadian', 'vancouver', 'toronto'],
    'jamaica': ['jamaica', 'jamaican'],
    'netherlands': ['netherlands', 'dutch', 'amsterdam', 'truffle'],
    'costa_rica': ['costa rica'],
    'mexico': ['mexico', 'mexican'],
    'peru': ['peru', 'peruvian', 'ayahuasca']
}

# Substance patterns
SUBSTANCES = {
    'psilocybin': ['psilocybin', 'mushroom', 'shroom', 'magic mushroom', 'psilo'],
    'ketamine': ['ketamine', 'ket', 'k therapy', 'infusion', 'troches', 'spravato'],
    'mdma': ['mdma', 'molly', 'ecstasy', 'mdma-assisted'],
    'lsd': ['lsd', 'acid', 'lysergic'],
    'ayahuasca': ['ayahuasca', 'aya', 'dmt', 'huasca'],
    'ibogaine': ['ibogaine', 'iboga'],
    '5-meo-dmt': ['5-meo', '5meo', 'bufo', 'toad']
}

# Treatment settings
TREATMENT_SETTINGS = {
    'clinical_trial': ['clinical trial', 'research study', 'maps', 'fda', 'phase 2', 'phase 3'],
    'service_center': ['service center', 'psilocybin service', 'measure 109', 'oregon program'],
    'ketamine_clinic': ['ketamine clinic', 'infusion center', 'iv ketamine', 'spravato'],
    'retreat': ['retreat', 'retreat center', 'ceremony', 'ceremonial'],
    'therapeutic': ['therapist', 'psychiatrist', 'psychologist', 'therapy office'],
    'underground': ['underground', 'gray market', 'dealer', 'plug']
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

# Exclusion patterns
EXCLUSION_PATTERNS = {
    'recreational': {
        'weight': -0.20,
        'terms': [
            'tripping', 'trip report', 'recreational', 'party', 'festival',
            'rave', 'just for fun', 'getting high', 'stoned', 'baked',
            'heroic dose', 'lemon tek', 'candy flip'
        ]
    },
    'cultivation': {
        'weight': -0.25,
        'terms': [
            'growing', 'cultivation', 'grow kit', 'spore', 'substrate',
            'fruiting', 'colonization', 'mycelium', 'monotub', 'bulk',
            'harvest', 'flush', 'tek', 'agar', 'grain spawn'
        ]
    },
    'questions_only': {
        'weight': -0.10,
        'terms': [
            'has anyone', 'does anyone', 'should i', 'can i', 'is it safe',
            'thinking about', 'considering', 'looking for advice',
            'any recommendations', 'where can i find', 'how do i'
        ]
    },
    'underground': {
        'weight': -0.15,
        'terms': [
            'dealer', 'plug', 'connect', 'scored', 'copped',
            'illegal', 'black market', 'dark web', 'dnm'
        ]
    },
    'spam': {
        'weight': -0.30,
        'terms': [
            'dm me', 'message me', 'wickr', 'telegram', 'signal',
            'for sale', 'selling', 'vendor', 'shop', 'buy from'
        ]
    }
}

# URL pattern
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    return URL_PATTERN.findall(text)


def detect_location(text: str) -> Optional[str]:
    """Detect geographic location mentioned in text."""
    text_lower = text.lower()
    for location, patterns in LOCATIONS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return location
    return None


def detect_substance(text: str) -> Optional[str]:
    """Detect substance mentioned in text."""
    text_lower = text.lower()
    for substance, patterns in SUBSTANCES.items():
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
    """Simple sentiment detection for outcomes."""
    text_lower = text.lower()

    positive_terms = [
        'helped', 'healing', 'healed', 'better', 'improved', 'life-changing',
        'transformative', 'breakthrough', 'grateful', 'amazing', 'wonderful',
        'incredible', 'best decision', 'recommend', 'worth it', 'cured',
        'remission', 'resolved', 'finally free', 'changed my life'
    ]

    negative_terms = [
        'worse', 'bad experience', 'traumatic', 'scary', 'terrifying',
        'horrible', 'awful', 'regret', 'warning', 'be careful', 'dont do',
        "don't do", 'waste of money', 'scam', 'didn\'t help', 'no effect',
        'made things worse', 'damaged', 'harmed', 'nightmare'
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


def detect_relevance(text: str, title: str = '') -> DetectionResult:
    """
    Detect if a post is relevant to psychedelic therapy experiences.
    Returns a DetectionResult with extracted variables.
    """
    result = DetectionResult()
    combined_text = f"{title} {text}".lower()

    # Extract URLs
    result.external_links = extract_urls(text)

    # Check exclusion patterns first
    for category, data in EXCLUSION_PATTERNS.items():
        matches = []
        for term in data['terms']:
            if term in combined_text:
                matches.append(term)
        if matches:
            result.detected_keywords[f'exclusion_{category}'] = matches
            result.relevance_score += data['weight']

            # If strongly excluded, mark and return early
            if data['weight'] <= -0.20 and len(matches) >= 2:
                result.exclusion_reason = category
                result.is_relevant = False
                return result

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
    result.is_legal_context = any(term in combined_text for term in ['legal', 'licensed', 'regulated', 'measure 109', 'approved'])

    # Bonus for having location + substance + treatment setting (strong signal)
    if result.location and result.substance:
        result.relevance_score += 0.10
    if result.treatment_setting and result.treatment_setting != 'underground':
        result.relevance_score += 0.10
    if result.is_legal_context:
        result.relevance_score += 0.08

    # Clamp score between 0 and 1
    result.relevance_score = max(0.0, min(1.0, result.relevance_score))

    # Determine if relevant (threshold: 0.15)
    result.is_relevant = result.relevance_score >= 0.15

    # Categorize the post
    if result.is_relevant:
        if 'experience_descriptors' in result.detected_keywords:
            result.category = 'experience_report'
        elif 'questions_only' in result.detected_keywords.get('exclusion_questions_only', []):
            result.category = 'question'
        elif result.outcome_sentiment in ['positive', 'negative']:
            result.category = 'outcome_report'
        else:
            result.category = 'discussion'

    return result


def categorize_post(text: str, title: str = '') -> str:
    """
    Categorize a post based on its content.
    Returns one of: experience_report, question, discussion, resource, other
    """
    combined = f"{title} {text}".lower()

    # Experience report indicators
    experience_indicators = [
        'my experience', 'my session', 'i went', 'i had', 'i tried',
        'trip report', 'experience report', 'just finished', 'completed my'
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
    # Test detection
    test_texts = [
        "Just completed my first psilocybin session at a licensed service center in Oregon. The facilitator was amazing and the experience was life-changing for my depression.",
        "Anyone know where I can get shrooms? Looking for a connect.",
        "I'm thinking about trying ketamine therapy for my anxiety. Has anyone tried it?",
        "My monotub is finally fruiting! First flush coming in nicely.",
        "Had an incredible MDMA-assisted therapy session through a clinical trial. My PTSD symptoms have significantly improved."
    ]

    for text in test_texts:
        result = detect_relevance(text)
        print(f"\nText: {text[:80]}...")
        print(f"  Relevant: {result.is_relevant} (score: {result.relevance_score:.2f})")
        print(f"  Category: {result.category}")
        print(f"  Location: {result.location}, Substance: {result.substance}")
        print(f"  Setting: {result.treatment_setting}, Indication: {result.clinical_indication}")
        if result.exclusion_reason:
            print(f"  Excluded: {result.exclusion_reason}")
