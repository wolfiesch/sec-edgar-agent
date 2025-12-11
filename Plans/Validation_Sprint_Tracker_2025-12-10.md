# Validation Sprint Tracker

**Created:** 12/10/2025 05:43 PM PST (via pst-timestamp)
**Sprint Duration:** 4 Weeks
**Sprint Goal:** Validate technical feasibility and market demand before MVP build
**Master Doc:** [Developer_First_SEC_API_Startup_2025-12-10.md](./Developer_First_SEC_API_Startup_2025-12-10.md)

---

## Sprint Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      4-WEEK VALIDATION SPRINT                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Week 1          Week 2          Week 3          Week 4                │
│  ────────        ────────        ────────        ────────              │
│  Table POC       User Research   Competitive     Landing Page          │
│                                  Analysis                               │
│                                                                         │
│  ▼               ▼               ▼               ▼                     │
│  Can we parse    Would they      What's the      Can we get            │
│  tables?         pay $249/mo?    gap?            100 signups?          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GO/NO-GO GATE (End of Week 4):                                        │
│  [ ] Table parsing works reliably                                      │
│  [ ] 5+ users said "yes, I'd pay $249/mo"                              │
│  [ ] Clear differentiation from sec-api.io documented                  │
│  [ ] 100+ waitlist signups                                             │
│                                                                         │
│  All checked → START MVP BUILD                                          │
│  Not all → REASSESS OR PIVOT                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Week 1: Table Parsing POC

**Dates:** TBD (Week of _____)
**Owner:** Wolfgang
**Goal:** Prove we can parse complex SEC tables into LLM-readable format

### Success Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Parse Apple Segment Information table with 100% numeric accuracy | [ ] Not Started | |
| 2 | Output in Markdown format | [ ] Not Started | |
| 3 | Feed to Claude/GPT-4 - answers "Americas operating income 2024?" correctly | [ ] Not Started | |
| 4 | Citation preserved (file, page, table location) | [ ] Not Started | |
| 5 | Processing time < 5 seconds per table | [ ] Not Started | |

### Daily Plan

| Day | Focus | Tasks | Status |
|-----|-------|-------|--------|
| **Day 1** | Environment Setup | - [ ] Install sec-parser, edgartools, pandas, bs4<br>- [ ] Set up test script structure<br>- [ ] Verify SEC API access | [ ] Not Started |
| **Day 2** | Data Acquisition | - [ ] Download Apple latest 10-K<br>- [ ] Identify Segment Information table location<br>- [ ] Extract raw HTML | [ ] Not Started |
| **Day 3** | Parser v1 | - [ ] Implement sec-parser approach<br>- [ ] Test on target table<br>- [ ] Document issues/gaps | [ ] Not Started |
| **Day 4** | Parser v2 | - [ ] Try XBRL extraction via EdgarTools<br>- [ ] Compare approaches<br>- [ ] Implement fallback logic | [ ] Not Started |
| **Day 5** | Validation | - [ ] Feed output to Claude<br>- [ ] Test 5 factual questions<br>- [ ] Measure accuracy<br>- [ ] Document results | [ ] Not Started |

### Deliverables

- [ ] `scripts/table_parsing_poc.py` - Working parser script
- [ ] `tests/test_table_parsing.py` - Test suite with accuracy metrics
- [ ] `docs/table_parsing_results.md` - Findings and recommendations

### Technical Notes

```python
# Target table: Apple Segment Information
# Expected structure:
# | Region | Metric | 2024 | 2023 | 2022 |
# |--------|--------|------|------|------|
# | Americas | Net sales | $X | $Y | $Z |
# | Americas | Operating income | ... | ... | ... |
# | Europe | Net sales | ... | ... | ... |
# ... etc

# Libraries to try:
# 1. sec-parser (primary) - https://github.com/alphanome-ai/sec-parser
# 2. edgartools (XBRL) - https://edgartools.readthedocs.io/
# 3. LayoutLM (fallback) - for complex nested tables
```

### Blockers & Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| sec-parser doesn't handle nested headers | Medium | Fall back to XBRL or custom parser |
| XBRL data incomplete for narrative tables | High | Use HTML parsing as primary for non-financial tables |
| Performance too slow | Low | Batch processing, caching |

---

## Week 2: User Research

**Dates:** TBD (Week of _____)
**Owner:** Wolfgang
**Goal:** Validate willingness to pay $249/mo for LLM-ready SEC data

### Success Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Complete 10 user interviews | [ ] Not Started | |
| 2 | 5+ users say "yes, I'd pay $249/mo" | [ ] Not Started | |
| 3 | Document top 3 use cases | [ ] Not Started | |
| 4 | Identify must-have features | [ ] Not Started | |

### Interview Targets

| # | Type | Source | Contact | Status | Notes |
|---|------|--------|---------|--------|-------|
| 1 | Fintech Developer | r/algotrading | | [ ] Not Started | |
| 2 | Fintech Developer | HN | | [ ] Not Started | |
| 3 | Quant Researcher | LinkedIn | | [ ] Not Started | |
| 4 | Small Fund Analyst | Network | | [ ] Not Started | |
| 5 | AI Startup Founder | Network | | [ ] Not Started | |
| 6 | Former Big 4 | PwC Network | | [ ] Not Started | |
| 7 | Compliance Officer | LinkedIn | | [ ] Not Started | |
| 8 | Data Engineer | Discord | | [ ] Not Started | |
| 9 | Academic Researcher | University | | [ ] Not Started | |
| 10 | Indie Hacker | Twitter/X | | [ ] Not Started | |

### Interview Script

```markdown
## Intro (2 min)
- Explain purpose: researching financial data APIs
- No selling, just learning

## Current Workflow (5 min)
1. How do you currently access SEC filing data?
2. What tools do you use? (AlphaSense, Bloomberg, sec-api.io, DIY)
3. What's the most painful part of the process?

## Use Cases (5 min)
4. What do you typically try to extract from filings?
5. Do you use LLMs/RAG with SEC data? How?
6. How important is citation/provenance to you?

## Pricing (5 min)
7. How much do you currently spend on financial data? (per month)
8. If an API gave you pre-chunked, LLM-ready SEC data with citations:
   - Would you pay $99/mo?
   - Would you pay $249/mo?
   - What would make it worth $249/mo?

## Wrap-up (3 min)
9. What feature would make this a must-have for you?
10. Can I follow up when we launch?
```

### Deliverables

- [ ] `docs/user_research_findings.md` - Summary of interviews
- [ ] Interview recordings/notes (with permission)
- [ ] Feature prioritization based on feedback

---

## Week 3: Competitive Analysis

**Dates:** TBD (Week of _____)
**Owner:** Wolfgang
**Goal:** Document exactly what sec-api.io and others can/can't do

### Success Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Complete sec-api.io trial | [ ] Not Started | |
| 2 | Document feature gap matrix | [ ] Not Started | |
| 3 | Test same query across 3 competitors | [ ] Not Started | |
| 4 | Identify unique value proposition | [ ] Not Started | |

### Competitors to Analyze

| Competitor | Trial Available | Status | Notes |
|------------|-----------------|--------|-------|
| sec-api.io | Yes (100 free calls) | [ ] Not Started | Primary competitor |
| Intrinio | Yes (limited) | [ ] Not Started | Enterprise focus |
| Alpha Vantage | Yes (25 calls/day) | [ ] Not Started | Market data focus |
| Kay.ai | Unknown | [ ] Not Started | Embeddings only |
| Captide | Unknown | [ ] Not Started | RAG-focused |

### Test Query Matrix

| Query | sec-api.io | Intrinio | Our Approach |
|-------|------------|----------|--------------|
| "Get AAPL risk factors mentioning China" | | | |
| "Compare NVDA risk disclosure 2023 vs 2024" | | | |
| "Extract lease maturity table from AAPL 10-K" | | | |
| "Get pre-computed embeddings for MSFT MD&A" | | | |
| "Find all companies mentioning supply chain in 10-K" | | | |

### Feature Gap Matrix

| Feature | sec-api.io | Intrinio | Us (Planned) |
|---------|------------|----------|--------------|
| Semantic search | | | |
| Pre-computed embeddings | | | |
| Citation in response | | | |
| Temporal change detection | | | |
| Table parsing (accurate) | | | |
| Python SDK | | | |
| Transparent pricing | | | |

### Deliverables

- [ ] `docs/competitive_analysis.md` - Detailed comparison
- [ ] Feature gap matrix (filled in)
- [ ] Unique selling proposition statement

---

## Week 4: Landing Page & Waitlist

**Dates:** TBD (Week of _____)
**Owner:** Wolfgang
**Goal:** Launch landing page and get 100 waitlist signups

### Success Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Landing page live | [ ] Not Started | |
| 2 | 100+ waitlist signups | [ ] Not Started | |
| 3 | <3% bounce rate | [ ] Not Started | |
| 4 | At least 1 "founding member" commit | [ ] Not Started | |

### Landing Page Elements

| Element | Status | Notes |
|---------|--------|-------|
| Hero headline | [ ] Not Started | "LLM-ready SEC data with citations" |
| Value props (3) | [ ] Not Started | Citations, Temporal, Embeddings |
| Code example | [ ] Not Started | 5 lines of Python |
| Pricing preview | [ ] Not Started | $249/mo Pro |
| Waitlist form | [ ] Not Started | Email + use case |
| Social proof | [ ] Not Started | Beta testimonials if available |

### Launch Channels

| Channel | Target Signups | Status | Notes |
|---------|----------------|--------|-------|
| Hacker News (Show HN) | 50 | [ ] Not Started | Primary channel |
| r/algotrading | 20 | [ ] Not Started | |
| r/MachineLearning | 10 | [ ] Not Started | |
| Twitter/X | 10 | [ ] Not Started | Financial AI community |
| LinkedIn | 5 | [ ] Not Started | Professional network |
| Direct outreach | 5 | [ ] Not Started | Interview participants |

### Tech Stack for Landing Page

```
Option A: Simple (Recommended)
- Carrd.co or Framer
- Waitlist: Tally.so or Typeform
- Analytics: Plausible or Fathom

Option B: Custom
- Next.js + Vercel
- Supabase for waitlist
- Posthog for analytics
```

### Deliverables

- [ ] Live landing page URL
- [ ] Waitlist with 100+ emails
- [ ] Conversion analytics report

---

## Go/No-Go Decision Framework

### At End of Week 4, Evaluate:

| Criterion | Target | Actual | Pass? |
|-----------|--------|--------|-------|
| Table parsing accuracy | >95% | | |
| User interviews completed | 10 | | |
| Users willing to pay $249/mo | 5+ | | |
| Competitive gap documented | Yes | | |
| Waitlist signups | 100+ | | |
| **Overall** | 5/5 | | |

### Decision Matrix

| Scenario | Outcome | Next Step |
|----------|---------|-----------|
| 5/5 criteria met | **GO** | Start MVP build (8 weeks) |
| 4/5 criteria met | **CONDITIONAL GO** | Address gap, then proceed |
| 3/5 criteria met | **REASSESS** | Pivot scope or approach |
| <3/5 criteria met | **NO-GO** | Major pivot or abandon |

---

## Sprint Retrospective Template

*To be filled at end of sprint*

### What Went Well
-

### What Could Be Improved
-

### Key Learnings
-

### Decisions Made
-

### Updated Assumptions
-

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 12/10/2025 05:43 PM PST | Claude/Wolfgang | Initial sprint tracker creation |

---

## Related Documents

- [Master Design Document](./Developer_First_SEC_API_Startup_2025-12-10.md)
- [Table Parsing Results](../docs/table_parsing_results.md) *(to be created)*
- [User Research Findings](../docs/user_research_findings.md) *(to be created)*
- [Competitive Analysis](../docs/competitive_analysis.md) *(to be created)*
