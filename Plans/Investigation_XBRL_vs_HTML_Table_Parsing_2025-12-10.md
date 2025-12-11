# Investigation: XBRL vs HTML Table Parsing

---
**IMPLEMENTATION STATUS**: ✅ COMPLETED
**Implemented Date**: 12/10/2025 09:22 PM PST (via pst-timestamp)
**Implementation Summary**: Table parsing POC validated with 100% accuracy using inline XBRL extraction. All 5 success criteria met. Ready for MVP implementation.
---

## Usage

To parse SEC tables using the validated inline XBRL approach:

```bash
# Parse a specific table from HTML file
uv run python scripts/table_parsing_poc/parse_inline_xbrl.py

# Test LLM comprehension
uv run python scripts/table_parsing_poc/test_with_llm.py
```

## What Was Implemented

**Completed:**
- ✅ Inline XBRL extraction parser (`parse_inline_xbrl.py`)
- ✅ Ground truth CSV for validation (`aapl_segment_groundtruth.csv`)
- ✅ LLM comprehension testing (`test_with_llm.py`)
- ✅ Comprehensive results documentation (`docs/table_parsing_results.md`)
- ✅ 100% numeric accuracy (42/42 data points)
- ✅ 100% LLM comprehension (5/5 questions correct)

**Files Created:**
- `scripts/table_parsing_poc/download_filing.py` - Filing download and table extraction
- `scripts/table_parsing_poc/parse_inline_xbrl.py` - Main parser implementation
- `scripts/table_parsing_poc/test_with_llm.py` - LLM validation
- `data/test_tables/aapl_segment_groundtruth.csv` - Validation baseline
- `data/test_tables/aapl_segment_parsed.md` - Parsed output (Markdown)
- `docs/table_parsing_results.md` - Full investigation report

**Deviations from Original Plan:**
- Skipped sec-parser approach (inline XBRL was sufficient)
- Skipped custom HTML parser (not needed)
- Compressed 3-day investigation into 1 day (~3 hours)
- Used GPT-4 mini instead of Claude for LLM testing (OpenAI API more readily available)

**Key Finding:** SEC tables contain embedded `<ix:nonfraction>` XBRL tags with structured data - parsing is simpler than expected!

## Testing

**Validation Tests:**
1. **Accuracy Test:** Compare parsed output to manually transcribed ground truth → **100% match (42/42 rows)**
2. **LLM Comprehension Test:** Ask GPT-4 5 factual questions about the table → **100% correct (5/5)**
3. **Performance Test:** Measure parsing time → **<2 seconds per table**

**To run tests:**
```bash
# Run parser and validate accuracy
uv run python scripts/table_parsing_poc/parse_inline_xbrl.py

# Test LLM comprehension
uv run python scripts/table_parsing_poc/test_with_llm.py
```

**Test Results:** See [docs/table_parsing_results.md](../docs/table_parsing_results.md) for comprehensive report.

---

# Original Investigation Plan

**Created:** 12/10/2025 08:41 PM PST (via pst-timestamp)
**Status:** ✅ Completed
**Owner:** Wolfgang
**Type:** Investigation
**Duration:** 3 days (Days 1-3 of Validation Sprint Week 1) → **Actual: 1 day (~3 hours)**
**Parent Plan:** [Validation Sprint Tracker](./Validation_Sprint_Tracker_2025-12-10.md)

---

## Objective

Determine the most reliable approach for parsing complex SEC filing tables into LLM-readable format with 100% numeric accuracy. This is the **critical validation gate** for the entire startup—if we can't solve table parsing, we don't have a product.

### Research Question

**Can we reliably parse Apple's Segment Information table from their latest 10-K with sufficient accuracy that an LLM can answer factual questions correctly?**

### Why This Matters

> **"The HTML Table Nightmare is the real technical risk."** - Gemini feedback

SEC filings contain critical financial data in HTML tables with:
- Multi-level headers (e.g., Region → Metric)
- Nested structures with subtotals
- Inconsistent formatting across companies
- Merged cells and complex layouts

Our **citation-native architecture** depends on being able to extract this data cleanly and preserve its source location.

---

## Success Criteria

| # | Criterion | Target | How to Measure |
|---|-----------|--------|----------------|
| 1 | **Numeric Accuracy** | 100% | All numbers in parsed output match source table exactly |
| 2 | **Structure Preservation** | Complete | Headers, rows, columns correctly mapped |
| 3 | **LLM Comprehension** | >95% | Claude/GPT-4 answers 5 factual questions correctly |
| 4 | **Citation Preserved** | Yes | Can link parsed data back to [AAPL 10-K 2024, Item 8, Table X, Page Y] |
| 5 | **Processing Speed** | <5 seconds | Per table extraction and parsing |

### Pass/Fail Gate

- **PASS:** Criteria 1-4 all met → Proceed to MVP build
- **CONDITIONAL PASS:** 3/5 met → Document gaps, implement fixes, retest
- **FAIL:** <3/5 met → Research alternative approaches (LayoutLM, vision models) or pivot product scope

---

## Test Case: Apple Segment Information Table

### Why Apple?

1. **Representative complexity:** Multi-level headers, nested structure
2. **Well-documented:** Easy to verify accuracy
3. **Tech/SaaS vertical:** Aligns with MVP focus
4. **High-value use case:** Geographic revenue breakdown is common query

### Target Table Structure

**Source:** Apple Inc. 10-K for fiscal year 2024
**Location:** Item 8 - Financial Statements (Segment Information)
**Expected format:**

```
| Region         | Metric            | 2024    | 2023    | 2022    |
|----------------|-------------------|---------|---------|---------|
| Americas       | Net sales         | $X,XXX  | $X,XXX  | $X,XXX  |
| Americas       | Operating income  | $X,XXX  | $X,XXX  | $X,XXX  |
| Europe         | Net sales         | $X,XXX  | $X,XXX  | $X,XXX  |
| Europe         | Operating income  | $X,XXX  | $X,XXX  | $X,XXX  |
| Greater China  | Net sales         | $X,XXX  | $X,XXX  | $X,XXX  |
| Greater China  | Operating income  | $X,XXX  | $X,XXX  | $X,XXX  |
| ...            | ...               | ...     | ...     | ...     |
```

### Test Questions for LLM Validation

After parsing, feed the output to Claude/GPT-4 and ask:

1. "What was Americas operating income in 2024?"
2. "How much did Greater China net sales change from 2023 to 2024?"
3. "Which region had the highest operating income in 2024?"
4. "What was the total net sales across all regions in 2022?"
5. "Did any region see a decline in net sales from 2023 to 2024?"

**Expected:** LLM answers all 5 correctly with high confidence and cites specific numbers.

---

## Technical Approaches to Test

### Approach 1: sec-parser (Primary)

**Library:** [`sec-parser`](https://github.com/alphanome-ai/sec-parser)
**Why try first:** Purpose-built for SEC EDGAR HTML documents

**Pros:**
- Open source, actively maintained
- Designed specifically for SEC filings
- Handles semantic elements (sections, tables, paragraphs)

**Cons:**
- May not handle all edge cases
- Relatively new library
- Limited documentation for complex tables

**Implementation Plan:**
```python
from sec_parser import EdgarParser

# Download Apple 10-K HTML
filing_html = download_filing("AAPL", "10-K", 2024)

# Parse with sec-parser
parser = EdgarParser()
parsed = parser.parse(filing_html)

# Extract tables
tables = parsed.get_tables()
segment_table = find_segment_info_table(tables)

# Convert to Markdown
markdown_output = table_to_markdown(segment_table)
```

### Approach 2: XBRL via EdgarTools (Secondary)

**Library:** [`edgartools`](https://edgartools.readthedocs.io/)
**Why try:** We already use edgartools, XBRL is structured data

**Pros:**
- Structured data (XML-based)
- Standardized tags for financial metrics
- Already integrated into our codebase

**Cons:**
- Not all tables have XBRL equivalents (narrative tables missing)
- XBRL tags may not map cleanly to display tables
- Geographic segment data may use custom tags

**Implementation Plan:**
```python
from edgartools import Filing

# Get Apple 10-K
filing = Filing("AAPL", "10-K", 2024)

# Extract XBRL data
xbrl = filing.xbrl()

# Query segment revenue data
segment_revenue = xbrl.get_facts(
    concept="RevenueFromContractWithCustomerByGeographicArea"
)

# Query segment operating income
segment_income = xbrl.get_facts(
    concept="OperatingIncomeLossBySegment"
)

# Combine into table format
table_data = combine_xbrl_facts(segment_revenue, segment_income)
markdown_output = format_as_markdown(table_data)
```

### Approach 3: Custom HTML Parser (Fallback)

**Libraries:** BeautifulSoup, pandas, lxml
**Why try:** Maximum control, can handle edge cases

**Pros:**
- Complete control over parsing logic
- Can handle any HTML structure
- Fallback if other approaches fail

**Cons:**
- Time-intensive to build
- Brittle (breaks with layout changes)
- Requires extensive testing

**Implementation Plan:**
```python
from bs4 import BeautifulSoup
import pandas as pd

# Parse HTML
soup = BeautifulSoup(filing_html, 'lxml')

# Find segment information table by context
# (look for headers containing "Americas", "Europe", "Greater China")
tables = soup.find_all('table')
segment_table = identify_segment_table(tables)

# Extract headers
headers = extract_multi_level_headers(segment_table)

# Extract rows
rows = extract_table_rows(segment_table)

# Convert to pandas DataFrame
df = pd.DataFrame(rows, columns=headers)

# Export to Markdown
markdown_output = df.to_markdown()
```

### Hybrid Approach (Recommended)

**Strategy:** Try approaches in sequence, use best result

1. **Try XBRL first** (fastest, most reliable for financial tables)
2. **If XBRL incomplete, try sec-parser** (handles narrative tables)
3. **If sec-parser fails, use custom parser** (maximum control)
4. **Store metadata about which approach worked** (for future filings)

```python
def parse_table(filing, table_type="segment_info"):
    """
    Hybrid table parsing with fallback logic.

    Returns:
        TableData: Parsed table with metadata about approach used
    """
    # Attempt 1: XBRL
    try:
        result = parse_via_xbrl(filing, table_type)
        if validate_completeness(result):
            return TableData(
                content=result,
                source="xbrl",
                confidence="high"
            )
    except Exception as e:
        log.warning(f"XBRL parsing failed: {e}")

    # Attempt 2: sec-parser
    try:
        result = parse_via_sec_parser(filing, table_type)
        if validate_completeness(result):
            return TableData(
                content=result,
                source="sec-parser",
                confidence="medium"
            )
    except Exception as e:
        log.warning(f"sec-parser failed: {e}")

    # Attempt 3: Custom parser
    try:
        result = parse_via_custom_parser(filing, table_type)
        return TableData(
            content=result,
            source="custom",
            confidence="low"
        )
    except Exception as e:
        log.error(f"All parsing approaches failed: {e}")
        raise TableParsingError(f"Could not parse {table_type}")
```

---

## Implementation Plan (3 Days)

### Day 1: Setup + Data Acquisition (8 hours)

#### Morning (4 hours): Environment Setup
- [ ] Install required libraries
  ```bash
  uv pip install sec-parser edgartools beautifulsoup4 lxml pandas tabulate
  ```
- [ ] Create `scripts/table_parsing_poc/` directory structure
- [ ] Set up test framework with pytest
- [ ] Configure logging

#### Afternoon (4 hours): Data Acquisition
- [ ] Download Apple 10-K 2024 using edgartools
- [ ] Extract HTML source for Item 8 (Financial Statements)
- [ ] Manually identify Segment Information table location
- [ ] Save reference HTML to `data/test_tables/aapl_segment_info.html`
- [ ] Create ground truth CSV with expected values
  - Manually transcribe table to `data/test_tables/aapl_segment_info_groundtruth.csv`
  - This is our accuracy baseline

**Deliverable:** Apple 10-K downloaded, segment table identified, ground truth created

---

### Day 2: Parser Implementation (8 hours)

#### Morning (4 hours): XBRL Approach
- [ ] Implement `parse_via_xbrl()` function
- [ ] Query XBRL for geographic segment data
- [ ] Map XBRL facts to table structure
- [ ] Compare output to ground truth
- [ ] **Decision point:** If 100% accuracy → use XBRL. If gaps → proceed to sec-parser

#### Afternoon (4 hours): sec-parser Approach
- [ ] Implement `parse_via_sec_parser()` function
- [ ] Extract tables using sec-parser API
- [ ] Identify segment table from parsed elements
- [ ] Convert to Markdown format
- [ ] Compare output to ground truth
- [ ] **Decision point:** If 100% accuracy → use sec-parser. If gaps → proceed to custom parser

**Deliverable:** Two parsing approaches implemented and tested

---

### Day 3: Validation + Documentation (8 hours)

#### Morning (4 hours): Custom Parser (if needed) + Hybrid Logic
- [ ] Implement `parse_via_custom_parser()` if approaches 1-2 failed
- [ ] Implement hybrid fallback logic
- [ ] Run final accuracy comparison against ground truth
- [ ] **GATE:** Achieve 100% numeric accuracy or document why not possible

#### Afternoon (4 hours): LLM Validation + Documentation
- [ ] Feed parsed table to Claude Sonnet
- [ ] Ask 5 test questions
- [ ] Measure accuracy of LLM responses
- [ ] Document results in `docs/table_parsing_results.md`
- [ ] Create recommendations for MVP implementation
- [ ] Update Validation Sprint Tracker with results

**Deliverable:**
- Validation complete
- `docs/table_parsing_results.md` with findings
- Go/No-Go recommendation

---

## Files to Create/Modify

### New Files

```
scripts/table_parsing_poc/
├── __init__.py
├── download_filing.py          # Download Apple 10-K
├── parse_xbrl.py               # XBRL parsing approach
├── parse_sec_parser.py         # sec-parser approach
├── parse_custom.py             # Custom HTML parser
├── hybrid_parser.py            # Orchestrates fallback logic
├── validate_accuracy.py        # Compare to ground truth
└── test_with_llm.py           # Feed to Claude and test Q&A

tests/table_parsing_poc/
├── __init__.py
├── test_parse_xbrl.py
├── test_parse_sec_parser.py
├── test_parse_custom.py
└── test_hybrid_parser.py

data/test_tables/
├── aapl_segment_info.html      # Raw HTML table
├── aapl_segment_info_groundtruth.csv  # Manual transcription
└── aapl_segment_info_parsed.md # Final parsed output

docs/
└── table_parsing_results.md    # Investigation findings
```

### Modified Files

```
pyproject.toml                  # Add new dependencies
Plans/Validation_Sprint_Tracker_2025-12-10.md  # Update Week 1 status
```

---

## Dependencies & Prerequisites

### Python Libraries

```toml
[project.dependencies]
# Existing
edgartools = "^3.0.0"
beautifulsoup4 = "^4.12.0"
lxml = "^5.0.0"
pandas = "^2.2.0"

# New for this investigation
sec-parser = "^0.30.0"  # SEC HTML parser
tabulate = "^0.9.0"     # Markdown table generation
```

### Data Requirements

- Apple 10-K filing for fiscal year 2024
- Access to SEC EDGAR (no auth required)
- Claude API access for LLM validation

### Time Requirements

- **Total:** 24 hours (3 days × 8 hours)
- **Can be compressed:** Yes, to 2 days if working 12-hour days
- **Buffer:** Add 8 hours for unexpected issues (total 32 hours / 4 days)

---

## Testing Strategy

### Unit Tests

```python
# tests/table_parsing_poc/test_parse_xbrl.py
def test_xbrl_parser_accuracy():
    """Test XBRL parser against ground truth."""
    parser = XBRLParser()
    result = parser.parse("AAPL", "10-K", 2024)
    ground_truth = load_ground_truth("aapl_segment_info_groundtruth.csv")

    # Assert 100% numeric accuracy
    assert compare_tables(result, ground_truth) == 1.0

def test_xbrl_parser_citation():
    """Test that citations are preserved."""
    parser = XBRLParser()
    result = parser.parse("AAPL", "10-K", 2024)

    assert result.citation.ticker == "AAPL"
    assert result.citation.form == "10-K"
    assert result.citation.year == 2024
    assert result.citation.section == "Item 8"
```

### Integration Tests

```python
# tests/table_parsing_poc/test_hybrid_parser.py
def test_hybrid_parser_fallback():
    """Test that hybrid parser tries all approaches."""
    parser = HybridParser()

    # Mock XBRL to fail
    with patch('parse_xbrl', side_effect=Exception("XBRL failed")):
        result = parser.parse("AAPL", "10-K", 2024)

        # Should fall back to sec-parser or custom
        assert result.source in ["sec-parser", "custom"]
```

### LLM Validation Tests

```python
# scripts/table_parsing_poc/test_with_llm.py
def test_llm_comprehension():
    """Test that LLM can answer questions from parsed table."""
    parsed_table = hybrid_parser.parse("AAPL", "10-K", 2024)

    questions = [
        "What was Americas operating income in 2024?",
        "How much did Greater China net sales change from 2023 to 2024?",
        "Which region had the highest operating income in 2024?",
        "What was the total net sales across all regions in 2022?",
        "Did any region see a decline in net sales from 2023 to 2024?"
    ]

    # Feed to Claude
    claude_responses = []
    for q in questions:
        response = call_claude_api(
            prompt=f"Based on this table:\n\n{parsed_table}\n\nQuestion: {q}"
        )
        claude_responses.append(response)

    # Manually verify answers (first run)
    # Then assert correct answers in automated tests
    accuracy = calculate_answer_accuracy(claude_responses, expected_answers)
    assert accuracy >= 0.95  # 95% threshold
```

### Manual Validation Checklist

- [ ] Visual inspection: Does parsed Markdown look correct?
- [ ] Spot check: Do 10 random numbers match ground truth?
- [ ] Structure check: Are headers preserved correctly?
- [ ] Citation check: Can we link back to source filing + page?
- [ ] Speed check: Does parsing complete in <5 seconds?

---

## Potential Challenges & Mitigations

### Challenge 1: XBRL Tags Don't Match Display Table

**Problem:** XBRL may use different granularity than HTML table (e.g., quarterly vs annual)

**Mitigation:**
- Document XBRL limitations for this specific table
- Fall back to HTML parsing
- For MVP, prioritize HTML parsing for narrative tables, XBRL for pure financials

### Challenge 2: Multi-Level Headers Lose Context

**Problem:** Nested headers like "Americas → Operating Income" may flatten incorrectly

**Mitigation:**
- Implement smart header merging (e.g., "Americas Operating Income")
- Preserve original structure in metadata
- Test with LLM to ensure comprehension

### Challenge 3: Inconsistent HTML Structure Across Companies

**Problem:** Parser works for Apple but breaks for other companies

**Mitigation:**
- Test on 3 companies: AAPL (Tech), JPM (Finance), WMT (Retail)
- Document common patterns
- Build regex-based heuristics for table identification

### Challenge 4: Processing Speed Too Slow

**Problem:** Parsing takes >5 seconds per table

**Mitigation:**
- Profile code to find bottlenecks
- Cache parsed results
- Consider parallel processing for batch ingestion

### Challenge 5: LLM Can't Answer Questions Accurately

**Problem:** Parsed output is technically correct but LLM-unfriendly

**Mitigation:**
- Add natural language context to tables (e.g., "Apple Inc. Geographic Segment Revenue for fiscal years 2022-2024")
- Include units explicitly (e.g., "in millions of USD")
- Test different output formats (Markdown vs CSV vs JSON)

---

## Success Metrics & Decision Criteria

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Numeric accuracy** | 100% | Compare parsed vs ground truth CSV |
| **LLM answer accuracy** | >95% | 5/5 questions answered correctly |
| **Processing speed** | <5 sec | Time from HTML input to Markdown output |
| **Coverage** | 100% | All table cells captured (no missing data) |

### Qualitative Assessment

- [ ] **Maintainability:** Is the parser code clean and well-documented?
- [ ] **Robustness:** Does it handle edge cases gracefully?
- [ ] **Scalability:** Can we extend this to other table types?
- [ ] **Integration:** Does it fit into our existing architecture?

### Go/No-Go Decision Matrix

| Outcome | Criteria | Decision |
|---------|----------|----------|
| **GO** | All 5 quantitative metrics met + qualitative assessment positive | Proceed to MVP build (Week 3) |
| **CONDITIONAL GO** | 4/5 metrics met, clear path to fix remaining gap | Fix over weekend, retest Monday, then proceed |
| **REASSESS** | 3/5 metrics met | Research alternative approaches (LayoutLM, GPT-4 Vision), 1 extra week |
| **NO-GO** | <3/5 metrics met | Major technical blocker, pivot product scope or abandon |

---

## Expected Outcomes & Deliverables

### If Successful (PASS)

**Deliverables:**
1. Working hybrid parser with 100% accuracy on Apple segment table
2. Documented approach with code in `scripts/table_parsing_poc/`
3. Test suite with >80% coverage
4. `docs/table_parsing_results.md` with recommendations:
   - Which parsing approach to use for MVP
   - Edge cases to handle
   - Integration plan with existing codebase

**Next Steps:**
- Update Validation Sprint Tracker: Week 1 Day 1-3 ✅ Complete
- Proceed to Days 4-7: User interviews
- Confidence level: HIGH for MVP table parsing implementation

### If Conditional (NEEDS WORK)

**Deliverables:**
1. Partial working parser (e.g., 95% accuracy)
2. Documented gaps and proposed fixes
3. Additional test cases needed

**Next Steps:**
- Allocate weekend (2 days) to fix gaps
- Retest Monday morning
- If fixed → proceed. If not → reassess approach

### If Fails (NO-GO)

**Deliverables:**
1. Analysis of why approaches failed
2. Alternative approaches to research:
   - **LayoutLM** - Layout-aware transformer for document understanding
   - **GPT-4 Vision** - Vision model for table extraction from images
   - **Camelot/Tabula** - PDF table extraction (if convert HTML to PDF)
   - **Scope pivot** - Focus on XBRL-only data, skip narrative tables

**Next Steps:**
- Document technical blocker in Validation Sprint Tracker
- Make NO-GO decision or extend validation sprint by 1 week
- If extended: Research and prototype alternative approaches

---

## Integration with Validation Sprint

### Week 1 Timeline (7 days)

| Day | This Investigation | Parallel Activities |
|-----|-------------------|---------------------|
| **Day 1** | Setup + Data Acquisition | - |
| **Day 2** | Parser Implementation | - |
| **Day 3** | Validation + Documentation | - |
| **Day 4** | - | Source 20 interview candidates |
| **Day 5** | - | Conduct interviews (5) |
| **Day 6** | - | Conduct interviews (5) |
| **Day 7** | - | Synthesize findings |

### Success Criteria Contribution

This investigation validates **Week 1 Success Criterion #1:**
- [ ] Table parsing works with >95% accuracy

If this passes, we have strong evidence that the core technical challenge is solvable.

---

## Post-Investigation Actions

### If PASS

1. **Update Sprint Tracker**
   ```markdown
   - [x] Table parsing works with >95% accuracy ✅
   - Result: [Approach] achieved 100% accuracy in 3 days
   ```

2. **Create MVP Implementation Plan**
   - File: `Plans/Feature_Table_Parser_MVP_2025-12-XX.md`
   - Scope: Generalize POC to handle multiple table types
   - Timeline: Week 3 (MVP build phase)

3. **Communicate Results**
   - Share `docs/table_parsing_results.md` with stakeholders
   - Update master design document with confirmed approach

### If CONDITIONAL

1. **Document Gaps**
   - Specific accuracy failures
   - Edge cases not handled
   - Performance issues

2. **Create Fix Plan**
   - Allocate 2-day buffer
   - Clear acceptance criteria
   - Retest protocol

### If NO-GO

1. **Pivot Decision**
   - Schedule decision meeting
   - Review alternative approaches
   - Estimate additional validation time needed (1-2 weeks)

2. **Update Master Plan**
   - Mark table parsing as "BLOCKED"
   - Document blocker in critical challenges section
   - Propose alternative product scope if needed

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 12/10/2025 08:41 PM PST (via pst-timestamp) | Claude/Wolfgang | Initial investigation plan created |

---

## Related Documents

- [Validation Sprint Tracker](./Validation_Sprint_Tracker_2025-12-10.md) - Parent plan (Week 1, Days 1-3)
- [Master Design Document](./Developer_First_SEC_API_Startup_2025-12-10.md) - Startup strategy
- [Plan-Driven Development Framework](../.claude/PLAN_DRIVEN_DEVELOPMENT.md) - Execution standards

---

## Appendix: Key Libraries Documentation

### sec-parser
- GitHub: https://github.com/alphanome-ai/sec-parser
- Docs: https://sec-parser.readthedocs.io/
- Key features: Semantic element detection, table extraction, section parsing

### edgartools
- Docs: https://edgartools.readthedocs.io/
- Key features: XBRL parsing, filing download, fact extraction
- Already in use: `src/data/edgar_client.py`

### BeautifulSoup
- Docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Key features: HTML parsing, navigation, extraction

### pandas
- Docs: https://pandas.pydata.org/docs/
- Key features: DataFrame manipulation, CSV I/O, to_markdown()
