import { HttpClient, HttpParams } from '@angular/common/http';
import { Inject, Injectable, InjectionToken } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';

import {
  Connector,
  ConnectorActionSchema,
  ConnectorInstance,
  CredentialDetail,
  CredentialInfo,
  CredentialStoreRequest,
  CredentialStoreResponse,
  CredentialTokenRegenerateResponse,
  CredentialValidationResult,
  Flow,
  FlowCreateRequest,
  FlowUpdateRequest,
  FlowExecution,
  FlowExecutionDetail,
  HealthResponse,
  Workflow,
  WorkflowCreateRequest,
  WorkflowUpdateRequest,
  WorkflowExecution as WorkflowExecutionModel,
  WorkflowExecutionDetail,
  AiGenerateRequest,
  AiGenerateResponse,
  AiSuggestMappingsRequest,
  AiSuggestMappingsResponse,
  AiExplainErrorRequest,
  AiExplainErrorResponse,
  SchedulerStatus,
  SchedulerUpdate,
  VerificationErrorsResponse,
  VerificationLatestResponse,
  VerificationRunDetail,
  VerificationRunResponse,
  VerificationRunsResponse,
} from '../models';

export interface ConnectorListParams {
  category?: string;
  interface?: string;
  capability?: string;
  country?: string;
  event?: string;
  action?: string;
  q?: string;
  auth_type?: string;
  status?: string;
  supports_oauth2?: boolean;
  has_webhooks?: boolean;
  sandbox_available?: boolean;
}

export interface PinquarkConfig {
  apiUrl: string;
  apiKey: string;
}

export const PINQUARK_CONFIG = new InjectionToken<PinquarkConfig>('PINQUARK_CONFIG');

const ADMIN_SECRET_STORAGE_KEY = 'pinquark_admin_secret';

@Injectable({ providedIn: 'root' })
export class PinquarkApiService {
  private readonly apiUrl: string;
  private readonly headers: Record<string, string>;
  private adminSecret: string | null = null;

  get isAdmin(): boolean {
    return !!this.getAdminSecret();
  }

  get adminHeaders(): Record<string, string> {
    const secret = this.getAdminSecret();
    return secret ? { 'X-Admin-Secret': secret } : this.headers;
  }

  constructor(
    private readonly http: HttpClient,
    @Inject(PINQUARK_CONFIG) config: PinquarkConfig
  ) {
    this.apiUrl = config.apiUrl;
    this.headers = { 'X-API-Key': config.apiKey };
    this.adminSecret = sessionStorage.getItem(ADMIN_SECRET_STORAGE_KEY);
  }

  setAdminSecret(secret: string): void {
    this.adminSecret = secret;
    sessionStorage.setItem(ADMIN_SECRET_STORAGE_KEY, secret);
  }

  clearAdminSecret(): void {
    this.adminSecret = null;
    sessionStorage.removeItem(ADMIN_SECRET_STORAGE_KEY);
  }

  private getAdminSecret(): string | null {
    if (!this.adminSecret) {
      this.adminSecret = sessionStorage.getItem(ADMIN_SECRET_STORAGE_KEY);
    }
    return this.adminSecret;
  }

  health(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.apiUrl}/health`);
  }

  // --- Connectors ---

  listConnectors(params?: ConnectorListParams): Observable<Connector[]> {
    let httpParams = new HttpParams();
    if (params?.category) httpParams = httpParams.set('category', params.category);
    if (params?.interface) httpParams = httpParams.set('interface', params.interface);
    if (params?.capability) httpParams = httpParams.set('capability', params.capability);
    if (params?.country) httpParams = httpParams.set('country', params.country);
    if (params?.event) httpParams = httpParams.set('event', params.event);
    if (params?.action) httpParams = httpParams.set('action', params.action);
    if (params?.q) httpParams = httpParams.set('q', params.q);
    if (params?.auth_type) httpParams = httpParams.set('auth_type', params.auth_type);
    if (params?.status) httpParams = httpParams.set('status', params.status);
    if (params?.supports_oauth2 !== undefined) {
      httpParams = httpParams.set('supports_oauth2', String(params.supports_oauth2));
    }
    if (params?.has_webhooks !== undefined) {
      httpParams = httpParams.set('has_webhooks', String(params.has_webhooks));
    }
    if (params?.sandbox_available !== undefined) {
      httpParams = httpParams.set('sandbox_available', String(params.sandbox_available));
    }

    return this.http.get<Connector[]>(`${this.apiUrl}/api/v1/connectors`, {
      headers: this.headers,
      params: httpParams,
    });
  }

  getConnector(category: string, name: string): Observable<Connector> {
    return this.http.get<Connector>(`${this.apiUrl}/api/v1/connectors/${category}/${name}`, {
      headers: this.headers,
    });
  }

  getConnectorOpenApiSpec(connectorName: string, version?: string): Observable<object> {
    let params = new HttpParams();
    if (version) params = params.set('version', version);
    return this.http.get<object>(`${this.apiUrl}/api/v1/connectors/${connectorName}/openapi`, {
      headers: this.headers,
      params,
    });
  }

  getConnectorActionSchema(connectorName: string, action: string, version?: string): Observable<ConnectorActionSchema> {
    const encodedAction = action.split('.').map(part => encodeURIComponent(part)).join('/');
    let params = new HttpParams();
    if (version) params = params.set('version', version);
    return this.http.get<ConnectorActionSchema>(
      `${this.apiUrl}/api/v1/connectors/${connectorName}/schema/${encodedAction}`,
      { headers: this.headers, params },
    );
  }

  downloadOnPremiseAgent(connectorName: string, connectorVersion?: string): Observable<void> {
    let url = `${this.apiUrl}/api/v1/connectors/${connectorName}/onpremise-agent`;
    if (connectorVersion) {
      url += `?version=${encodeURIComponent(connectorVersion)}`;
    }
    return this.http.get(url, {
      headers: this.headers,
      responseType: 'blob',
      observe: 'response',
    }).pipe(
      tap(response => {
        const disposition = response.headers.get('Content-Disposition') || '';
        const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
        const filename = filenameMatch?.[1] ?? `${connectorName}-onpremise-agent.zip`;
        const blob = response.body;
        if (!blob) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
      }),
      catchError(err => {
        const status = err?.status ?? 0;
        const message = status === 401
          ? 'Authentication required to download the agent.'
          : status === 404
            ? 'On-premise agent not found for this connector.'
            : `Failed to download agent (HTTP ${status}).`;
        return throwError(() => new Error(message));
      }),
    ) as unknown as Observable<void>;
  }

  // --- Connector Instances ---

  listConnectorInstances(): Observable<ConnectorInstance[]> {
    return this.http.get<ConnectorInstance[]>(`${this.apiUrl}/api/v1/connector-instances`, {
      headers: this.headers,
    });
  }

  activateConnector(body: {
    connector_name: string;
    connector_version: string;
    connector_category: string;
    display_name?: string;
    config?: Record<string, unknown>;
  }): Observable<ConnectorInstance> {
    return this.http.post<ConnectorInstance>(`${this.apiUrl}/api/v1/connector-instances`, body, {
      headers: this.headers,
    });
  }

  deactivateConnector(instanceId: string): Observable<Record<string, string>> {
    return this.http.delete<Record<string, string>>(`${this.apiUrl}/api/v1/connector-instances/${instanceId}`, {
      headers: this.headers,
    });
  }

  // --- Credentials ---

  listCredentials(): Observable<CredentialInfo[]> {
    return this.http.get<CredentialInfo[]>(`${this.apiUrl}/api/v1/credentials`, {
      headers: this.headers,
    });
  }

  getCredentials(connectorName: string, credentialName = 'default'): Observable<CredentialDetail> {
    const params = new HttpParams().set('credential_name', credentialName);
    return this.http.get<CredentialDetail>(`${this.apiUrl}/api/v1/credentials/${connectorName}`, {
      headers: this.headers,
      params,
    });
  }

  listCredentialNames(connectorName: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/api/v1/credentials/${connectorName}/names`, {
      headers: this.headers,
    });
  }

  storeCredentials(body: CredentialStoreRequest): Observable<CredentialStoreResponse> {
    return this.http.post<CredentialStoreResponse>(`${this.apiUrl}/api/v1/credentials`, body, {
      headers: this.headers,
    });
  }

  regenerateCredentialToken(
    connectorName: string,
    credentialName = 'default',
  ): Observable<CredentialTokenRegenerateResponse> {
    const params = new HttpParams().set('credential_name', credentialName);
    return this.http.post<CredentialTokenRegenerateResponse>(
      `${this.apiUrl}/api/v1/credentials/${connectorName}/token/regenerate`,
      null,
      { headers: this.headers, params },
    );
  }

  deleteCredentials(connectorName: string, credentialName?: string): Observable<Record<string, string>> {
    let params = new HttpParams();
    if (credentialName) params = params.set('credential_name', credentialName);
    return this.http.delete<Record<string, string>>(`${this.apiUrl}/api/v1/credentials/${connectorName}`, {
      headers: this.headers,
      params,
    });
  }

  generateTestData(connectorName: string): Observable<Record<string, string>> {
    return this.http.post<Record<string, string>>(
      `${this.apiUrl}/api/v1/connectors/${connectorName}/generate-test-data`,
      {},
      { headers: this.headers },
    );
  }

  validateCredentials(
    connectorName: string,
    credentialName = 'default',
    credentials?: Record<string, string>,
  ): Observable<CredentialValidationResult> {
    const body = credentials
      ? { connector_name: connectorName, credential_name: credentialName, credentials }
      : null;
    const params = new HttpParams().set('credential_name', credentialName);
    return this.http.post<CredentialValidationResult>(
      `${this.apiUrl}/api/v1/credentials/${connectorName}/validate`,
      body,
      { headers: this.headers, params },
    );
  }

  // --- Flows ---

  listFlows(): Observable<Flow[]> {
    return this.http.get<Flow[]>(`${this.apiUrl}/api/v1/flows`, {
      headers: this.headers,
    });
  }

  createFlow(body: FlowCreateRequest): Observable<Flow> {
    return this.http.post<Flow>(`${this.apiUrl}/api/v1/flows`, body, {
      headers: this.headers,
    });
  }

  updateFlow(flowId: string, body: FlowUpdateRequest): Observable<Flow> {
    return this.http.patch<Flow>(`${this.apiUrl}/api/v1/flows/${flowId}`, body, {
      headers: this.headers,
    });
  }

  deleteFlow(flowId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/api/v1/flows/${flowId}`, {
      headers: this.headers,
    });
  }

  // --- Flow Executions ---

  listFlowExecutions(params?: {
    flow_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
    date_from?: string;
    date_to?: string;
  }): Observable<FlowExecution[]> {
    let httpParams = new HttpParams();
    if (params?.flow_id) httpParams = httpParams.set('flow_id', params.flow_id);
    if (params?.status) httpParams = httpParams.set('status', params.status);
    if (params?.limit) httpParams = httpParams.set('limit', params.limit.toString());
    if (params?.offset) httpParams = httpParams.set('offset', params.offset.toString());
    if (params?.date_from) httpParams = httpParams.set('date_from', params.date_from);
    if (params?.date_to) httpParams = httpParams.set('date_to', params.date_to);

    return this.http.get<FlowExecution[]>(`${this.apiUrl}/api/v1/flow-executions`, {
      headers: this.headers,
      params: httpParams,
    });
  }

  getFlowExecutionDetail(executionId: string): Observable<FlowExecutionDetail> {
    return this.http.get<FlowExecutionDetail>(`${this.apiUrl}/api/v1/flow-executions/${executionId}`, {
      headers: this.headers,
    });
  }

  // --- Events ---

  triggerEvent(connectorName: string, event: string, data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.apiUrl}/api/v1/events`, {
      connector_name: connectorName,
      event,
      data,
    }, { headers: this.headers });
  }

  // --- Workflows ---

  listWorkflows(): Observable<Workflow[]> {
    return this.http.get<Workflow[]>(`${this.apiUrl}/api/v1/workflows`, {
      headers: this.headers,
    });
  }

  getWorkflow(workflowId: string): Observable<Workflow> {
    return this.http.get<Workflow>(`${this.apiUrl}/api/v1/workflows/${workflowId}`, {
      headers: this.headers,
    });
  }

  createWorkflow(body: WorkflowCreateRequest): Observable<Workflow> {
    return this.http.post<Workflow>(`${this.apiUrl}/api/v1/workflows`, body, {
      headers: this.headers,
    });
  }

  updateWorkflow(workflowId: string, body: WorkflowUpdateRequest): Observable<Workflow> {
    return this.http.patch<Workflow>(`${this.apiUrl}/api/v1/workflows/${workflowId}`, body, {
      headers: this.headers,
    });
  }

  deleteWorkflow(workflowId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/api/v1/workflows/${workflowId}`, {
      headers: this.headers,
    });
  }

  testWorkflow(workflowId: string, triggerData: Record<string, unknown>): Observable<WorkflowExecutionModel> {
    return this.http.post<WorkflowExecutionModel>(
      `${this.apiUrl}/api/v1/workflows/${workflowId}/test`,
      { trigger_data: triggerData },
      { headers: this.headers },
    );
  }

  toggleWorkflow(workflowId: string): Observable<{ status: string; is_enabled: boolean }> {
    return this.http.post<{ status: string; is_enabled: boolean }>(
      `${this.apiUrl}/api/v1/workflows/${workflowId}/toggle`,
      {},
      { headers: this.headers },
    );
  }

  listWorkflowExecutions(params?: {
    workflow_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
    date_from?: string;
    date_to?: string;
  }): Observable<WorkflowExecutionModel[]> {
    let httpParams = new HttpParams();
    if (params?.workflow_id) httpParams = httpParams.set('workflow_id', params.workflow_id);
    if (params?.status) httpParams = httpParams.set('status', params.status);
    if (params?.limit) httpParams = httpParams.set('limit', params.limit.toString());
    if (params?.offset) httpParams = httpParams.set('offset', params.offset.toString());
    if (params?.date_from) httpParams = httpParams.set('date_from', params.date_from);
    if (params?.date_to) httpParams = httpParams.set('date_to', params.date_to);
    return this.http.get<WorkflowExecutionModel[]>(`${this.apiUrl}/api/v1/workflow-executions`, {
      headers: this.headers,
      params: httpParams,
    });
  }

  getWorkflowExecutionDetail(executionId: string): Observable<WorkflowExecutionDetail> {
    return this.http.get<WorkflowExecutionDetail>(`${this.apiUrl}/api/v1/workflow-executions/${executionId}`, {
      headers: this.headers,
    });
  }

  aiGenerateWorkflow(body: AiGenerateRequest): Observable<AiGenerateResponse> {
    return this.http.post<AiGenerateResponse>(`${this.apiUrl}/api/v1/workflows/ai-generate`, body, {
      headers: this.headers,
    });
  }

  aiSuggestFieldMappings(body: AiSuggestMappingsRequest): Observable<AiSuggestMappingsResponse> {
    return this.http.post<AiSuggestMappingsResponse>(`${this.apiUrl}/api/v1/ai/field-mappings/suggest`, body, {
      headers: this.headers,
    });
  }

  aiExplainError(body: AiExplainErrorRequest): Observable<AiExplainErrorResponse> {
    return this.http.post<AiExplainErrorResponse>(`${this.apiUrl}/api/v1/ai/explain-error`, body, {
      headers: this.headers,
    });
  }

  // --- Verification ---

  verificationRunAll(): Observable<VerificationRunResponse> {
    return this.http.post<VerificationRunResponse>(`${this.apiUrl}/api/verification/run`, {}, {
      headers: this.adminHeaders,
    });
  }

  verificationRunSingle(connectorName: string, version?: string): Observable<VerificationRunResponse> {
    const params = version ? `?version=${encodeURIComponent(version)}` : '';
    return this.http.post<VerificationRunResponse>(`${this.apiUrl}/api/verification/run/${connectorName}${params}`, {}, {
      headers: this.adminHeaders,
    });
  }

  verificationSchedulerStatus(): Observable<SchedulerStatus> {
    return this.http.get<SchedulerStatus>(`${this.apiUrl}/api/verification/scheduler`, {
      headers: this.adminHeaders,
    });
  }

  verificationSchedulerUpdate(body: SchedulerUpdate): Observable<SchedulerStatus> {
    return this.http.put<SchedulerStatus>(`${this.apiUrl}/api/verification/scheduler`, body, {
      headers: this.adminHeaders,
    });
  }

  verificationListRuns(page = 1, pageSize = 20): Observable<VerificationRunsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<VerificationRunsResponse>(`${this.apiUrl}/api/verification/runs`, {
      headers: this.adminHeaders,
      params,
    });
  }

  verificationGetRun(runId: string): Observable<VerificationRunDetail> {
    return this.http.get<VerificationRunDetail>(`${this.apiUrl}/api/verification/runs/${runId}`, {
      headers: this.adminHeaders,
    });
  }

  verificationListErrors(params?: {
    connector_name?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Observable<VerificationErrorsResponse> {
    let httpParams = new HttpParams();
    if (params?.connector_name) httpParams = httpParams.set('connector_name', params.connector_name);
    if (params?.date_from) httpParams = httpParams.set('date_from', params.date_from);
    if (params?.date_to) httpParams = httpParams.set('date_to', params.date_to);
    if (params?.page) httpParams = httpParams.set('page', params.page.toString());
    if (params?.page_size) httpParams = httpParams.set('page_size', params.page_size.toString());
    return this.http.get<VerificationErrorsResponse>(`${this.apiUrl}/api/verification/errors`, {
      headers: this.adminHeaders,
      params: httpParams,
    });
  }

  verificationLatest(): Observable<VerificationLatestResponse> {
    return this.http.get<VerificationLatestResponse>(`${this.apiUrl}/api/verification/reports/latest`, {
      headers: this.adminHeaders,
    });
  }

  // ── Sync Ledger ──

  getSyncStats(workflowId: string): Observable<{ workflow_id: string; workflow_name: string; sync_config: unknown; stats: { synced: number; failed: number; pending: number; stale: number; total: number } }> {
    return this.http.get<{ workflow_id: string; workflow_name: string; sync_config: unknown; stats: { synced: number; failed: number; pending: number; stale: number; total: number } }>(
      `${this.apiUrl}/api/v1/workflows/${workflowId}/sync-stats`,
      { headers: this.headers },
    );
  }

  getSyncFailed(workflowId: string, limit = 50): Observable<{ id: string; entity_key: string; attempt_count: number; last_error: string | null; updated_at: string | null }[]> {
    return this.http.get<{ id: string; entity_key: string; attempt_count: number; last_error: string | null; updated_at: string | null }[]>(
      `${this.apiUrl}/api/v1/workflows/${workflowId}/sync-failed`,
      { headers: this.headers, params: { limit: limit.toString() } },
    );
  }

  retrySyncs(workflowId: string): Observable<{ reset_count: number }> {
    return this.http.post<{ reset_count: number }>(
      `${this.apiUrl}/api/v1/workflows/${workflowId}/sync-retry`,
      {},
      { headers: this.headers },
    );
  }

  clearSyncLedger(workflowId: string): Observable<{ deleted_count: number }> {
    return this.http.post<{ deleted_count: number }>(
      `${this.apiUrl}/api/v1/workflows/${workflowId}/sync-clear`,
      {},
      { headers: this.headers },
    );
  }
}
