import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ResponsePanelProps {
  content: string | null;
  isProcessing: boolean;
}

export function ResponsePanel({ content, isProcessing }: ResponsePanelProps) {
  if (!content) {
      if (isProcessing) {
          return (
              <div className="h-full flex items-center justify-center text-gray-500 animate-pulse">
                  Wait for it...
              </div>
          );
      }
      return (
          <div className="h-full flex items-center justify-center text-gray-500">
              Ready to research.
          </div>
      );
  }

  return (
    <div className="prose prose-invert max-w-none p-6 bg-gray-800/50 rounded-lg border border-gray-700 shadow-md">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
