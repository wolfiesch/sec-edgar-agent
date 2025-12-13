# Phase 2: Feature Push & Demo Readiness

**Created:** 12/13/2025 01:46 AM PST (via pst-timestamp)
**Status:** PLANNING
**Goal:** Transform MVP into demo-ready product with compelling differentiators

---

## Executive Summary

Phase 2 focuses on three parallel tracks:
1. **Demo Polish** - Make the product visually impressive and frictionless
2. **Differentiation** - Build features competitors don't have
3. **Go-to-Market** - Validate demand and prepare for users

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 2: FEATURE PUSH                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Track A: Demo Polish     Track B: Differentiation    Track C: GTM          │
│  ─────────────────────    ────────────────────────    ──────────────        │
│                                                                              │
│  • Quick Actions Panel    • Compare Companies         • Landing Page        │
│  • Export Functionality   • Historical Trends         • User Interviews     │
│  • Latency Optimization   • Change Detection          • Waitlist            │
│                           • Ticker Robustness                               │
│                                                                              │
│  ▼                        ▼                           ▼                     │
│  "Wow, this is polished"  "No one else does this"    "100+ signups"        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current State (Post Phase 1)

### Completed ✅
- Multi-agent orchestration (plan → execute → validate → synthesize)
- 26 registered tools across 5 categories
- Table parsing with 100% accuracy (income, balance, cashflow, segments)
- Semantic search with ChromaDB vector store
- Python SDK (`pip install -e sdk/`)
- React frontend with 3 tabs (Chat, Tables, Search)
- Deployed to Fly.io (https://sec-edgar-agent.fly.dev/)

### Gaps Identified
- No visual data representation (charts)
- No multi-company comparison UI
- No export functionality
- Agent latency ~8-12s for simple queries
- Hardcoded ticker mapping (~30 companies)
- No landing page or waitlist

---

## Track A: Demo Polish

### A1. Quick Actions Panel
**Priority:** T0 | **Effort:** 1 day | **Impact:** High

Add preset action buttons to reduce demo friction.

**Deliverables:**
- [ ] Quick action buttons above query input
- [ ] Preset queries: "Company Overview", "Financial Summary", "Risk Factors", "Recent Filings"
- [ ] Ticker autocomplete with 50+ common companies
- [ ] Recent tickers memory (localStorage)

**Implementation:**
```tsx
// frontend/src/components/QuickActions.tsx
const quickActions = [
  { label: "📊 Financial Overview", query: "Give me a financial overview of {ticker}" },
  { label: "⚠️ Risk Factors", query: "What are the key risk factors for {ticker}?" },
  { label: "📈 Revenue Trends", query: "Show {ticker} revenue trends over the past 3 years" },
  { label: "📋 Latest 10-K Summary", query: "Summarize {ticker}'s latest 10-K filing" },
];
```

**Success Criteria:**
- [ ] One-click query submission
- [ ] Ticker input with autocomplete
- [ ] Mobile-responsive design

---

### A2. Export Functionality
**Priority:** T0 | **Effort:** 0.5 days | **Impact:** Medium

Allow users to export results for use in their applications.

**Deliverables:**
- [ ] "Copy as Markdown" button on ResponsePanel
- [ ] "Download JSON" button for structured data
- [ ] "Copy Citation" for individual sources

**Implementation:**
```tsx
// Add to ResponsePanel.tsx
<button onClick={() => navigator.clipboard.writeText(markdownContent)}>
  Copy Markdown
</button>
<button onClick={() => downloadJson(structuredData)}>
  Download JSON
</button>
```

**Success Criteria:**
- [ ] Clipboard copy works cross-browser
- [ ] JSON export includes citations and metadata
- [ ] Toast notification on successful copy

---

### A3. Latency Optimization
**Priority:** T1 | **Effort:** 2 days | **Impact:** High

Reduce time-to-first-result for simple queries.

**Current State:**
- 4 LLM calls per query: Plan → Execute → Validate → Synthesize
- Average latency: 8-12 seconds
- Target: <5 seconds for simple queries

**Deliverables:**
- [ ] Query complexity classifier (simple vs complex)
- [ ] Skip validation for simple factual queries
- [ ] Merge validate+synthesize for medium queries
- [ ] Streaming first results earlier

**Implementation Strategy:**
```python
# src/agents/orchestrator.py
def classify_query_complexity(query: str) -> str:
    """Classify query as 'simple', 'medium', or 'complex'."""
    simple_patterns = ["what is", "revenue", "net income", "stock price"]
    complex_patterns = ["compare", "analyze", "trend", "risk factors"]
    # Return classification based on pattern matching
```

**Success Criteria:**
- [ ] Simple queries: <5 seconds
- [ ] Medium queries: <8 seconds
- [ ] Complex queries: <15 seconds (acceptable)

---

## Track B: Differentiation Features

### B1. Compare Companies Feature
**Priority:** T0 | **Effort:** 2 days | **Impact:** Very High

Multi-company comparison is a key differentiator - competitors don't offer this.

**Deliverables:**
- [ ] New "Compare" tab in frontend
- [ ] Multi-ticker input (2-5 companies)
- [ ] Metric selector (Revenue, Net Income, EPS, etc.)
- [ ] Side-by-side table output
- [ ] Visual comparison chart

**Implementation:**
```tsx
// frontend/src/components/CompareCompanies.tsx
interface CompareRequest {
  tickers: string[];  // ["AAPL", "MSFT", "GOOGL"]
  metrics: string[];  // ["revenue", "net_income", "eps"]
  years: number;      // 3
}
```

**API Integration:**
- Uses existing `compare_companies` tool
- Endpoint: `POST /api/v1/compare` (new)

**Success Criteria:**
- [ ] Compare 2-5 companies in <10 seconds
- [ ] Clean tabular output with YoY changes
- [ ] Bar chart visualization

---

### B2. Historical Trend Visualization
**Priority:** T1 | **Effort:** 2 days | **Impact:** High

Transform raw trend data into visual charts.

**Deliverables:**
- [ ] Line chart component for time-series data
- [ ] Bar chart for year-over-year comparisons
- [ ] Integration with `analyze_historical_trends` tool output
- [ ] Interactive tooltips with exact values

**Tech Stack:**
- Recharts (React charting library)
- Already compatible with Tailwind dark theme

**Implementation:**
```tsx
// frontend/src/components/TrendChart.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

const TrendChart = ({ data, metric }) => (
  <LineChart data={data}>
    <XAxis dataKey="year" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey={metric} stroke="#3b82f6" />
  </LineChart>
);
```

**Success Criteria:**
- [ ] Charts render for revenue, net income, EPS trends
- [ ] Responsive sizing
- [ ] Dark theme compatible

---

### B3. Filing Change Detection
**Priority:** T1 | **Effort:** 2 days | **Impact:** High

"What changed?" is a unique value proposition.

**Deliverables:**
- [ ] Diff view component for text changes
- [ ] Integration with `detect_risk_changes` tool
- [ ] Year-over-year comparison selector
- [ ] Highlighted additions/deletions

**Use Cases:**
- "What changed in AAPL's risk factors between 2023 and 2024?"
- "Compare TSLA's business description across last 3 years"
- "Show new risks added in latest 10-K"

**Implementation:**
```tsx
// frontend/src/components/FilingDiff.tsx
const FilingDiff = ({ oldText, newText }) => {
  const diff = computeDiff(oldText, newText);
  return (
    <div className="diff-view">
      {diff.map(part => (
        <span className={part.added ? 'bg-green-900' : part.removed ? 'bg-red-900' : ''}>
          {part.value}
        </span>
      ))}
    </div>
  );
};
```

**Success Criteria:**
- [ ] Clear visual diff with green/red highlighting
- [ ] Summary of key changes
- [ ] Works for risk factors, business description, MD&A

---

### B4. Ticker Robustness
**Priority:** T2 | **Effort:** 1 day | **Impact:** Medium

Fix "Tesla revenue" failing but "TSLA revenue" working.

**Current State:**
- Hardcoded mapping for ~30 companies in executor.py
- Fallback pattern matching is limited

**Deliverables:**
- [ ] SEC CIK → Ticker lookup integration
- [ ] Fuzzy company name matching
- [ ] Cache of company name → ticker mappings
- [ ] Graceful error messages for unknown companies

**Implementation Options:**
1. **SEC EDGAR Company Search API** (free, authoritative)
2. **Local database of S&P 500 + popular companies** (fast, limited)
3. **Third-party API** (comprehensive, potential cost)

**Recommended:** Option 1 + 2 hybrid

```python
# src/data/ticker_resolver.py
class TickerResolver:
    def __init__(self):
        self.local_cache = load_sp500_tickers()  # ~500 companies

    def resolve(self, query: str) -> str | None:
        # Try exact match first
        if query.upper() in self.local_cache:
            return query.upper()
        # Try fuzzy match
        matches = fuzzy_search(query, self.local_cache.keys())
        if matches:
            return matches[0]
        # Fall back to SEC API
        return self.search_sec_edgar(query)
```

**Success Criteria:**
- [ ] "Tesla" → "TSLA" works
- [ ] "Microsoft" → "MSFT" works
- [ ] Unknown companies return helpful error

---

## Track C: Go-to-Market Prep

### C1. Landing Page
**Priority:** T2 | **Effort:** 1 day | **Impact:** High (for validation)

Simple landing page to capture interest and validate demand.

**Deliverables:**
- [ ] Hero section with value proposition
- [ ] Demo GIF/video showing key features
- [ ] Feature highlights (3-4 bullets)
- [ ] Waitlist signup form
- [ ] Pricing preview ($249/mo teaser)

**Tech Stack:**
- Next.js or simple HTML/Tailwind
- Deploy to Vercel
- Waitlist: ConvertKit, Buttondown, or simple Supabase

**Content Structure:**
```
┌─────────────────────────────────────────┐
│  SEC EDGAR API for LLMs                 │
│  ─────────────────────────              │
│  100% accurate financial tables.        │
│  Built for AI applications.             │
│                                         │
│  [See Demo]  [Join Waitlist]            │
├─────────────────────────────────────────┤
│  ✓ Parse any SEC table instantly        │
│  ✓ Compare companies side-by-side       │
│  ✓ Track filing changes over time       │
│  ✓ Python SDK included                  │
├─────────────────────────────────────────┤
│  [Demo GIF here]                        │
├─────────────────────────────────────────┤
│  Starting at $249/mo                    │
│  [Join Waitlist - Get 30% Off Launch]   │
└─────────────────────────────────────────┘
```

**Success Criteria:**
- [ ] Page live at sec-api-llm.dev (or similar)
- [ ] Waitlist form captures email
- [ ] Target: 100 signups in 2 weeks

---

### C2. User Research Interviews
**Priority:** T2 | **Effort:** Ongoing | **Impact:** Critical (for validation)

Validate willingness to pay and understand pain points.

**Target Users:**
- Fintech developers building AI products
- Quant researchers at hedge funds
- Financial analysts using LLMs
- Indie hackers building finance tools

**Interview Guide:**
1. What tools do you currently use for SEC data?
2. What's the most frustrating part of working with SEC filings?
3. How much time do you spend on data extraction vs analysis?
4. Would you pay $249/mo for 100% accurate, LLM-ready SEC data?
5. What features would make this a must-have?

**Outreach Channels:**
- LinkedIn (fintech/quant communities)
- Twitter/X (AI/finance accounts)
- Reddit (r/algotrading, r/fintech, r/LocalLLaMA)
- Hacker News (Show HN post)

**Deliverables:**
- [ ] Interview script document
- [ ] 5-10 completed interviews
- [ ] Synthesis document with key insights
- [ ] Go/No-Go decision on pricing

**Success Criteria:**
- [ ] 5+ users say "yes, I'd pay $249/mo"
- [ ] Clear understanding of must-have features
- [ ] Documented objections and concerns

---

## Implementation Schedule

### Sprint 1: Demo Polish (Days 1-3)
| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1 | Quick Actions | QuickActions component, ticker autocomplete |
| 2 | Export + Compare UI | Export buttons, Compare tab skeleton |
| 3 | Compare Backend | Compare API endpoint, integration |

### Sprint 2: Differentiation (Days 4-7)
| Day | Focus | Deliverables |
|-----|-------|--------------|
| 4 | Charts Setup | Recharts integration, TrendChart component |
| 5 | Trend Visualization | Historical trends with charts |
| 6 | Change Detection | FilingDiff component, risk factor diffs |
| 7 | Ticker Robustness | TickerResolver, fuzzy matching |

### Sprint 3: Optimization + GTM (Days 8-10)
| Day | Focus | Deliverables |
|-----|-------|--------------|
| 8 | Latency Optimization | Query classifier, fast path |
| 9 | Landing Page | Landing page live, waitlist active |
| 10 | Polish + Deploy | Final testing, production deploy |

### Ongoing: User Research
- Start outreach on Day 1
- Conduct interviews throughout sprints
- Synthesize findings after Sprint 3

---

## Success Metrics

### Demo Readiness
| Metric | Target | Current |
|--------|--------|---------|
| Simple query latency | <5s | ~10s |
| Features demoed in <2 min | 5+ | 3 |
| "Wow" reactions in demos | High | Medium |

### Differentiation
| Metric | Target | Current |
|--------|--------|---------|
| Unique features vs competitors | 3+ | 1 (tables) |
| Multi-company comparison | Yes | No |
| Visual charts | Yes | No |

### Go-to-Market
| Metric | Target | Current |
|--------|--------|---------|
| Waitlist signups | 100+ | 0 |
| User interviews completed | 5+ | 0 |
| "Would pay $249/mo" responses | 5+ | 0 |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Latency optimization fails | Medium | High | Accept 8s for complex, focus on perceived speed |
| Low waitlist signups | Medium | High | Test multiple channels, adjust messaging |
| Users won't pay $249/mo | Medium | Critical | Explore $99/mo tier, usage-based pricing |
| Chart library issues | Low | Medium | Fallback to simple tables |

---

## Dependencies

### External
- Recharts library (MIT license, well-maintained)
- SEC EDGAR API (free, no auth required)
- Waitlist service (ConvertKit free tier)

### Internal
- Existing tool implementations (compare, trends, risk detection)
- Current frontend architecture (React + Tailwind)
- Fly.io deployment pipeline

---

## Go/No-Go Gates

### After Sprint 1
- [ ] Quick actions working
- [ ] Export functionality complete
- [ ] Compare tab renders

### After Sprint 2
- [ ] Charts displaying correctly
- [ ] Change detection working
- [ ] Ticker resolution improved

### After Sprint 3
- [ ] Landing page live
- [ ] Latency targets met
- [ ] Ready for user demos

### Final Gate (End of Phase 2)
- [ ] 100+ waitlist signups
- [ ] 5+ "would pay" interviews
- [ ] All T0/T1 features complete

**All checked → START MONETIZATION**
**Not all → REASSESS APPROACH**

---

## Changelog

| Timestamp | Change |
|-----------|--------|
| 12/13/2025 01:46 AM PST (via pst-timestamp) | Initial plan created |
| 12/13/2025 02:01 AM PST (via pst-timestamp) | **Sprint 1 Day 1-2 Complete**: QuickActions component (60 tickers, autocomplete, recent tickers localStorage), Export buttons (Copy MD, Download JSON) on ResponsePanel, Toast notification system, Compare tab skeleton with CompareCompanies component, POST /api/v1/compare endpoint |
| 12/13/2025 02:17 AM PST (via pst-timestamp) | **Sprint 2 Complete**: Recharts integration with TrendChart component, bar/line chart visualization in Compare tab, FilingDiff component for risk factor change detection with POST /api/v1/filings/diff endpoint, TickerResolver with 200+ company mappings integrated into executor |

