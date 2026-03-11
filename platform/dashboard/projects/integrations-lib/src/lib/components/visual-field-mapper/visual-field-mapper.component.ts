import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ConnectorFieldDef, FieldMapping, AiSuggestMappingsResponse, TransformStep, TRANSFORM_TYPES, TransformTypeDef } from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';

interface AiSettings {
  model: 'gemini' | 'opus';
  apiKey: string;
}

@Component({
  selector: 'pinquark-visual-field-mapper',
  standalone: true,
  imports: [
    FormsModule,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  template: `
    <div class="vfm">
      <div class="vfm__toolbar">
        <div class="vfm__actions">
          <button mat-stroked-button (click)="autoMap()"><mat-icon>auto_fix_high</mat-icon> Auto-map</button>
          <button mat-stroked-button (click)="suggestWithAi()" [disabled]="aiLoading || sourceFields.length === 0 || destinationFields.length === 0">
            <mat-icon>{{ aiLoading ? 'hourglass_top' : 'psychology' }}</mat-icon> {{ aiLoading ? 'Thinking...' : 'AI Auto-map' }}
          </button>
          <button mat-button color="warn" (click)="clearMappings()" [disabled]="mappings.length === 0"><mat-icon>clear_all</mat-icon> Clear</button>
        </div>
        @if (pendingSource) {
          <span class="vfm__hint vfm__hint--active">
            <mat-icon>ads_click</mat-icon> <strong>{{ pendingSource.label }}</strong> selected — click a target field
          </span>
        }
      </div>

      <div class="vfm__layout">
        <div class="vfm__col">
          <div class="vfm__col-head">
            <span class="vfm__col-title">{{ sourceLabel }}</span>
            <span class="vfm__col-count">{{ sourceFields.length }}</span>
          </div>
          <div class="vfm__field-list">
            @for (field of sourceFields; track field.field) {
              <button type="button" class="vfm__field"
                [attr.data-side]="'source'" [attr.data-field]="field.field"
                [class.vfm__field--selected]="pendingSource?.field === field.field"
                [class.vfm__field--dragging]="draggedSource?.field === field.field"
                draggable="true" (dragstart)="onDragStart($event, field)" (dragend)="onDragEnd()" (click)="selectSource(field)">
                <mat-icon class="vfm__grip">drag_indicator</mat-icon>
                <div class="vfm__field-text">
                  <span class="vfm__field-name">{{ field.label }}</span>
                  <span class="vfm__field-key">{{ field.field }}</span>
                </div>
                <span class="vfm__field-type">{{ field.type }}</span>
              </button>
            }
          </div>
        </div>

        <div class="vfm__col vfm__col--center">
          <div class="vfm__col-head">
            <span class="vfm__col-title">Mappings</span>
            <span class="vfm__col-count">{{ mappings.length }}</span>
          </div>
          @if (mappings.length === 0) {
            <div class="vfm__empty">
              <mat-icon>device_hub</mat-icon>
              <span>No mappings yet. Select left, click right.</span>
            </div>
          } @else {
            <div class="vfm__field-list">
              @for (mapping of mappings; track mappingKey(mapping, $index); let i = $index) {
                <div class="vfm__map-row" [class.vfm__map-row--active]="editingTransformIndex === i"
                  (click)="toggleTransformEditor(i, $event)">
                  <span class="vfm__map-from" [matTooltip]="displaySource(mapping)">{{ displaySource(mapping) }}</span>
                  <mat-icon class="vfm__map-arrow">east</mat-icon>
                  <span class="vfm__map-to" [matTooltip]="displayTarget(mapping)">{{ displayTarget(mapping) }}</span>
                  <span class="vfm__map-fx" matTooltip="Transforms">fx {{ getTransformCount(mapping) }}</span>
                  <button mat-icon-button class="vfm__map-del" (click)="removeMapping(i); $event.stopPropagation()" matTooltip="Remove">
                    <mat-icon>delete_outline</mat-icon>
                  </button>
                </div>
                @if (editingTransformIndex === i) {
                  <div class="vfm__tx-editor" (click)="$event.stopPropagation()">
                    <div class="vfm__tx-head">
                      <span>Transforms: {{ displaySource(mapping) }} → {{ displayTarget(mapping) }}</span>
                      <button mat-icon-button (click)="editingTransformIndex = -1"><mat-icon>close</mat-icon></button>
                    </div>
                    @for (step of getTransformSteps(mapping); track $index; let si = $index) {
                      <div class="vfm__tx-step">
                        <mat-form-field appearance="outline" class="vfm__tx-type">
                          <mat-label>Type</mat-label>
                          <mat-select [value]="step.type" (selectionChange)="updateTransformType(i, si, $event.value)">
                            @for (tt of transformTypes; track tt.value) { <mat-option [value]="tt.value">{{ tt.label }}</mat-option> }
                          </mat-select>
                        </mat-form-field>
                        @for (cfgKey of getTransformConfigFields(step.type); track cfgKey) {
                          <mat-form-field appearance="outline" class="vfm__tx-cfg">
                            <mat-label>{{ cfgKey }}</mat-label>
                            <input matInput [value]="step[cfgKey] ?? ''" (change)="updateTransformConfig(i, si, cfgKey, $event)" />
                          </mat-form-field>
                        }
                        <button mat-icon-button color="warn" (click)="removeTransformStep(i, si)"><mat-icon>remove_circle</mat-icon></button>
                      </div>
                    }
                    <button mat-stroked-button (click)="addTransformStep(i)"><mat-icon>add</mat-icon> Add</button>
                  </div>
                }
              }
            </div>
          }
        </div>

        <div class="vfm__col">
          <div class="vfm__col-head">
            <span class="vfm__col-title">{{ destinationLabel }}</span>
            <span class="vfm__col-count">{{ destinationFields.length }}</span>
          </div>
          <div class="vfm__field-list">
            @for (field of destinationFields; track field.field) {
              <button type="button" class="vfm__field"
                [attr.data-side]="'target'" [attr.data-field]="field.field"
                [class.vfm__field--mapped]="isMappedTarget(field.field)"
                [class.vfm__field--drop-active]="draggedSource && !isMappedTarget(field.field)"
                [class.vfm__field--drop-hover]="dropHoverField === field.field"
                (dragover)="onDragOver($event, field)" (dragleave)="onDragLeave()" (drop)="onDrop($event, field)" (click)="connectTo(field)">
                <div class="vfm__field-text">
                  <span class="vfm__field-name">{{ field.label }}@if (field.required) {<span class="vfm__req">*</span>}</span>
                  <span class="vfm__field-key">{{ field.field }}</span>
                </div>
                <span class="vfm__field-type">{{ field.type }}</span>
              </button>
            }
          </div>
        </div>
      </div>

      <details class="vfm__preview">
        <summary class="vfm__preview-toggle">
          <mat-icon>science</mat-icon> Test mapping preview
        </summary>
        <div class="vfm__preview-body">
          <div class="vfm__preview-row">
            <mat-form-field appearance="outline" class="vfm__preview-input">
              <mat-label>Sample input</mat-label>
              <textarea matInput rows="6" [(ngModel)]="sampleInputJson"></textarea>
            </mat-form-field>
            <div class="vfm__preview-out">
              @if (previewError) { <span class="vfm__preview-err">{{ previewError }}</span> }
              @else { <pre>{{ previewOutputJson }}</pre> }
            </div>
          </div>
          <button mat-stroked-button (click)="generatePreview()"><mat-icon>play_arrow</mat-icon> Run preview</button>
        </div>
      </details>
    </div>
  `,
  styles: [`
    .vfm { display: flex; flex-direction: column; gap: 8px; color: #1e293b; font-size: 13px; }

    .vfm__toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
    .vfm__actions { display: flex; gap: 6px; flex-wrap: wrap; }
    .vfm__hint { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #64748b; }
    .vfm__hint mat-icon { width: 16px; height: 16px; font-size: 16px; }
    .vfm__hint--active { color: #2563eb; font-weight: 600; }

    .vfm__layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, 0.9fr) minmax(0, 1fr); gap: 8px; align-items: start; }

    .vfm__col { border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; }
    .vfm__col--center { background: #f8fafc; }
    .vfm__col-head { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
    .vfm__col-title { font-size: 12px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.04em; }
    .vfm__col-count { font-size: 11px; font-weight: 700; color: #64748b; background: #f1f5f9; padding: 2px 7px; border-radius: 999px; }

    .vfm__field-list { display: flex; flex-direction: column; gap: 4px; padding: 6px; max-height: 460px; overflow: auto; }

    .vfm__field { display: flex; align-items: center; gap: 8px; width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 7px 10px; cursor: pointer; text-align: left; transition: border-color 0.15s, background 0.15s; }
    .vfm__field:hover { border-color: #93c5fd; background: #f8fbff; }
    .vfm__field--selected { border-color: #2563eb; background: #eff6ff; }
    .vfm__field--dragging { opacity: 0.5; border-color: #2563eb; }
    .vfm__field--drop-active { border-style: dashed; border-color: #93c5fd; }
    .vfm__field--drop-hover { border-color: #2563eb; background: #eff6ff; }
    .vfm__field--mapped { border-color: #86efac; background: #f0fdf4; }

    .vfm__grip { font-size: 14px; width: 14px; height: 14px; color: #94a3b8; cursor: grab; flex-shrink: 0; }
    .vfm__field-text { min-width: 0; flex: 1; display: flex; flex-direction: column; }
    .vfm__field-name { font-size: 12px; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .vfm__field-key { font-size: 11px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .vfm__field-type { font-size: 10px; color: #94a3b8; white-space: nowrap; flex-shrink: 0; }
    .vfm__req { color: #dc2626; margin-left: 2px; }

    .vfm__empty { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 28px 12px; color: #94a3b8; font-size: 12px; }
    .vfm__empty mat-icon { width: 20px; height: 20px; font-size: 20px; }

    .vfm__map-row { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; cursor: pointer; transition: border-color 0.15s; }
    .vfm__map-row:hover { border-color: #93c5fd; background: #f8fbff; }
    .vfm__map-row--active { border-color: #2563eb; background: #eff6ff; }
    .vfm__map-from, .vfm__map-to { flex: 1; min-width: 0; font-size: 12px; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .vfm__map-arrow { width: 14px; height: 14px; font-size: 14px; color: #2563eb; flex-shrink: 0; }
    .vfm__map-fx { font-size: 10px; font-weight: 700; color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 999px; flex-shrink: 0; }
    .vfm__map-del { width: 28px; height: 28px; flex-shrink: 0; }
    .vfm__map-del mat-icon { font-size: 16px; width: 16px; height: 16px; }

    .vfm__tx-editor { margin-top: 4px; padding: 8px; border: 1px solid #c7d7f5; border-radius: 8px; background: #f0f5ff; }
    .vfm__tx-head { display: flex; align-items: center; justify-content: space-between; font-size: 11px; font-weight: 600; color: #1d4ed8; margin-bottom: 6px; }
    .vfm__tx-step { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
    .vfm__tx-type { width: 150px; }
    .vfm__tx-cfg { width: 130px; }

    .vfm__preview { border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; }
    .vfm__preview-toggle { padding: 8px 12px; cursor: pointer; font-size: 12px; font-weight: 600; color: #475569; display: flex; align-items: center; gap: 6px; list-style: none; }
    .vfm__preview-toggle::-webkit-details-marker { display: none; }
    .vfm__preview-toggle mat-icon { width: 16px; height: 16px; font-size: 16px; }
    .vfm__preview-body { padding: 8px 12px 12px; border-top: 1px solid #e2e8f0; }
    .vfm__preview-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px; }
    .vfm__preview-input { width: 100%; }
    .vfm__preview-out { min-height: 160px; padding: 10px; border-radius: 8px; background: #0f172a; color: #e2e8f0; overflow: auto; font-size: 11px; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
    .vfm__preview-out pre { margin: 0; white-space: pre-wrap; word-break: break-word; line-height: 1.5; }
    .vfm__preview-err { color: #fca5a5; font-size: 11px; }

    @media (max-width: 1100px) {
      .vfm__layout, .vfm__preview-row { grid-template-columns: 1fr; }
    }
  `],
})
export class VisualFieldMapperComponent {
  @Input() heading = 'Visual Field Mapper';
  @Input() description = 'Map source fields to destination fields visually.';
  @Input() sourceLabel = 'Source Schema';
  @Input() destinationLabel = 'Destination Schema';
  @Input() sourceFields: ConnectorFieldDef[] = [];
  @Input() destinationFields: ConnectorFieldDef[] = [];
  @Input() mappings: FieldMapping[] = [];
  @Input() contextHint = '';

  @Output() mappingsChange = new EventEmitter<FieldMapping[]>();

  pendingSource: ConnectorFieldDef | null = null;
  draggedSource: ConnectorFieldDef | null = null;
  dropHoverField: string | null = null;
  editingTransformIndex = -1;
  transformTypes: TransformTypeDef[] = TRANSFORM_TYPES;
  sampleInputJson = '{}';
  previewOutputJson = '{}';
  previewError = '';
  aiLoading = false;

  constructor(
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar,
  ) {}

  selectSource(field: ConnectorFieldDef): void {
    this.pendingSource = this.pendingSource?.field === field.field ? null : field;
  }

  connectTo(field: ConnectorFieldDef): void {
    if (!this.pendingSource) {
      this.snackBar.open('Select a source field first', '', { duration: 2000 });
      return;
    }

    const next = [...this.mappings];
    const existingIndex = next.findIndex(mapping => this.resolveTarget(mapping) === field.field);
    const base = existingIndex >= 0
      ? { ...next[existingIndex] }
      : { from: this.pendingSource.field, to: field.field } as FieldMapping;

    base.from = this.pendingSource.field;
    base.to = field.field;
    delete base.from_custom;
    delete base.sources;

    if (existingIndex >= 0) {
      next[existingIndex] = base;
    } else {
      next.push(base);
    }

    this.pendingSource = null;
    this.emitMappings(next);
  }

  onDragStart(event: DragEvent, field: ConnectorFieldDef): void {
    this.draggedSource = field;
    this.pendingSource = field;
    event.dataTransfer?.setData('text/plain', field.field);
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'link';
    }
  }

  onDragEnd(): void {
    this.draggedSource = null;
    this.dropHoverField = null;
  }

  onDragOver(event: DragEvent, field: ConnectorFieldDef): void {
    if (!this.draggedSource) return;
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'link';
    }
    this.dropHoverField = field.field;
  }

  onDragLeave(): void {
    this.dropHoverField = null;
  }

  onDrop(event: DragEvent, field: ConnectorFieldDef): void {
    event.preventDefault();
    this.dropHoverField = null;
    if (this.draggedSource) {
      this.pendingSource = this.draggedSource;
      this.connectTo(field);
    }
    this.draggedSource = null;
  }

  toggleTransformEditor(index: number, event: Event): void {
    event.stopPropagation();
    this.editingTransformIndex = this.editingTransformIndex === index ? -1 : index;
  }

  getTransformSteps(mapping: FieldMapping): TransformStep[] {
    if (!mapping.transform) return [];
    return Array.isArray(mapping.transform) ? mapping.transform : [mapping.transform];
  }

  getTransformConfigFields(type: string): string[] {
    const def = TRANSFORM_TYPES.find(t => t.value === type);
    return def?.configFields ?? [];
  }

  addTransformStep(mappingIndex: number): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const steps = this.getTransformSteps(mapping);
    mapping.transform = [...steps, { type: 'uppercase' }];
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  removeTransformStep(mappingIndex: number, stepIndex: number): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const steps = [...this.getTransformSteps(mapping)];
    steps.splice(stepIndex, 1);
    mapping.transform = steps.length > 0 ? steps : undefined;
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  updateTransformType(mappingIndex: number, stepIndex: number, newType: string): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const steps = [...this.getTransformSteps(mapping)];
    steps[stepIndex] = { type: newType };
    mapping.transform = steps;
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  updateTransformConfig(mappingIndex: number, stepIndex: number, key: string, event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const steps = [...this.getTransformSteps(mapping)];
    steps[stepIndex] = { ...steps[stepIndex], [key]: value };
    mapping.transform = steps;
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  autoMap(): void {
    const takenTargets = new Set(this.mappings.map(mapping => this.resolveTarget(mapping)));
    const next = [...this.mappings];

    for (const destination of this.destinationFields) {
      if (takenTargets.has(destination.field)) {
        continue;
      }
      const candidate = this.findBestSource(destination);
      if (!candidate) {
        continue;
      }
      next.push({ from: candidate.field, to: destination.field });
      takenTargets.add(destination.field);
    }

    this.emitMappings(next);
    this.snackBar.open('Suggested mappings generated', '', { duration: 2500 });
  }

  async suggestWithAi(): Promise<void> {
    const settings = this.loadAiSettings();
    if (!settings?.apiKey) {
      this.snackBar.open('Save AI settings first on the Settings page', 'OK', { duration: 3500 });
      return;
    }

    this.aiLoading = true;
    this.api.aiSuggestFieldMappings({
      model: settings.model,
      api_key: settings.apiKey,
      prompt: this.contextHint,
      source_fields: this.sourceFields,
      destination_fields: this.destinationFields,
      existing_mappings: this.mappings,
    }).subscribe({
      next: (resp: AiSuggestMappingsResponse) => {
        this.aiLoading = false;
        this.emitMappings(resp.mappings ?? []);
        this.snackBar.open(resp.message || 'AI mapping suggestions applied', '', { duration: 3000 });
      },
      error: (err) => {
        this.aiLoading = false;
        const detail = err?.error?.detail || 'AI mapping suggestion failed';
        this.snackBar.open(detail, 'OK', { duration: 4000 });
      },
    });
  }

  clearMappings(): void {
    this.pendingSource = null;
    this.emitMappings([]);
  }

  removeMapping(index: number): void {
    const next = [...this.mappings];
    next.splice(index, 1);
    this.emitMappings(next);
  }

  isMappedTarget(fieldPath: string): boolean {
    return this.mappings.some(mapping => this.resolveTarget(mapping) === fieldPath);
  }

  isMappedSource(fieldPath: string): boolean {
    return this.mappings.some(mapping =>
      mapping.from === fieldPath || mapping.sources?.includes(fieldPath) === true,
    );
  }

  displaySource(mapping: FieldMapping): string {
    if (mapping.sources?.length) {
      return mapping.sources.join(' + ');
    }
    if (mapping.from === '__custom__') {
      return mapping.from_custom || '(static value)';
    }
    return mapping.from || '(empty)';
  }

  displayTarget(mapping: FieldMapping): string {
    return this.resolveTarget(mapping) || '(empty)';
  }

  mappingKey(mapping: FieldMapping, index: number): string {
    return `${this.displaySource(mapping)}:${this.displayTarget(mapping)}:${index}`;
  }

  getTransformCount(mapping: FieldMapping): number {
    if (!mapping.transform) {
      return 0;
    }
    return Array.isArray(mapping.transform) ? mapping.transform.length : 1;
  }

  generatePreview(): void {
    this.previewError = '';
    try {
      const input = JSON.parse(this.sampleInputJson || '{}') as Record<string, unknown>;
      const output: Record<string, unknown> = {};
      for (const mapping of this.mappings) {
        const target = this.resolveTarget(mapping);
        if (!target) {
          continue;
        }
        let value = this.resolveMappingValue(input, mapping);
        value = this.applyTransforms(value, mapping);
        this.assignPath(output, target, value);
      }
      this.previewOutputJson = JSON.stringify(output, null, 2);
    } catch (error) {
      this.previewError = error instanceof Error ? error.message : 'Invalid JSON';
      this.previewOutputJson = '{}';
    }
  }

  private emitMappings(mappings: FieldMapping[]): void {
    this.mappings = mappings;
    this.mappingsChange.emit(mappings);
    this.generatePreview();
  }

  private resolveTarget(mapping: FieldMapping): string {
    return mapping.to === '__custom__' ? mapping.to_custom || '' : mapping.to || '';
  }

  private loadAiSettings(): AiSettings | null {
    try {
      const stored = localStorage.getItem('pinquark_ai_settings');
      if (!stored) {
        return null;
      }
      return JSON.parse(stored) as AiSettings;
    } catch {
      return null;
    }
  }

  private findBestSource(destination: ConnectorFieldDef): ConnectorFieldDef | null {
    const destinationTokens = this.tokenize(destination);
    let best: { field: ConnectorFieldDef; score: number } | null = null;

    for (const source of this.sourceFields) {
      const score = this.getSimilarityScore(destinationTokens, this.tokenize(source));
      if (score <= 0) {
        continue;
      }
      if (!best || score > best.score) {
        best = { field: source, score };
      }
    }

    return best?.score && best.score >= 3 ? best.field : null;
  }

  private tokenize(field: ConnectorFieldDef): string[] {
    const raw = `${field.label} ${field.field}`
      .replace(/\[\]/g, ' array ')
      .replace(/[._-]/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .toLowerCase();
    return raw.split(/\s+/).filter(Boolean);
  }

  private getSimilarityScore(destinationTokens: string[], sourceTokens: string[]): number {
    const exact = destinationTokens.filter(token => sourceTokens.includes(token)).length;
    const destinationTail = destinationTokens[destinationTokens.length - 1];
    const sourceTail = sourceTokens[sourceTokens.length - 1];
    const tailMatch = destinationTail === sourceTail ? 2 : 0;
    const pluralMatch = destinationTokens.some(dt => sourceTokens.some(st => dt.replace(/s$/, '') === st.replace(/s$/, ''))) ? 1 : 0;
    return exact + tailMatch + pluralMatch;
  }

  private resolveMappingValue(input: Record<string, unknown>, mapping: FieldMapping): unknown {
    const source = mapping.from === '__custom__' ? mapping.from_custom ?? '' : mapping.from;
    if (!source) {
      return null;
    }
    if (mapping.sources?.length) {
      return mapping.sources.map(path => this.readPath(input, path));
    }
    return this.readPath(input, source);
  }

  private readPath(source: unknown, path: string): unknown {
    if (!path) {
      return null;
    }
    const parts = path.split('.');
    return this.readPathParts(source, parts);
  }

  private readPathParts(source: unknown, parts: string[]): unknown {
    if (parts.length === 0) {
      return source;
    }
    if (source == null) {
      return null;
    }

    const [current, ...rest] = parts;
    const isArraySegment = current.endsWith('[]');
    const key = isArraySegment ? current.slice(0, -2) : current;
    const value = typeof source === 'object' && source !== null
      ? (source as Record<string, unknown>)[key]
      : undefined;

    if (isArraySegment) {
      if (!Array.isArray(value)) {
        return [];
      }
      return rest.length === 0
        ? value
        : value.map(item => this.readPathParts(item, rest));
    }

    return this.readPathParts(value, rest);
  }

  private assignPath(target: Record<string, unknown>, path: string, value: unknown): void {
    const parts = path.split('.');
    this.assignPathParts(target, parts, value);
  }

  private assignPathParts(target: Record<string, unknown> | unknown[], parts: string[], value: unknown): void {
    const [current, ...rest] = parts;
    const isArraySegment = current.endsWith('[]');
    const key = isArraySegment ? current.slice(0, -2) : current;

    if (rest.length === 0) {
      if (Array.isArray(target)) {
        return;
      }
      target[key] = value;
      return;
    }

    if (Array.isArray(target)) {
      return;
    }

    if (isArraySegment) {
      const currentValue = Array.isArray(target[key]) ? target[key] as unknown[] : [];
      const inputArray = Array.isArray(value) ? value : [];
      const nextArray = currentValue.length > 0 ? currentValue : inputArray.map(() => ({}));
      target[key] = nextArray;
      nextArray.forEach((item, index) => {
        const itemValue = inputArray[index];
        if (typeof item === 'object' && item !== null) {
          this.assignPathParts(item as Record<string, unknown>, rest, itemValue);
        }
      });
      return;
    }

    const next = typeof target[key] === 'object' && target[key] !== null
      ? target[key] as Record<string, unknown>
      : {};
    target[key] = next;
    this.assignPathParts(next, rest, value);
  }

  private applyTransforms(value: unknown, mapping: FieldMapping): unknown {
    const steps = !mapping.transform
      ? []
      : Array.isArray(mapping.transform)
        ? mapping.transform
        : [mapping.transform];

    return steps.reduce((current, step) => {
      if (current == null) {
        return current;
      }
      switch (step.type) {
        case 'uppercase':
          return String(current).toUpperCase();
        case 'lowercase':
          return String(current).toLowerCase();
        case 'trim':
          return String(current).trim();
        case 'prepend':
          return `${step['value'] ?? ''}${current}`;
        case 'append':
          return `${current}${step['value'] ?? ''}`;
        case 'default':
          return current === '' || current == null ? step['default_value'] : current;
        case 'to_int':
          return Number.parseInt(String(current), 10);
        case 'to_float':
          return Number.parseFloat(String(current));
        case 'to_string':
          return String(current);
        case 'math': {
          const operand = Number(step['operand'] ?? 0);
          const base = Number(current);
          switch (step['operation']) {
            case 'sub': return base - operand;
            case 'mul': return base * operand;
            case 'div': return operand === 0 ? base : base / operand;
            default: return base + operand;
          }
        }
        case 'split':
          return String(current).split(String(step['separator'] ?? ','));
        case 'join':
          return Array.isArray(current) ? current.join(String(step['separator'] ?? ',')) : current;
        case 'replace':
          return String(current).split(String(step['old'] ?? '')).join(String(step['new'] ?? ''));
        default:
          return current;
      }
    }, value);
  }
}
