export type WorkflowNodeType =
  | 'trigger'
  | 'action'
  | 'condition'
  | 'switch'
  | 'think'
  | 'transform'
  | 'filter'
  | 'delay'
  | 'loop'
  | 'merge'
  | 'parallel'
  | 'aggregate'
  | 'http_request'
  | 'set_variable'
  | 'response';

export interface WorkflowNodePosition {
  x: number;
  y: number;
}

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  label: string;
  position: WorkflowNodePosition;
  config: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle: string;
  label: string;
}

export interface WorkflowVariable {
  default?: unknown;
  type?: string;
  description?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  is_enabled: boolean;
  version: number;
  trigger_connector: string | null;
  trigger_event: string | null;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  variables: Record<string, WorkflowVariable>;
  on_error: string;
  max_retries: number;
  timeout_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowCreateRequest {
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  variables?: Record<string, unknown>;
  on_error?: string;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
  variables?: Record<string, unknown>;
  is_enabled?: boolean;
  on_error?: string;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface WorkflowNodeResult {
  node_id: string;
  node_type: string;
  label: string;
  status: 'success' | 'failed' | 'filtered' | 'running';
  output?: unknown;
  error?: string;
  duration_ms?: number;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'running' | 'success' | 'failed';
  trigger_data: Record<string, unknown>;
  node_results: WorkflowNodeResult[];
  context_snapshot: Record<string, unknown>;
  error: string | null;
  error_node_id: string | null;
  duration_ms: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface ConditionRule {
  field: string;
  field_custom?: string;
  operator:
    | 'eq'
    | 'neq'
    | 'gt'
    | 'lt'
    | 'gte'
    | 'lte'
    | 'contains'
    | 'not_contains'
    | 'starts_with'
    | 'ends_with'
    | 'exists'
    | 'not_exists'
    | 'in'
    | 'not_in'
    | 'regex'
    | 'is_empty'
    | 'is_not_empty';
  value?: unknown;
}

export interface TransformStep {
  type: string;
  [key: string]: unknown;
}

export interface FieldMapping {
  from: string;
  to: string;
  from_custom?: string;
  to_custom?: string;
  sources?: string[];
  transform?: TransformStep | TransformStep[];
}

export interface NodeTypeDefinition {
  type: WorkflowNodeType;
  label: string;
  icon: string;
  color: string;
  category: 'trigger' | 'logic' | 'action' | 'data' | 'flow';
  handles: {
    inputs: string[];
    outputs: string[];
  };
  description: string;
}

export const NODE_TYPE_DEFINITIONS: NodeTypeDefinition[] = [
  {
    type: 'trigger',
    label: 'Trigger',
    icon: 'bolt',
    color: '#4caf50',
    category: 'trigger',
    handles: { inputs: [], outputs: ['default'] },
    description: 'Starting point — listens for a connector event',
  },
  {
    type: 'action',
    label: 'Action',
    icon: 'play_arrow',
    color: '#2196f3',
    category: 'action',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Execute an action on a connector',
  },
  {
    type: 'condition',
    label: 'Condition',
    icon: 'call_split',
    color: '#ff9800',
    category: 'logic',
    handles: { inputs: ['default'], outputs: ['true', 'false'] },
    description: 'If/else branching based on data conditions',
  },
  {
    type: 'switch',
    label: 'Switch',
    icon: 'account_tree',
    color: '#ff5722',
    category: 'logic',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Multi-branch routing based on field value',
  },
  {
    type: 'transform',
    label: 'Transform',
    icon: 'transform',
    color: '#9c27b0',
    category: 'data',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Map and transform data fields',
  },
  {
    type: 'filter',
    label: 'Filter',
    icon: 'filter_alt',
    color: '#795548',
    category: 'logic',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Pass data through only if conditions are met',
  },
  {
    type: 'think',
    label: 'Think (AI)',
    icon: 'psychology',
    color: '#6a1b9a',
    category: 'logic',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'AI Agent — analyze data with a prompt and get structured results',
  },
  {
    type: 'delay',
    label: 'Delay',
    icon: 'hourglass_empty',
    color: '#607d8b',
    category: 'flow',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Wait for a specified duration',
  },
  {
    type: 'loop',
    label: 'Loop',
    icon: 'loop',
    color: '#009688',
    category: 'flow',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Iterate over an array in the data',
  },
  {
    type: 'merge',
    label: 'Merge',
    icon: 'call_merge',
    color: '#3f51b5',
    category: 'flow',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Merge multiple branches together',
  },
  {
    type: 'parallel',
    label: 'Parallel',
    icon: 'fork_right',
    color: '#ff6f00',
    category: 'flow',
    handles: { inputs: ['default'], outputs: ['branch', 'done'] },
    description:
      'Execute multiple branches in parallel (scatter-gather) and collect results. Use "branch" handle for parallel branches, "done" for continuation.',
  },
  {
    type: 'aggregate',
    label: 'Aggregate',
    icon: 'compare_arrows',
    color: '#1b5e20',
    category: 'data',
    handles: { inputs: ['default'], outputs: ['default'] },
    description:
      'Aggregate parallel results — find cheapest, most expensive, or concatenate',
  },
  {
    type: 'http_request',
    label: 'HTTP Request',
    icon: 'http',
    color: '#e91e63',
    category: 'action',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Make an arbitrary HTTP call',
  },
  {
    type: 'set_variable',
    label: 'Set Variable',
    icon: 'data_object',
    color: '#00bcd4',
    category: 'data',
    handles: { inputs: ['default'], outputs: ['default'] },
    description: 'Set a variable in the workflow context',
  },
  {
    type: 'response',
    label: 'Response',
    icon: 'output',
    color: '#f44336',
    category: 'flow',
    handles: { inputs: ['default'], outputs: [] },
    description: 'End the workflow and return a response',
  },
];

export const CONDITION_OPERATORS = [
  { value: 'eq', label: 'equals (==)' },
  { value: 'neq', label: 'not equals (!=)' },
  { value: 'gt', label: 'greater than (>)' },
  { value: 'lt', label: 'less than (<)' },
  { value: 'gte', label: 'greater or equal (>=)' },
  { value: 'lte', label: 'less or equal (<=)' },
  { value: 'contains', label: 'contains' },
  { value: 'not_contains', label: 'does not contain' },
  { value: 'starts_with', label: 'starts with' },
  { value: 'ends_with', label: 'ends with' },
  { value: 'exists', label: 'exists (not null)' },
  { value: 'not_exists', label: 'is null' },
  { value: 'in', label: 'in list' },
  { value: 'not_in', label: 'not in list' },
  { value: 'regex', label: 'matches regex' },
  { value: 'is_empty', label: 'is empty' },
  { value: 'is_not_empty', label: 'is not empty' },
];

export interface TransformTypeDef {
  value: string;
  label: string;
  multiSource?: boolean;
  configFields?: string[];
}

export const TRANSFORM_TYPES: TransformTypeDef[] = [
  { value: 'template', label: 'Template', multiSource: true, configFields: ['template'] },
  { value: 'join', label: 'Join', multiSource: true, configFields: ['separator'] },
  { value: 'coalesce', label: 'Coalesce (first non-null)', multiSource: true, configFields: ['default_value'] },
  { value: 'regex_extract', label: 'Regex Extract', configFields: ['pattern', 'group'] },
  { value: 'regex_replace', label: 'Regex Replace', configFields: ['pattern', 'replacement'] },
  { value: 'map', label: 'Value Map', configFields: ['values'] },
  { value: 'lookup', label: 'Lookup Table', configFields: ['table', 'default'] },
  { value: 'format', label: 'Format Template', configFields: ['template'] },
  { value: 'uppercase', label: 'UPPERCASE' },
  { value: 'lowercase', label: 'lowercase' },
  { value: 'trim', label: 'Trim Whitespace' },
  { value: 'replace', label: 'Replace Text', configFields: ['old', 'new'] },
  { value: 'split', label: 'Split String', configFields: ['separator'] },
  { value: 'concat', label: 'Concatenate', configFields: ['separator', 'parts'] },
  { value: 'substring', label: 'Substring', configFields: ['start', 'end'] },
  { value: 'date_format', label: 'Date Format', configFields: ['input_format', 'output_format'] },
  { value: 'math', label: 'Math Operation', configFields: ['operation', 'operand'] },
  { value: 'prepend', label: 'Prepend', configFields: ['value'] },
  { value: 'append', label: 'Append', configFields: ['value'] },
  { value: 'to_int', label: 'To Integer' },
  { value: 'to_float', label: 'To Float' },
  { value: 'to_string', label: 'To String' },
  { value: 'default', label: 'Default Value', configFields: ['default_value'] },
];

export type AiModelType = 'gemini' | 'opus';

export interface AiChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AiGenerateRequest {
  prompt: string;
  model: AiModelType;
  api_key: string;
  conversation: AiChatMessage[];
  current_nodes: Record<string, unknown>[];
  current_edges: Record<string, unknown>[];
  connectors: Record<string, unknown>[];
}

export interface AiGenerateResponse {
  message: string;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
  name?: string;
  description?: string;
}

export const AI_MODELS = [
  { value: 'gemini' as AiModelType, label: 'Google Gemini 2.5 Flash' },
  { value: 'opus' as AiModelType, label: 'Anthropic Claude Opus 4.6' },
];
