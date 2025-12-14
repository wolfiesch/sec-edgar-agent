
import { QueryInput } from './components/QueryInput';
import { WorkflowTimeline } from './components/WorkflowTimeline';
import { ResponsePanel } from './components/ResponsePanel';
import { QueryHistory } from './components/QueryHistory';
import { TableParser } from './components/TableParser';
import { SemanticSearch } from './components/SemanticSearch';
import { QuickActions } from './components/QuickActions';
import { CompareCompanies } from './components/CompareCompanies';
import { FilingDiff } from './components/FilingDiff';
import { ToastContainer, useToast } from './components/Toast';
import { useQuery } from './hooks/useQuery';
import { useQueryHistory } from './hooks/useQueryHistory';
import { Layout, History as HistoryIcon, Table as TableIcon, MessageSquare, Search, GitCompare, FileSearch } from 'lucide-react';
import { useEffect, useState } from 'react';

function App() {
  const {
    submitQuery,
    events,
    isProcessing,
    reset,
    queryId,
    query,
    connectionStatus
  } = useQuery();

  const { history, addToHistory, clearHistory } = useQueryHistory();
  const { toasts, dismissToast, success, error, info } = useToast();
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'tables' | 'search' | 'compare' | 'changes'>('chat');

  const handleToast = (type: 'success' | 'error' | 'info', message: string) => {
    if (type === 'success') success(message);
    else if (type === 'error') error(message);
    else info(message);
  };

  // Auto-save history when queryId is generated
  useEffect(() => {
    if (queryId && query) {
      addToHistory(query, queryId);
    }
  }, [queryId, query, addToHistory]);

  const handleQuerySubmit = (q: string) => {
      submitQuery(q);
      setShowHistory(false);
  };

  // Extract final answer from events if available
  const completionEvent = events.find(e => e.phase === 'complete');
  const finalAnswer = completionEvent ? completionEvent.message : null;
  const hasResult = events.length > 0;
  
  return (
    <div className="min-h-screen bg-[rgb(var(--bg-dark))] text-[rgb(var(--text-main))] font-sans selection:bg-sky-500/30">
        {/* Header */}
        <header className="border-b border-slate-800/60 bg-[rgb(var(--bg-dark))]/80 backdrop-blur-md sticky top-0 z-50">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="bg-gradient-to-br from-sky-500 to-blue-600 p-2.5 rounded-xl shadow-lg shadow-sky-500/20">
                        <Layout className="w-5 h-5 text-white" />
                    </div>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-emerald-400 tracking-tight">
                        SEC Edgar Agent
                    </h1>
                </div>

                {/* Navigation Tabs */}
                <div className="flex items-center bg-slate-900/50 border border-slate-800 rounded-xl p-1.5 backdrop-blur-sm">
                    <button
                        onClick={() => setActiveTab('chat')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                            activeTab === 'chat' 
                                ? 'bg-gray-800 text-white shadow-sm' 
                                : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <MessageSquare className="w-4 h-4" />
                        Agent Chat
                    </button>
                    <button
                        onClick={() => setActiveTab('tables')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                            activeTab === 'tables'
                                ? 'bg-gray-800 text-white shadow-sm'
                                : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <TableIcon className="w-4 h-4" />
                        Table Parser
                    </button>
                    <button
                        onClick={() => setActiveTab('search')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                            activeTab === 'search'
                                ? 'bg-gray-800 text-white shadow-sm'
                                : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <Search className="w-4 h-4" />
                        Semantic Search
                    </button>
                    <button
                        onClick={() => setActiveTab('compare')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                            activeTab === 'compare'
                                ? 'bg-gray-800 text-white shadow-sm'
                                : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <GitCompare className="w-4 h-4" />
                        Compare
                    </button>
                    <button
                        onClick={() => setActiveTab('changes')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                            activeTab === 'changes'
                                ? 'bg-gray-800 text-white shadow-sm'
                                : 'text-gray-400 hover:text-gray-200'
                        }`}
                    >
                        <FileSearch className="w-4 h-4" />
                        Changes
                    </button>
                </div>

                <div className="flex items-center gap-4 text-sm">
                    {activeTab === 'chat' && (
                        <button 
                            onClick={() => setShowHistory(!showHistory)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${showHistory ? 'bg-gray-800 text-blue-400' : 'text-gray-400 hover:text-gray-200'}`}
                        >
                            <HistoryIcon className="w-4 h-4" />
                            <span className="hidden sm:inline">History</span>
                        </button>
                    )}
                    <div className="text-gray-500">v0.1.0</div>
                </div>
            </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8 max-w-[1600px] relative">
            
            {activeTab === 'chat' ? (
                <>
                    {/* History Dropdown */}
                    {showHistory && (
                        <div className="absolute top-0 right-4 z-20 w-80 shadow-2xl animate-in fade-in slide-in-from-top-2">
                            <QueryHistory 
                                history={history} 
                                onSelect={handleQuerySubmit} 
                                onClear={clearHistory} 
                            />
                        </div>
                    )}

                    {/* Search Section */}
                    <div className="mb-12 text-center space-y-6">
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl text-gray-100">
                            Autonomous Financial Research
                        </h2>
                        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
                            Ask complex questions about public companies. The agent plans, executes tools, and validates results in real-time.
                        </p>

                        {/* Quick Actions - Only show when no result */}
                        {!hasResult && !isProcessing && (
                            <QuickActions
                                onSubmit={handleQuerySubmit}
                                isLoading={isProcessing}
                            />
                        )}

                        <QueryInput
                            onSubmit={handleQuerySubmit}
                            isLoading={isProcessing}
                            onReset={reset}
                            hasResult={hasResult}
                        />
                    </div>

                    {/* Workspace Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                        {/* Left: Workflow Feed */}
                        <div className="lg:col-span-4 space-y-6">
                            <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-4 h-[600px] overflow-y-auto custom-scrollbar">
                                <WorkflowTimeline
                                    events={events}
                                    connectionStatus={connectionStatus as 'disconnected' | 'connecting' | 'connected' | 'error'}
                                />
                            </div>
                        </div>

                        {/* Right: Response Area */}
                        <div className="lg:col-span-8">
                            <div className="bg-gray-900/50 rounded-xl border border-gray-800 min-h-[600px] h-full"> 
                                <ResponsePanel content={finalAnswer} isProcessing={isProcessing} onToast={handleToast} />
                            </div>
                        </div>
                    </div>
                </>
            ) : activeTab === 'tables' ? (
                <TableParser />
            ) : activeTab === 'search' ? (
                <SemanticSearch />
            ) : activeTab === 'compare' ? (
                <CompareCompanies onToast={handleToast} />
            ) : (
                <FilingDiff onToast={handleToast} />
            )}
        </main>

        {/* Toast Notifications */}
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

export default App;
