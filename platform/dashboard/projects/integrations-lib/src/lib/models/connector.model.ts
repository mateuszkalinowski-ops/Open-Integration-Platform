export interface ConnectorHealthSummary {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  latency_ms?: number | null;
  last_check?: number | null;
  consecutive_failures: number;
  last_error?: string | null;
  error_rate_5m?: number | null;
}

export interface ConnectorActionMetadata {
  label?: string;
  description?: string;
}

export interface OnPremiseAgentInfo {
  display_name: string;
  description: string;
  source_directory: string;
  platform: string;
  requirements: string[];
  install_steps: string[];
}

export interface Connector {
  name: string;
  category: string;
  version: string;
  display_name: string;
  description: string;
  country: string;
  logo_url: string;
  website_url: string;
  interface: string;
  capabilities: string[];
  events: string[];
  actions: string[];
  action_metadata?: Record<string, ConnectorActionMetadata>;
  config_schema: ConfigSchema;
  api_endpoints: ApiEndpoint[];
  event_fields: Record<string, ConnectorFieldDef[]>;
  action_fields: Record<string, ConnectorFieldDef[]>;
  output_fields: Record<string, ConnectorFieldDef[]>;
  auth_type: string;
  status: 'stable' | 'beta' | 'planned' | string;
  supports_oauth2: boolean;
  sandbox_available: boolean;
  has_webhooks: boolean;
  health?: ConnectorHealthSummary | null;
  deployment: string;
  requires_onpremise_agent: boolean;
  onpremise_agent: OnPremiseAgentInfo | null;
}

export const COUNTRY_FLAG_MAP: Record<string, string> = {
  PL: '\u{1F1F5}\u{1F1F1}',
  DE: '\u{1F1E9}\u{1F1EA}',
  US: '\u{1F1FA}\u{1F1F8}',
  CZ: '\u{1F1E8}\u{1F1FF}',
  NL: '\u{1F1F3}\u{1F1F1}',
  GB: '\u{1F1EC}\u{1F1E7}',
  FR: '\u{1F1EB}\u{1F1F7}',
  ES: '\u{1F1EA}\u{1F1F8}',
  IT: '\u{1F1EE}\u{1F1F9}',
  SK: '\u{1F1F8}\u{1F1F0}',
  AT: '\u{1F1E6}\u{1F1F9}',
  SE: '\u{1F1F8}\u{1F1EA}',
  DK: '\u{1F1E9}\u{1F1F0}',
  FI: '\u{1F1EB}\u{1F1EE}',
  NO: '\u{1F1F3}\u{1F1F4}',
  LT: '\u{1F1F1}\u{1F1F9}',
  LV: '\u{1F1F1}\u{1F1FB}',
  EE: '\u{1F1EA}\u{1F1EA}',
  HU: '\u{1F1ED}\u{1F1FA}',
  RO: '\u{1F1F7}\u{1F1F4}',
  BG: '\u{1F1E7}\u{1F1EC}',
  HR: '\u{1F1ED}\u{1F1F7}',
  SI: '\u{1F1F8}\u{1F1EE}',
  BE: '\u{1F1E7}\u{1F1EA}',
  PT: '\u{1F1F5}\u{1F1F9}',
  IE: '\u{1F1EE}\u{1F1EA}',
  CH: '\u{1F1E8}\u{1F1ED}',
  UA: '\u{1F1FA}\u{1F1E6}',
  CA: '\u{1F1E8}\u{1F1E6}',
};

export const COUNTRY_NAME_MAP: Record<string, string> = {
  PL: 'Polska',
  DE: 'Niemcy',
  US: 'USA',
  CZ: 'Czechy',
  NL: 'Holandia',
  GB: 'Wielka Brytania',
  FR: 'Francja',
  ES: 'Hiszpania',
  IT: 'Wlochy',
  SK: 'Slowacja',
  AT: 'Austria',
  SE: 'Szwecja',
  DK: 'Dania',
  FI: 'Finlandia',
  NO: 'Norwegia',
  LT: 'Litwa',
  LV: 'Lotwa',
  EE: 'Estonia',
  HU: 'Wegry',
  RO: 'Rumunia',
  BG: 'Bulgaria',
  HR: 'Chorwacja',
  SI: 'Slowenia',
  BE: 'Belgia',
  PT: 'Portugalia',
  IE: 'Irlandia',
  CH: 'Szwajcaria',
  UA: 'Ukraina',
  CA: 'Kanada',
};

export interface ConnectorGroup {
  name: string;
  category: string;
  display_name: string;
  description: string;
  country: string;
  logo_url: string;
  website_url: string;
  interface: string;
  auth_type: string;
  status: 'stable' | 'beta' | 'planned' | string;
  supports_oauth2: boolean;
  sandbox_available: boolean;
  has_webhooks: boolean;
  health?: ConnectorHealthSummary | null;
  latest: Connector;
  versions: Connector[];
  activeVersions: string[];
}

export interface CategorySection {
  category: string;
  displayName: string;
  icon: string;
  groups: ConnectorGroup[];
}

export const CATEGORY_ORDER: string[] = [
  'courier', 'ecommerce', 'erp', 'wms', 'automation', 'other',
];

export const CATEGORY_DISPLAY: Record<string, { name: string; icon: string }> = {
  courier:    { name: 'Courier Services',      icon: 'local_shipping' },
  ecommerce:  { name: 'E-commerce',            icon: 'shopping_cart' },
  erp:        { name: 'ERP Systems',            icon: 'business' },
  wms:        { name: 'Warehouse Management',   icon: 'warehouse' },
  automation: { name: 'Automation',             icon: 'smart_toy' },
  other:      { name: 'Other',                  icon: 'category' },
};

export interface ConfigFieldType {
  type: 'string' | 'boolean' | 'select' | 'integer' | 'password';
  label?: string;
  default?: string | boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  row?: string;
}

export interface ConfigSchema {
  required: string[];
  optional: string[];
  field_types?: Record<string, ConfigFieldType>;
}

export interface ConnectorFieldDef {
  field: string;
  label: string;
  type: string;
  required?: boolean;
  description?: string;
}

export interface ConnectorActionSchema {
  connector_name: string;
  action: string;
  source: 'static' | 'dynamic' | 'merged';
  cached: boolean;
  input_fields: ConnectorFieldDef[];
  output_fields: ConnectorFieldDef[];
}

export interface ApiEndpoint {
  group: string;
  method: string;
  path: string;
  summary: string;
  description?: string;
  request_body?: ApiField[];
  response_body?: ApiField[];
}

export interface ApiField {
  field: string;
  type: string;
  required?: boolean;
  description?: string;
}

export interface ConnectorInstance {
  id: string;
  connector_name: string;
  connector_version: string;
  connector_category: string;
  display_name: string;
  is_enabled: boolean;
  config: Record<string, unknown>;
  created_at: string;
}

export interface Flow {
  id: string;
  name: string;
  is_enabled: boolean;
  source_connector: string;
  source_event: string;
  source_filter: Record<string, unknown> | null;
  destination_connector: string;
  destination_action: string;
  field_mapping: FieldMap[];
  on_error: string;
  max_retries: number;
  created_at: string;
}

export interface FieldMap {
  from: string;
  to: string;
  sources?: string[];
  transform?: Record<string, unknown> | Record<string, unknown>[];
}

export interface FlowExecution {
  id: string;
  flow_id: string;
  status: 'running' | 'success' | 'failed' | 'skipped';
  source_event_data: Record<string, unknown>;
  destination_action_data: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  duration_ms: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface FlowCreateRequest {
  name: string;
  source_connector: string;
  source_event: string;
  source_filter?: Record<string, unknown>;
  destination_connector: string;
  destination_action: string;
  field_mapping: FieldMap[];
  on_error?: string;
  max_retries?: number;
}

export interface FlowUpdateRequest {
  name?: string;
  source_connector?: string;
  source_event?: string;
  source_filter?: Record<string, unknown>;
  destination_connector?: string;
  destination_action?: string;
  field_mapping?: FieldMap[];
  on_error?: string;
  max_retries?: number;
  is_enabled?: boolean;
}

export interface CredentialStoreRequest {
  connector_name: string;
  credential_name: string;
  old_credential_name?: string;
  credentials: Record<string, string>;
}

export interface CredentialInfo {
  connector_name: string;
  credential_name: string;
  display_name: string;
  category: string;
  keys: string[];
  updated_at: string | null;
  token?: string | null;
}

export interface CredentialDetail {
  connector: string;
  credential_name: string;
  keys: string[];
  values: Record<string, string>;
  has_credentials: boolean;
  token?: string | null;
}

export interface CredentialStoreResponse {
  status: string;
  connector: string;
  credential_name: string;
  keys: string[];
  token: string;
  workflows_updated: number;
  account_provisioned: boolean;
}

export interface CredentialTokenRegenerateResponse {
  connector: string;
  credential_name: string;
  token: string;
}

export interface CredentialValidationResult {
  status: 'success' | 'failed' | 'unsupported';
  message: string;
  response_time_ms?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  checks: Record<string, string>;
}

export interface GdprMeta {
  redacted: boolean;
  policy: string;
  include_raw: boolean;
}

export interface FlowExecutionDetail {
  id: string;
  flow_id: string;
  status: 'running' | 'success' | 'failed' | 'skipped';
  source_event_data: Record<string, unknown>;
  destination_action_data: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  retry_count: number;
  duration_ms: number | null;
  started_at: string;
  completed_at: string | null;
  flow_name: string | null;
  source_connector: string | null;
  destination_connector: string | null;
  gdpr_meta: GdprMeta;
}

export interface WorkflowExecutionDetail {
  id: string;
  workflow_id: string | null;
  status: 'running' | 'success' | 'failed';
  trigger_data: Record<string, unknown>;
  node_results: WorkflowNodeResultDetail[];
  context_snapshot: Record<string, unknown>;
  workflow_nodes_snapshot: Record<string, unknown>[] | null;
  workflow_edges_snapshot: Record<string, unknown>[] | null;
  error: string | null;
  error_node_id: string | null;
  duration_ms: number | null;
  started_at: string;
  completed_at: string | null;
  workflow_name: string | null;
  workflow_description: string | null;
  trigger_connector: string | null;
  trigger_event: string | null;
  gdpr_meta: GdprMeta;
}

export interface WorkflowNodeResultDetail {
  node_id: string;
  node_type: string;
  label: string;
  status: 'success' | 'failed' | 'filtered' | 'running';
  output?: Record<string, unknown>;
  error?: string;
  duration_ms?: number;
  [key: string]: unknown;
}
