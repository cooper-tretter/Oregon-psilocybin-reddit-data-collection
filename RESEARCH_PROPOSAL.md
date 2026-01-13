# Research Proposal: Real-World Psilocybin Therapy Experiences on Reddit

## Background

With the implementation of Oregon's Measure 109 (2023) and Colorado's Natural Medicine Health Act (2022), legal psilocybin-assisted therapy is now available in real-world settings outside of clinical trials. These programs represent a significant shift from controlled research environments to community-based service delivery, creating both opportunities and uncertainties about optimal implementation.

Reddit and similar online platforms have become important venues where individuals share detailed first-person accounts of their therapeutic experiences. These naturalistic reports offer a unique window into patient experiences that complement clinical trial data, capturing perspectives on:
- Subjective acute experiences during sessions
- Perceived short and long-term outcomes
- Quality of service delivery and facilitator interactions
- Preparation and integration processes
- Challenges and adverse experiences

This study aims to systematically collect and analyze these first-person reports to inform policy, guide service center best practices, and identify factors associated with positive and negative outcomes.

## Study Aims

### Primary Aims
1. **Characterize reported outcomes** of legal psilocybin therapy in Oregon and Colorado, including both positive outcomes (symptom improvement, personal insights, wellbeing) and negative outcomes (adverse experiences, lack of benefit, harms)
2. **Identify treatment-level factors** associated with outcomes, including service center characteristics, facilitator interactions, dosing protocols, and preparation/integration practices
3. **Describe the population** seeking legal psilocybin services, including clinical indications (depression, anxiety, PTSD, addiction, existential distress, personal growth) and demographic patterns

### Secondary Aims
4. Examine acute session experiences and their relationship to reported outcomes
5. Identify commonly reported challenges, concerns, and areas for improvement in service delivery
6. Compare experiences across different states/jurisdictions as legal access expands

## Methods

### Data Collection

**Platform:** Reddit (via Reddit API and PullPush historical archive)

**Target Subreddits:**
- State/city subreddits: r/oregon, r/Portland, r/askPortland, r/Eugene, r/Bend, r/colorado, r/Denver, r/boulder
- Psychedelic-focused: r/Psychonaut, r/Psychedelics, r/psilocybin, r/PsilocybinMushrooms, r/shrooms, r/RationalPsychonaut
- Therapy-focused: r/psychedelictherapy, r/TherapeuticPsychedelics

**Search Strategy:** Keyword searches combining location terms (Oregon, Colorado, Portland, Denver, etc.) with psilocybin-related terms (psilocybin, mushroom, session, therapy, facilitator, service center, Measure 109, etc.)

### Inclusion Criteria

Posts are included if they meet ALL of the following:

1. **Location Requirement:** Explicitly mentions Oregon OR Colorado in the context of psilocybin therapy/services
   - Location must appear within 200 characters of psilocybin-related terms (contextual relevance check)
   - Includes references to specific cities (Portland, Eugene, Bend, Denver, Boulder)
   - Includes references to state programs (Measure 109, Oregon Health Authority, natural medicine act)

2. **Substance Requirement:** Specifically discusses psilocybin/psilocybin mushrooms
   - NOT ketamine, MDMA, LSD, ayahuasca, or other substances
   - Terms: psilocybin, mushroom, shroom (in therapeutic context)

3. **Content Type:** First-person experience reports describing actual therapy/session experiences
   - Trip reports and session summaries
   - Personal narratives of therapeutic experiences
   - Reflections on outcomes and effects
   - Detailed descriptions of the service experience

4. **Relevance Indicators (weighted scoring):**
   - First-person language: "I took," "my session," "I experienced," "my journey"
   - Oregon-specific terms: "Oregon service center," "licensed facilitator," "Measure 109"
   - Experience descriptors: "during the session," "the medicine," "integration"
   - Therapeutic context: "my therapist," "preparation session," "guided session"

### Exclusion Criteria

Posts are excluded if they match ANY of the following:

**Subreddit-Level Exclusions (~100 subreddits):**
- Fiction/creative writing: r/nosleep, r/WritingPrompts, r/shortscarystories
- Investment/stocks: r/shroomstocks, r/wallstreetbets, r/psychedelicinvesting
- Cultivation: r/unclebens, r/mushroomgrowers, r/sporetraders
- Other therapies: r/ketamine, r/therapeuticketamine, r/tmstherapy
- Non-target states: r/massachusetts, r/california, r/newmexico, etc.
- Personal ads/dating: r/r4r, r/dirtyr4r
- Business/startups: r/femalefounders, r/entrepreneur, r/startups

**Content-Level Exclusions (pattern matching):**

| Category | Examples | Rationale |
|----------|----------|-----------|
| News/Articles | "according to," "reported that," "study shows" | Third-party reporting, not personal experience |
| Policy Discussion | "should be legal," "legislation," "vote on" | Opinion/debate, not experience |
| Cultivation | "fruiting," "colonization," "spore," "substrate" | Growing guides, not therapy |
| Sourcing | "where to get," "where can i buy," "dealer" | Seeking substances, not therapy reports |
| Questions/Requests | "has anyone tried," "looking for recommendations" | Seeking info, not sharing experience |
| Research Recruitment | "participants needed," "taking part in study" | Recruitment posts |
| Advertisements | "we offer," "our services," "schedule today" | Commercial promotion |
| Business Introductions | "I co-founded," "my company," "vertically integrated" | Business announcements |
| Informational Guides | "here's what to know," "complete guide" | Educational content, not personal experience |
| Facilitator Perspective | "as a licensed facilitator," "I guide clients" | Provider perspective, not patient experience |
| Drug Identification | "what did I take," "chocolate bar," "mushroom bar" | Unknown substance questions |
| Opinion/Op-Ed | "in my opinion," "I believe that," "we should" | Commentary without personal experience |
| Legislative Updates | "bill passed," "governor signed," "OHA announced" | News about policy |

**Instant Disqualifiers (weight = -1.0):**
- Cultivation-related content
- Sourcing requests
- Drug identification questions

### Data Processing

1. **Automated Collection:** Python scripts using Reddit API (PRAW) and PullPush API for historical data
2. **Relevance Scoring:** Weighted keyword matching algorithm with inclusion/exclusion patterns
3. **Location Verification:** Contextual check ensuring location mentions relate to psilocybin context
4. **Manual Review:** Human verification of borderline cases and quality check of automated classifications

### Planned Analyses

**Qualitative Analysis:**
- Thematic analysis of experience narratives
- Coding for outcome types (positive/negative), acute experiences, service quality factors
- Identification of common themes and patterns

**Quantitative Analysis:**
- Descriptive statistics on post characteristics, locations, clinical indications
- Sentiment analysis of outcome descriptions
- Comparison across jurisdictions, service centers (where identifiable), time periods

## Preliminary Data Summary

**Current Dataset (as of January 2026):**
- Total posts collected: 1,678
- Posts meeting relevance criteria: 77
  - Oregon-related: 73 (95%)
  - Colorado-related: 4 (5%)
- Posts classified as trip/session reports: 510 (before location filtering)

**Data Quality Notes:**
- Strict filtering prioritizes precision over recall
- Oregon significantly over-represented (program launched earlier, more established)
- Colorado data limited (newer program, different regulatory structure)

## Ethical Considerations

- All data is publicly posted on Reddit
- No personally identifiable information collected beyond public usernames
- Analysis focuses on aggregate patterns, not individual identification
- IRB exemption to be sought (precedent: social media research on public posts)
- Will consult with Lukas Cannon regarding his prior IRB submissions for similar work

## Timeline and Next Steps

1. Finalize data collection methodology and expand dataset
2. Submit IRB exemption application to TNS
3. Develop detailed coding scheme for qualitative analysis
4. Begin systematic analysis of experience reports
5. Prepare preliminary findings for discussion

## References

- Oregon Psilocybin Services Act (Measure 109)
- Colorado Natural Medicine Health Act (Proposition 122)
- [Additional academic references on psychedelic therapy outcomes, social media research methods to be added]

---

*Prepared by Cooper Tretter*
*The New School for Social Research*
*January 2026*
