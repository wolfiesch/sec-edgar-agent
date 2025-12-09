export interface QueryResponse {
  query_id: string;
  status: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface ToolExecutionResult {
  success: boolean;
  result: any; // Ideally more specific
  error?: string;
  citations: string[];
}

export type WorkflowPhase = 
  | 'planning' 
  | 'executing' 
  | 'validating' 
  | 'synthesizing' 
  | 'complete' 
  | 'error';

export interface WorkflowEvent {
  phase: WorkflowPhase;
  message: string;
  data: any;
  timestamp: string;
}

export interface Task {
  id: string;
  description: string;
  tool?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
}

export interface Plan {
  original_query: string;
  tasks: Task[];
  is_simple: boolean;
}
