import { QueryInput } from './components/QueryInput';
import { WorkflowTimeline } from './components/WorkflowTimeline';
import { ResponsePanel } from './components/ResponsePanel';
import { useQuery } from './hooks/useQuery';
import { Layout } from 'lucide-react';

function App() {
  const {
    submitQuery,
    events,
    isProcessing,
  } = useQuery();

  // Extract final answer from events if available
  const completionEvent = events.find(e => e.phase === 'complete');
  const finalAnswer = completionEvent ? completionEvent.message : null;
  
  // Or maybe synthesis event has partial? For now use completion.
  
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
                <div className="text-sm text-gray-500">
                    v0.1.0-alpha
                </div>
            </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8 max-w-7xl">
            {/* Search Section */}
            <div className="mb-12 text-center space-y-4">
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl text-gray-100">
                    Autonomous Financial Research
                </h2>
                <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
                    Ask complex questions about public companies. The agent plans, executes tools, and validates results in real-time.
                </p>
                <QueryInput onSubmit={submitQuery} isLoading={isProcessing} />
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
        </main>
    </div>
  );
}

export default App;
