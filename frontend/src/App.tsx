
import { QueryInput } from './components/QueryInput';
import { WorkflowTimeline } from './components/WorkflowTimeline';
import { ResponsePanel } from './components/ResponsePanel';
import { QueryHistory } from './components/QueryHistory';
import { TableParser } from './components/TableParser';
import { useQuery } from './hooks/useQuery';
import { useQueryHistory } from './hooks/useQueryHistory';
import { Layout, History as HistoryIcon, Table as TableIcon, MessageSquare } from 'lucide-react';
import { useEffect, useState } from 'react';

function App() {
  const {
    submitQuery,
    events,
    isProcessing,
    reset,
    queryId,
    query
  } = useQuery();

  const { history, addToHistory, clearHistory } = useQueryHistory();
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'tables'>('chat');

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
    <div className="min-h-screen bg-gray-950 text-white font-sans selection:bg-blue-500/30">
        {/* Header */}
        <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-600 p-2 rounded-lg">
                        <Layout className="w-5 h-5 text-white" />
                    </div>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        SEC Edgar Agent
                    </h1>
                </div>

                {/* Navigation Tabs */}
                <div className="flex items-center bg-gray-900 border border-gray-800 rounded-lg p-1">
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
        <main className="container mx-auto px-4 py-8 max-w-7xl relative">
            
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
                    <div className="mb-12 text-center space-y-4">
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl text-gray-100">
                            Autonomous Financial Research
                        </h2>
                        <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
                            Ask complex questions about public companies. The agent plans, executes tools, and validates results in real-time.
                        </p>
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
                                <WorkflowTimeline events={events} />
                            </div>
                        </div>

                        {/* Right: Response Area */}
                        <div className="lg:col-span-8">
                            <div className="bg-gray-900/50 rounded-xl border border-gray-800 min-h-[600px] h-full"> 
                                <ResponsePanel content={finalAnswer} isProcessing={isProcessing} />
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <TableParser />
            )}
        </main>
    </div>
  );
}

export default App;
