import { ExternalLink } from 'lucide-react';

interface CitationLinkProps {
  url: string;
  text?: string;
}

export function CitationLink({ url, text }: CitationLinkProps) {
  return (
    <a 
      href={url} 
      target="_blank" 
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline decoration-blue-500/30 font-medium transition-colors"
    >
      {text || 'View Source'}
      <ExternalLink className="w-3 h-3" />
    </a>
  );
}
