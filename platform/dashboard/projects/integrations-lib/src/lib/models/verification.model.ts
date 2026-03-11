export interface VerificationCheck {
  name: string;
  status: 'PASS' | 'FAIL' | 'SKIP' | 'WARN';
  response_time_ms: number;
  error?: string;
  suggestion?: string;
  current_api_version?: string;
  latest_api_version?: string;
  docs_url?: string;
}

export interface VerificationSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration_ms: number;
}

export interface VerificationConnectorResult {
  id?: string;
  connector_name: string;
  connector_version: string;
  connector_category: string;
  status: 'PASS' | 'FAIL' | 'PARTIAL' | 'SKIP' | 'NOT_RUN';
  checks?: VerificationCheck[];
  summary: VerificationSummary;
  created_at: string | null;
}

export interface VerificationRunSummary {
  run_id: string;
  created_at: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration_ms: number;
  connectors: VerificationConnectorResult[];
}

export interface VerificationRunDetail {
  run_id: string;
  created_at: string;
  connectors_tested: number;
  total_passed: number;
  total_failed: number;
  total_skipped: number;
  total_duration_ms: number;
  connectors: VerificationConnectorResult[];
}

export interface VerificationRunsResponse {
  total: number;
  page: number;
  page_size: number;
  runs: VerificationRunSummary[];
}

export interface SchedulerStatus {
  enabled: boolean;
  interval_days: number;
  last_run: string | null;
  next_run: string | null;
  currently_running: boolean;
}

export interface SchedulerUpdate {
  enabled?: boolean;
  interval_days?: number;
}

export interface VerificationError {
  connector_name: string;
  connector_version: string;
  connector_category: string;
  check_name: string;
  error: string;
  suggestion?: string;
  response_time_ms: number;
  run_id: string;
  created_at: string;
}

export interface VerificationErrorsResponse {
  total: number;
  page: number;
  page_size: number;
  errors: VerificationError[];
}

export interface VerificationLatestResponse {
  run_id: string | null;
  created_at: string | null;
  connectors: VerificationConnectorResult[];
}

export interface VerificationRunResponse {
  run_id: string;
  status: string;
}
