# SEC EDGAR Agent - React Frontend Implementation Plan

**Created**: 12/09/2025 01:15 PM PST (via pst-timestamp)
**Status**: Draft - Awaiting Approval
**Estimated Effort**: Medium complexity, incremental delivery possible

---

## Executive Summary

Wrap the existing CLI in a minimal React frontend to provide visual feedback on:
- Query execution workflow (planning → executing → synthesizing)
- Tool calls and their results
- Final responses with proper formatting
- Citations linked to SEC filings

The approach prioritizes **visibility into what's happening** over feature completeness.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React Frontend                               │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Query   │  │   Workflow    │  │    Tool      │  │  Response │  │
│  │  Input   │  │   Timeline    │  │   Viewer     │  │   Panel   │  │
│  └──────────┘  └───────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket / SSE
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (New)                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  /api/query (POST)       - Start new query                    │   │
│  │  /api/query/stream (WS)  - Stream progress updates            │   │
│  │  /api/tools (GET)        - List available tools               │   │
│  │  /api/tools/{name} (POST)- Execute single tool                │   │
│  │  /api/company/{ticker}   - Quick company lookup               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Python calls
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Existing Agent System (Unchanged)                   │
│  StreamingOrchestrator → Planner → Executor → Validator → Response  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: FastAPI Backend Layer
**Goal**: Create API that wraps existing orchestrator with streaming support

#### Tasks:
1. **Create FastAPI app structure**
   - `src/api/main.py` - FastAPI app with CORS
   - `src/api/routes/` - Route modules
   - `src/api/models.py` - Pydantic request/response models

2. **Implement core endpoints**
   ```python
   POST /api/query
   # Request: {"query": "What's Apple's revenue?"}
   # Response: {"query_id": "uuid", "status": "started"}

   WS /api/query/{query_id}/stream
   # Streams: {"phase": "planning", "message": "...", "data": {...}}

   GET /api/tools
   # Response: [{"name": "get_company_info", "description": "...", "parameters": {...}}]

   POST /api/tools/{tool_name}
   # Request: {"ticker": "AAPL"}
   # Response: {"success": true, "result": {...}, "citations": [...]}
   ```

3. **Wrap StreamingOrchestrator**
   - Convert generator to async WebSocket messages
   - Add query session management
   - Include timing metadata in each message

4. **Add convenience endpoints**
   - `GET /api/company/{ticker}` - Quick lookup
   - `GET /api/filings/{ticker}` - Filing list
   - `GET /api/health` - Health check

#### Deliverables:
- `src/api/` directory with FastAPI implementation
- Can run with `uvicorn src.api.main:app`
- OpenAPI docs at `/docs`

---

### Phase 2: React App Scaffolding
**Goal**: Minimal React app that can communicate with backend

#### Tasks:
1. **Initialize React project**
   - Use Vite for fast development
   - TypeScript for type safety
   - Tailwind CSS for rapid styling
   - Location: `frontend/` directory

2. **Project structure**
   ```
   frontend/
   ├── src/
   │   ├── components/
   │   │   ├── QueryInput.tsx
   │   │   ├── WorkflowTimeline.tsx
   │   │   ├── ToolResultCard.tsx
   │   │   ├── ResponsePanel.tsx
   │   │   └── CitationLink.tsx
   │   ├── hooks/
   │   │   ├── useQuery.ts
   │   │   └── useWebSocket.ts
   │   ├── types/
   │   │   └── index.ts
   │   ├── App.tsx
   │   └── main.tsx
   ├── package.json
   └── vite.config.ts
   ```

3. **Core hooks**
   - `useWebSocket(queryId)` - Connect to streaming endpoint
   - `useQuery()` - Submit queries and track state

4. **Basic layout**
   - Single page with query input at top
   - Main area split: timeline left, results right

#### Deliverables:
- Working React app skeleton
- Can connect to backend
- Displays raw JSON from API

---

### Phase 3: Workflow Visualization
**Goal**: Show real-time progress through agent workflow

#### Components:

1. **WorkflowTimeline**
   ```tsx
   // Visual phases: Planning → Executing → Validating → Complete
   // Each phase shows:
   // - Status icon (spinner/check/error)
   // - Phase name
   // - Elapsed time
   // - Expandable details
   ```

2. **TaskList**
   ```tsx
   // Shows planned tasks from planner agent
   // Each task:
   // - Description
   // - Suggested tool
   // - Status (pending/running/done)
   // - Result preview when complete
   ```

3. **ToolExecutionCard**
   ```tsx
   // When a tool runs, show:
   // - Tool name with icon
   // - Input parameters (formatted JSON)
   // - Execution time
   // - Success/failure status
   // - Collapsible result preview
   ```

4. **Phase transitions**
   - Animate between phases
   - Show cumulative elapsed time
   - Highlight current phase

#### Visual Design:
```
┌─────────────────────────────────────────────────────────────────┐
│ [?] What is Apple's revenue growth over the last 3 years?  [Go]│
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────────────────────┐
│ ● Planning     0.8s  │  │ Plan: 3 tasks                        │
│ ◐ Executing    2.1s  │  │                                      │
│ ○ Validating    -    │  │ □ Get Apple revenue (2021-2024)      │
│ ○ Complete      -    │  │   Tool: get_income_statement         │
│                      │  │   Status: Running...                 │
│ Total: 2.9s          │  │                                      │
└──────────────────────┘  │ □ Calculate growth rates              │
                          │   Tool: analyze_historical_trends    │
                          │   Status: Pending                    │
                          │                                      │
                          │ □ Format comparison                   │
                          │   Status: Pending                    │
                          └──────────────────────────────────────┘
```

---

### Phase 4: Response Display
**Goal**: Render final response with rich formatting

#### Components:

1. **ResponsePanel**
   ```tsx
   // Renders markdown response
   // Uses react-markdown with:
   // - GitHub-flavored markdown
   // - Syntax highlighting for code
   // - Table rendering
   // - Custom citation component
   ```

2. **CitationLink**
   ```tsx
   // Parses [AAPL 10-K 2024] format
   // Renders as clickable chip
   // Links to SEC EDGAR filing
   // Tooltip shows full citation details
   ```

3. **DataTable**
   ```tsx
   // For financial data results
   // Sortable columns
   // Highlight key metrics
   // Export to CSV option
   ```

4. **ErrorDisplay**
   ```tsx
   // Friendly error messages
   // Shows which phase failed
   // Retry button
   // Partial results if available
   ```

---

### Phase 5: Quality of Life Features
**Goal**: Make the UI practical for daily use

#### Features:

1. **Query History**
   - Sidebar with recent queries
   - Click to re-run or view results
   - Stored in localStorage

2. **Quick Actions**
   - Buttons for common queries:
     - "Company Overview" - `/company TICKER`
     - "Recent Filings" - `/filings TICKER`
     - "Financials" - `/financials TICKER`
   - Ticker autocomplete

3. **Tool Browser**
   - List all 24 available tools
   - Show tool descriptions and parameters
   - "Try it" button for direct execution

4. **Dark Mode**
   - Toggle in header
   - Persist preference

5. **Export Options**
   - Copy response as markdown
   - Download as PDF
   - Share link (with query params)

---

## Technical Decisions

### Backend: FastAPI
**Why**:
- Async-native (perfect for streaming)
- Built-in WebSocket support
- Auto-generated OpenAPI docs
- Already using Python for agent

### Frontend: React + Vite + Tailwind
**Why**:
- Vite: Fast dev server, instant HMR
- React: Component model fits our UI structure
- Tailwind: Rapid styling without CSS files
- TypeScript: Catch errors early, better DX

### Real-time: WebSockets
**Why**:
- Bi-directional (can send cancel signals)
- Lower overhead than SSE for this use case
- Native browser support

### State Management: React Context + Hooks
**Why**:
- Simple enough for this app size
- No need for Redux/Zustand complexity
- Custom hooks encapsulate WebSocket logic

---

## File Structure (Final)

```
sec-edgar-agent/
├── src/
│   ├── api/                      # NEW: FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   ├── models.py            # Request/response schemas
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── query.py         # /api/query endpoints
│   │   │   ├── tools.py         # /api/tools endpoints
│   │   │   └── company.py       # /api/company endpoints
│   │   └── websocket.py         # WebSocket handler
│   ├── agents/                   # UNCHANGED
│   ├── tools/                    # UNCHANGED
│   ├── data/                     # UNCHANGED
│   ├── utils/                    # UNCHANGED
│   └── main.py                   # CLI (unchanged)
│
├── frontend/                     # NEW: React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── QueryInput.tsx
│   │   │   ├── WorkflowTimeline.tsx
│   │   │   ├── TaskList.tsx
│   │   │   ├── ToolExecutionCard.tsx
│   │   │   ├── ResponsePanel.tsx
│   │   │   ├── CitationLink.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── ErrorDisplay.tsx
│   │   │   ├── QueryHistory.tsx
│   │   │   ├── QuickActions.tsx
│   │   │   └── ToolBrowser.tsx
│   │   ├── hooks/
│   │   │   ├── useQuery.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useQueryHistory.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   └── citations.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── pyproject.toml               # Add fastapi, uvicorn deps
└── README.md                    # Update with frontend instructions
```

---

## Dependencies to Add

### Python (pyproject.toml)
```toml
[project.optional-dependencies]
api = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "websockets>=12.0",
]
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

---

## Running the App

### Development
```bash
# Terminal 1: Backend
uv run uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
# Opens http://localhost:5173
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Serve with FastAPI (static files)
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] FastAPI server starts without errors
- [ ] `/api/tools` returns list of 24 tools
- [ ] `/api/query` starts a query and returns ID
- [ ] WebSocket streams progress for a simple query

### Phase 2 Complete When:
- [ ] React app builds and runs
- [ ] Can submit a query from UI
- [ ] Receives WebSocket updates in console

### Phase 3 Complete When:
- [ ] Timeline shows all phases with timing
- [ ] Tasks are listed as they're planned
- [ ] Tool executions show in real-time

### Phase 4 Complete When:
- [ ] Final response renders as markdown
- [ ] Citations are clickable and link to SEC
- [ ] Tables display properly for financial data

### Phase 5 Complete When:
- [ ] Query history persists across sessions
- [ ] Quick actions work for common operations
- [ ] Dark mode toggle functions

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| WebSocket disconnects | Auto-reconnect with exponential backoff |
| Long-running queries timeout | Add progress heartbeat, show partial results |
| Large responses slow rendering | Virtualize long lists, lazy-load sections |
| SEC rate limits hit | Surface rate limit errors clearly in UI |

---

## Not In Scope (Future)

- User authentication
- Multi-user support
- Query sharing/collaboration
- Mobile-responsive design (desktop-first MVP)
- Offline mode
- Advanced charting for financial data

---

## Change Log

| Timestamp | Change | Notes |
|-----------|--------|-------|
| 12/09/2025 01:15 PM PST | Initial plan created | Awaiting approval |

---

## Questions for User Before Starting

1. **Hosting preference**: Local-only development or deploy somewhere (Vercel/Railway)?
2. **Styling preference**: Any specific design system or colors in mind?
3. **Phase priority**: Which phase is most critical to see first?
