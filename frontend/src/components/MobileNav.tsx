import { X, MessageSquare, Table, Search, GitCompare, FileSearch } from 'lucide-react';
import { useEffect } from 'react';

interface MobileNavProps {
  activeTab: 'chat' | 'tables' | 'search' | 'compare' | 'changes';
  setActiveTab: (tab: 'chat' | 'tables' | 'search' | 'compare' | 'changes') => void;
  isOpen: boolean;
  onClose: () => void;
}

export function MobileNav({ activeTab, setActiveTab, isOpen, onClose }: MobileNavProps) {
  // Prevent scrolling when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const navItems = [
    { id: 'chat', label: 'Agent Chat', icon: MessageSquare },
    { id: 'tables', label: 'Table Parser', icon: Table },
    { id: 'search', label: 'Semantic Search', icon: Search },
    { id: 'compare', label: 'Compare Companies', icon: GitCompare },
    { id: 'changes', label: 'Filing Changes', icon: FileSearch },
  ] as const;

  return (
    <div className="fixed inset-0 z-[100] md:hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="absolute right-0 top-0 bottom-0 w-[280px] bg-slate-950 border-l border-slate-800 shadow-2xl animate-in slide-in-from-right duration-300">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-800">
            <h2 className="text-lg font-semibold text-slate-100">Menu</h2>
            <button 
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Nav Items */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  onClose();
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  activeTab === item.id
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-slate-800">
            <div className="text-xs text-slate-500 text-center">
              SEC Edgar Agent v0.1.0
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
