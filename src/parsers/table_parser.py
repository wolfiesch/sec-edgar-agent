from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from bs4 import BeautifulSoup
from edgar import Company

@dataclass
class ParsedTable:
    """Structured table with metadata."""
    markdown: str
    structured: list[dict]
    citation: str
    confidence: str  # "high", "medium", "low"
    source_method: str  # "inline-xbrl"
    section: str | None = None  # e.g., "Item 8"

@dataclass
class XbrlContext:
    """Represents an XBRL context parsed from the filing."""
    id: str
    type: str  # "instant" or "duration"
    period: str  # ISO date or date range string
    dims: Dict[str, str] = field(default_factory=dict)
    
    @property
    def end_date(self) -> str:
        """Extract the end date for sorting columns."""
        if self.type == "instant":
            return self.period
        # For duration "YYYY-MM-DD/YYYY-MM-DD", take the second part
        return self.period.split("/")[-1] if "/" in self.period else self.period

# Configuration for different financial statements
TABLE_CONFIGS = {
    "balance_sheet": {
        "section": "Item 8",
        "description": "Consolidated Balance Sheet",
        # Map simple internal names to possible XBRL tags (list allows fallback)
        "metrics": {
            "Assets": ["us-gaap:Assets"],
            "Current Assets": ["us-gaap:AssetsCurrent"],
            "Cash & Equivalents": ["us-gaap:CashAndCashEquivalentsAtCarryingValue"],
            "Accounts Receivable": ["us-gaap:AccountsReceivableNetCurrent"],
            "Inventory": ["us-gaap:InventoryNet"],
            "Non-Current Assets": ["us-gaap:AssetsNoncurrent"],
            "Liabilities": ["us-gaap:Liabilities"],
            "Current Liabilities": ["us-gaap:LiabilitiesCurrent"],
            "Accounts Payable": ["us-gaap:AccountsPayableCurrent"],
            "Non-Current Liabilities": ["us-gaap:LiabilitiesNoncurrent"],
            "Stockholders Equity": ["us-gaap:StockholdersEquity", "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
        },
        "metric_order": [
            "Current Assets", "Cash & Equivalents", "Accounts Receivable", "Inventory",
            "Non-Current Assets", "Assets",
            "Current Liabilities", "Accounts Payable",
            "Non-Current Liabilities", "Liabilities",
            "Stockholders Equity"
        ],
        "context_type": "instant"
    },
    "income_statement": {
        "section": "Item 8",
        "description": "Consolidated Statement of Operations",
        "metrics": {
            "Revenue": ["us-gaap:Revenues", "us-gaap:SalesRevenueNet", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"],
            "Cost of Revenue": ["us-gaap:CostOfRevenue", "us-gaap:CostOfGoodsAndServicesSold"],
            "Gross Profit": ["us-gaap:GrossProfit"],
            "Operating Expenses": ["us-gaap:OperatingExpenses"],
            "R&D": ["us-gaap:ResearchAndDevelopmentExpense"],
            "SG&A": ["us-gaap:SellingGeneralAndAdministrativeExpense"],
            "Operating Income": ["us-gaap:OperatingIncomeLoss"],
            "Net Income": ["us-gaap:NetIncomeLoss"]
        },
        "metric_order": [
            "Revenue", "Cost of Revenue", "Gross Profit",
            "Operating Expenses", "R&D", "SG&A",
            "Operating Income", "Net Income"
        ],
        "context_type": "duration"
    },
    "cash_flow": {
        "section": "Item 8",
        "description": "Consolidated Statement of Cash Flows",
        "metrics": {
            "Net Cash from Operating": ["us-gaap:NetCashProvidedByUsedInOperatingActivities"],
            "Depreciation & Amortization": ["us-gaap:DepreciationDepletionAndAmortization"],
            "Net Cash from Investing": ["us-gaap:NetCashProvidedByUsedInInvestingActivities"],
            "CapEx": ["us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"],
            "Net Cash from Financing": ["us-gaap:NetCashProvidedByUsedInFinancingActivities"],
            "Dividends Paid": ["us-gaap:PaymentsOfDividends"],
            "Repurchases of Equity": ["us-gaap:PaymentsForRepurchaseOfCommonStock"]
        },
        "metric_order": [
            "Net Cash from Operating", "Depreciation & Amortization",
            "Net Cash from Investing", "CapEx",
            "Net Cash from Financing", "Dividends Paid", "Repurchases of Equity"
        ],
        "context_type": "duration"
    },
    "segment_information": {
        "section": "Item 8",
        "description": "Segment Operating Performance",
        "metrics": {
            "Net Sales": ["us-gaap:Revenues", "us-gaap:SalesRevenueNet"],
            "Operating Income": ["us-gaap:OperatingIncomeLoss"]
        },
        "metric_order": ["Net Sales", "Operating Income"],
        "context_type": "duration"
    }
}

class TableParser:
    """Production table parser using inline XBRL extraction."""

    def _parse_contexts(self, soup: BeautifulSoup) -> Dict[str, XbrlContext]:
        """Parse all context definitions from the XBRL hidden section."""
        contexts = {}
        
        # In Inline XBRL, contexts are often in <ix:resources> or just hidden <xbrli:context> tags
        context_tags = soup.find_all(lambda tag: tag.name and tag.name.lower().endswith("context"))
        
        for ctx in context_tags:
            c_id = ctx.get("id")
            if not c_id:
                continue
                
            # Parse Period
            # Use lower() for tag name checks to be safe with different parsers (lxml html vs xml)
            period_tag = ctx.find(lambda t: t.name and t.name.lower().endswith("period"))
            if not period_tag:
                continue
                
            c_type = "unknown"
            c_period = ""
            
            instant = period_tag.find(lambda t: t.name and t.name.lower().endswith("instant"))
            start_date = period_tag.find(lambda t: t.name and t.name.lower().endswith("startdate"))
            end_date = period_tag.find(lambda t: t.name and t.name.lower().endswith("enddate"))
            
            if instant:
                c_type = "instant"
                c_period = instant.get_text(strip=True)
            elif start_date and end_date:
                c_type = "duration"
                s = start_date.get_text(strip=True)
                e = end_date.get_text(strip=True)
                c_period = f"{s}/{e}"
            else:
                continue
            
            # Parse Dimensions
            dims = {}
            members = ctx.find_all(lambda t: t.name and t.name.lower().endswith("explicitmember"))
            for m in members:
                dim_name = m.get("dimension")
                mem_val = m.get_text(strip=True)
                if dim_name and mem_val:
                    clean_dim = dim_name.split(":")[-1]
                    clean_mem = mem_val.split(":")[-1]
                    dims[clean_dim] = clean_mem
            
            contexts[c_id] = XbrlContext(id=c_id, type=c_type, period=c_period, dims=dims)
            
        return contexts

    def parse_from_html(self, html_content: str, filing_info: dict, table_identifier: str = "balance_sheet") -> ParsedTable:
        """Parse table from HTML using inline XBRL tags."""
        soup = BeautifulSoup(html_content, "lxml")
        
        # 1. Parse Contexts
        contexts = self._parse_contexts(soup)
        
        # 2. Get Configuration
        table_config = TABLE_CONFIGS.get(table_identifier)
        section = table_config.get("section", "Item 8") if table_config else "Item 8"
        
        year_str = f" {filing_info.get('year')}" if filing_info.get('year') else ""
        base_citation = f"[{filing_info.get('ticker')} {filing_info.get('form_type')}{year_str}, {section}]"
        
        if not table_config:
            return ParsedTable("", [], base_citation, "low", "inline-xbrl", section)
            
        req_context_type = table_config["context_type"]
        target_metrics = table_config["metrics"]
        
        # 3. Find XBRL Non-Fraction tags
        xbrl_tags = soup.find_all(lambda t: t.name and t.name.endswith("nonfraction"))
        
        data_rows = []
        
        for tag in xbrl_tags:
            c_ref = tag.get("contextref")
            ctx = contexts.get(c_ref)
            if not ctx:
                continue
                
            if ctx.type != req_context_type:
                continue
                
            # Filter Strategy: 
            # For primary statements, allow NO dimensions OR common defaults.
            # For segment info, require matching dimensions logic (simplified here).
            is_segment_request = (table_identifier == "segment_information")
            has_dimensions = bool(ctx.dims)
            
            if not is_segment_request and has_dimensions:
                continue
            
            # Identify Metric
            tag_name = tag.get("name", "")
            if not tag_name:
                continue
            
            mapped_metric_name = None
            for display_name, valid_tags in target_metrics.items():
                if tag_name in valid_tags or any(tag_name.endswith(":" + vt.split(":")[-1]) for vt in valid_tags):
                    mapped_metric_name = display_name
                    break
            
            if not mapped_metric_name:
                continue
                
            # Extract Value
            text_val = tag.get_text(strip=True)
            if not text_val:
                continue
                
            try:
                sign = 1
                if tag.get("sign") == "-":
                    sign = -1
                
                clean_val_str = text_val.replace(",", "").replace("(", "").replace(")", "")
                val = float(clean_val_str) * sign
                
                if "(" in text_val and sign == 1:
                    val = -abs(val)
                    
            except ValueError:
                continue
            
            # Store Row
            data_rows.append({
                "Metric": mapped_metric_name,
                "Period": ctx.end_date, 
                "Value": val
            })
            
        # 4. Construct DataFrame
        if not data_rows:
             return ParsedTable("", [], base_citation, "low", "inline-xbrl", section)
             
        df = pd.DataFrame(data_rows)
        # Drop duplicates, keep last or first? First roughly fine.
        df = df.drop_duplicates(subset=["Metric", "Period"])
        
        # 5. Pivot
        pivot = df.pivot(index="Metric", columns="Period", values="Value")
        
        # 6. Formatting & Sorts
        sorted_cols = sorted(pivot.columns, reverse=True)
        pivot = pivot[sorted_cols]
        
        defined_order = table_config.get("metric_order", [])
        pivot["_sort_key"] = pivot.index.map(lambda x: defined_order.index(x) if x in defined_order else 999)
        pivot = pivot.sort_values("_sort_key")
        pivot = pivot.drop(columns=["_sort_key"])
        
        def fmt_money(x):
            if pd.isna(x): return ""
            return f"{x:,.0f}"
            
        markdown = pivot.map(fmt_money).to_markdown()
        structured = df.to_dict("records")
        
        return ParsedTable(
            markdown=markdown,
            structured=structured,
            citation=base_citation,
            confidence="high",
            source_method="inline-xbrl",
            section=section
        )

    def parse_from_filing(
        self,
        ticker: str,
        form_type: str,
        table_identifier: str,
        year: int | None = None
    ) -> ParsedTable:
        """High-level interface: fetch filing and parse table."""
        company = Company(ticker)
        filings = company.get_filings(form=form_type)

        if not filings:
             raise ValueError(f"No {form_type} filings found for {ticker}")

        selected_filing = None
        if year:
            for f in filings:
                if f.filing_date.year == year:
                    selected_filing = f
                    break
            if not selected_filing:
                 raise ValueError(f"No {form_type} filing found for {ticker} in {year}")
        else:
            selected_filing = filings[0]

        html_content = selected_filing.html()
        if not html_content:
            raise ValueError("Could not retrieve HTML content from filing")

        return self.parse_from_html(
            html_content,
            {
                "ticker": ticker,
                "form_type": form_type,
                "year": selected_filing.filing_date.year
            },
            table_identifier=table_identifier
        )
