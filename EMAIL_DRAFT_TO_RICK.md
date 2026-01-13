# Draft Email to Rick

---

**Subject:** Reddit Psilocybin Therapy Study - Initial Data Collection & Project Summary

---

Hi Rick,

Thank you again for suggesting this project direction. I've completed an initial exploratory data collection and wanted to share a summary of the project methodology and preliminary findings.

## Project Overview

I've built a data collection pipeline to systematically gather first-person accounts of psilocybin therapy experiences from Reddit, focusing on Oregon and Colorado where legal services are now available. The goal is to characterize reported outcomes, identify factors associated with positive/negative experiences, and inform service center best practices.

**Repository:** https://github.com/cooper-tretter/Oregon-psilocybin-reddit-data-collection

## Inclusion Criteria

Posts are included if they meet ALL of the following:

1. **Location:** Explicitly mentions Oregon OR Colorado in the context of psilocybin therapy
   - Must appear within ~200 characters of psilocybin-related terms (contextual check)
   - Includes references to cities (Portland, Eugene, Denver, Boulder) and programs (Measure 109, OHA)

2. **Substance:** Specifically discusses psilocybin/mushrooms (not ketamine, MDMA, etc.)

3. **Content Type:** First-person experience reports
   - Trip/session reports and personal narratives
   - Descriptions of therapeutic experiences and outcomes
   - Reflections on the service experience

4. **Relevance Indicators:** Weighted scoring for:
   - First-person language ("I took," "my session," "I experienced")
   - Oregon-specific terms ("service center," "licensed facilitator," "Measure 109")
   - Therapeutic context ("preparation session," "integration," "guided session")

## Exclusion Criteria

Posts are excluded if they match ANY of the following:

**Subreddit-Level Exclusions (~100 subreddits):**
- Fiction/creative writing (r/nosleep, r/WritingPrompts)
- Investment/stocks (r/shroomstocks, r/wallstreetbets)
- Cultivation (r/unclebens, r/mushroomgrowers)
- Other therapies (r/ketamine, r/therapeuticketamine)
- Non-target states (r/massachusetts, r/california)
- Business/startups (r/femalefounders, r/entrepreneur)

**Content-Level Exclusions:**
| Category | Rationale |
|----------|-----------|
| News/Articles | Third-party reporting, not personal experience |
| Policy Discussion | Opinion/debate without experience |
| Cultivation | Growing content, not therapy |
| Sourcing Requests | Seeking substances, not therapy reports |
| Research Recruitment | Study recruitment posts |
| Advertisements | Commercial promotion |
| Business Introductions | Company announcements |
| Facilitator Perspective | Provider view, not patient experience |
| Drug Identification | Questions about unknown substances |
| Legislative Updates | Policy news without experience |

**Instant Disqualifiers:** Cultivation, sourcing requests, and drug identification posts are automatically excluded regardless of other factors.

## Preliminary Data Summary

- **Total posts collected:** 1,678
- **Posts meeting all criteria:** 77
  - Oregon-related: 73 (95%)
  - Colorado-related: 4 (5%)
- **Trip/session reports (before location filter):** 510

The Oregon/Colorado imbalance reflects that Oregon's program has been operational longer. As Colorado's program expands, we expect more data from that jurisdiction.

## Next Steps

1. **IRB Exemption:** I will reach out to Lukas about his prior IRB submissions for similar social media research
2. **Expand Dataset:** Continue collection as more experiences are shared
3. **Develop Coding Scheme:** Create systematic categories for outcomes, acute experiences, service factors
4. **Begin Analysis:** Thematic analysis of experience narratives

I've also prepared a more detailed research proposal document (attached/in the repo) that expands on the background, methods, and planned analyses.

Please let me know if you have any questions or suggestions for refining the methodology. I'm happy to discuss further.

Gratefully,
Cooper

---

*Attachments: RESEARCH_PROPOSAL.md*
