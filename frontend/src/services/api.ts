
export interface TableParseRequest {
  ticker: string;
  form_type: string;
  year: number;
  table_name: string;
}

export interface ParsedTableResponse {
  markdown: string;
  structured: any[];
  citation: string;
  confidence: string;
  metadata: {
    source_method: string;
    ticker: string;
    form_type: string;
    year: number;
  };
}

export interface FilingResponse {
  ticker: string;
  form_type: string;
  filing_date: string;
  accession_no: string;
  url: string;
  citation: string;
  sections_available: string[];
}

export const SecClient = {
  async parseTable(request: TableParseRequest): Promise<ParsedTableResponse> {
    const res = await fetch('/api/v1/tables/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to parse table');
    }

    return res.json();
  },

  async getFiling(ticker: string, formType: string, year?: number): Promise<FilingResponse> {
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());

    const res = await fetch(`/api/v1/filings/${ticker}/${formType}?${params.toString()}`);

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to fetch filing');
    }

    return res.json();
  }
};
