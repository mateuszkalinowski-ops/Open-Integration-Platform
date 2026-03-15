import { Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule } from '@angular/material/stepper';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { forkJoin, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { Connector, ConnectorFieldDef, Flow, FieldMapping, COUNTRY_FLAG_MAP } from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';
import { VisualFieldMapperComponent } from '../visual-field-mapper/visual-field-mapper.component';

@Component({
  selector: 'pinquark-flow-designer',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatStepperModule,
    MatSnackBarModule,
    VisualFieldMapperComponent,
  ],
  template: `
    <div class="flow-designer">
      <h3>{{ editFlow ? 'Edit Flow' : 'Create Flow' }}</h3>
      <mat-stepper [linear]="!editFlow" #stepper>
        <!-- Step 1: Source -->
        <mat-step [stepControl]="sourceForm">
          <ng-template matStepLabel>Source</ng-template>
          <form [formGroup]="sourceForm">
            <mat-form-field appearance="outline" class="flow-designer__field">
              <mat-label>Source Connector</mat-label>
              <mat-select formControlName="source_connector" (selectionChange)="onSourceConnectorChange()">
                @for (c of connectors; track c.name) {
                  <mat-option [value]="c.name">@if (c.country) {{{ getFlag(c.country) }} }{{ c.display_name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline" class="flow-designer__field">
              <mat-label>Event</mat-label>
              <mat-select formControlName="source_event" (selectionChange)="onSourceEventChange()">
                @for (e of sourceEvents; track e) {
                  <mat-option [value]="e">{{ e }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <button mat-button matStepperNext color="primary">Next</button>
          </form>
        </mat-step>

        <!-- Step 2: Destination -->
        <mat-step [stepControl]="destForm">
          <ng-template matStepLabel>Destination</ng-template>
          <form [formGroup]="destForm">
            <mat-form-field appearance="outline" class="flow-designer__field">
              <mat-label>Destination Connector</mat-label>
              <mat-select formControlName="destination_connector" (selectionChange)="onDestConnectorChange()">
                @for (c of connectors; track c.name) {
                  <mat-option [value]="c.name">@if (c.country) {{{ getFlag(c.country) }} }{{ c.display_name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline" class="flow-designer__field">
              <mat-label>Action</mat-label>
              <mat-select formControlName="destination_action" (selectionChange)="onDestActionChange()">
                @for (a of destActions; track a) {
                  <mat-option [value]="a">{{ getActionDisplayLabel(a) }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            @if (getSelectedActionDescription()) {
              <p class="flow-designer__hint">{{ getSelectedActionDescription() }}</p>
            }
            <button mat-button matStepperPrevious>Back</button>
            <button mat-button matStepperNext color="primary">Next</button>
          </form>
        </mat-step>

        <!-- Step 3: Mapping & Name -->
        <mat-step>
          <ng-template matStepLabel>Mapping</ng-template>
          <form [formGroup]="mappingForm">
            <mat-form-field appearance="outline" class="flow-designer__field">
              <mat-label>Flow Name</mat-label>
              <input matInput formControlName="name" />
            </mat-form-field>

            <h4>Field Mapping</h4>
            <pinquark-visual-field-mapper
              [sourceFields]="sourceFieldDefs"
              [destinationFields]="destFieldDefs"
              [mappings]="visualMappings"
              [contextHint]="mappingContextHint"
              [heading]="'Visual Mapper'"
              [description]="'Create mappings visually or generate suggestions automatically.'"
              [sourceLabel]="'Source event'"
              [destinationLabel]="'Destination action'"
              (mappingsChange)="onVisualMappingsChange($event)"
            ></pinquark-visual-field-mapper>

            <div class="flow-designer__manual-toggle">
              <button mat-stroked-button type="button" (click)="showManualMapping = !showManualMapping">
                <mat-icon>{{ showManualMapping ? 'expand_less' : 'edit_note' }}</mat-icon>
                {{ showManualMapping ? 'Hide Manual Editor' : 'Open Manual Editor' }}
              </button>
            </div>

            @if (showManualMapping) {
            @if (sourceFieldDefs.length === 0 && destFieldDefs.length === 0) {
              <p class="flow-designer__hint">No fields defined — enter paths manually.</p>
            }
            <div formArrayName="field_mapping">
              @for (mapping of fieldMappings.controls; track $index; let i = $index) {
                <div class="flow-designer__mapping-row" [formGroupName]="i">
                  @if (sourceFieldDefs.length > 0) {
                    <mat-form-field appearance="outline">
                      <mat-label>From (source)</mat-label>
                      <mat-select formControlName="from">
                        @for (f of sourceFieldDefs; track f.field) {
                          <mat-option [value]="f.field">{{ f.label }} ({{ f.field }})</mat-option>
                        }
                        <mat-option value="__custom__">-- Custom value --</mat-option>
                      </mat-select>
                    </mat-form-field>
                    @if (getFromValue(i) === '__custom__') {
                      <mat-form-field appearance="outline" class="flow-designer__custom-input">
                        <mat-label>Custom value</mat-label>
                        <input matInput formControlName="from_custom" placeholder="enter path or constant" />
                      </mat-form-field>
                    }
                  } @else {
                    <mat-form-field appearance="outline">
                      <mat-label>From (source)</mat-label>
                      <input matInput formControlName="from" placeholder="source.field.path" />
                    </mat-form-field>
                  }
                  <mat-icon>arrow_forward</mat-icon>
                  @if (destFieldDefs.length > 0) {
                    <mat-form-field appearance="outline">
                      <mat-label>To (destination)</mat-label>
                      <mat-select formControlName="to">
                        @for (f of destFieldDefs; track f.field) {
                          <mat-option [value]="f.field">
                            {{ f.label }} ({{ f.field }})@if (f.required) { *}
                          </mat-option>
                        }
                        <mat-option value="__custom__">-- Custom value --</mat-option>
                      </mat-select>
                    </mat-form-field>
                    @if (getToValue(i) === '__custom__') {
                      <mat-form-field appearance="outline" class="flow-designer__custom-input">
                        <mat-label>Custom value</mat-label>
                        <input matInput formControlName="to_custom" placeholder="enter path" />
                      </mat-form-field>
                    }
                  } @else {
                    <mat-form-field appearance="outline">
                      <mat-label>To (destination)</mat-label>
                      <input matInput formControlName="to" placeholder="dest.field.path" />
                    </mat-form-field>
                  }
                  <button mat-icon-button (click)="removeMapping(i)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              }
            </div>
            <button mat-button (click)="addMapping()">
              <mat-icon>add</mat-icon> Add Mapping
            </button>
            }

            @if (missingRequiredFields.length > 0) {
              <p class="flow-designer__hint flow-designer__hint--warn">
                Wymagane pola docelowe bez mapowania: {{ missingRequiredFields.join(', ') }}
              </p>
            }

            <div class="flow-designer__actions">
              <button mat-button matStepperPrevious>Back</button>
              <button mat-raised-button color="primary" (click)="saveFlow()" [disabled]="saving">
                {{ saving ? (editFlow ? 'Saving...' : 'Creating...') : (editFlow ? 'Save Flow' : 'Create Flow') }}
              </button>
            </div>
          </form>
        </mat-step>
      </mat-stepper>
    </div>
  `,
  styles: [`
    .flow-designer__field { width: 100%; margin-bottom: 8px; }
    .flow-designer__mapping-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }
    .flow-designer__mapping-row mat-form-field { flex: 1; min-width: 180px; }
    .flow-designer__custom-input { flex: 0.8; }
    .flow-designer__actions { display: flex; justify-content: space-between; margin-top: 24px; }
    .flow-designer__hint { color: #666; font-size: 13px; margin-bottom: 12px; }
    .flow-designer__hint--warn { color: #e65100; }
    .flow-designer__manual-toggle { margin: 14px 0 10px; }
  `],
})
export class FlowDesignerComponent implements OnInit, OnChanges, OnDestroy {
  @Input() editFlow: Flow | null = null;
  @Output() flowCreated = new EventEmitter<Flow>();
  @Output() flowUpdated = new EventEmitter<Flow>();

  connectors: Connector[] = [];
  sourceEvents: string[] = [];
  destActions: string[] = [];
  sourceFieldDefs: ConnectorFieldDef[] = [];
  destFieldDefs: ConnectorFieldDef[] = [];
  saving = false;
  showManualMapping = false;

  sourceForm: FormGroup;
  destForm: FormGroup;
  mappingForm: FormGroup;

  private readonly destroy$ = new Subject<void>();
  private schemaRequestId = 0;

  constructor(
    private readonly fb: FormBuilder,
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar
  ) {
    this.sourceForm = this.fb.group({
      source_connector: ['', Validators.required],
      source_event: ['', Validators.required],
    });
    this.destForm = this.fb.group({
      destination_connector: ['', Validators.required],
      destination_action: ['', Validators.required],
    });
    this.mappingForm = this.fb.group({
      name: ['', Validators.required],
      field_mapping: this.fb.array([]),
    });
  }

  get fieldMappings(): FormArray {
    return this.mappingForm.get('field_mapping') as FormArray;
  }

  get visualMappings(): FieldMapping[] {
    const raw = this.mappingForm.value.field_mapping ?? [];
    return raw
      .map((mapping: any) => {
        const resolved: FieldMapping = {
          from: mapping.from === '__custom__' ? (mapping.from_custom ?? '') : mapping.from,
          to: mapping.to === '__custom__' ? (mapping.to_custom ?? '') : mapping.to,
        };
        if (mapping.sources?.length) resolved.sources = mapping.sources;
        if (mapping.transform) resolved.transform = mapping.transform;
        return resolved;
      })
      .filter((mapping: FieldMapping) => mapping.from || mapping.to || mapping.sources?.length);
  }

  get mappingContextHint(): string {
    const source = this.sourceForm.get('source_connector')?.value || '';
    const event = this.sourceForm.get('source_event')?.value || '';
    const destination = this.destForm.get('destination_connector')?.value || '';
    const action = this.destForm.get('destination_action')?.value || '';
    return `Map ${source}.${event} to ${destination}.${action}`.trim();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngOnInit(): void {
    forkJoin({
      connectors: this.api.listConnectors(),
      instances: this.api.listConnectorInstances(),
    }).pipe(takeUntil(this.destroy$)).subscribe(({ connectors, instances }) => {
      const activeKeys = new Set(
        instances.filter(i => i.is_enabled).map(i => `${i.connector_name}:${i.connector_version}`)
      );
      const active = connectors.filter(c => activeKeys.has(`${c.name}:${c.version}`));
      const byName = new Map<string, typeof active[0]>();
      for (const c of active) {
        const existing = byName.get(c.name);
        if (!existing || this.compareSemver(c.version, existing.version) > 0) {
          byName.set(c.name, c);
        }
      }
      this.connectors = Array.from(byName.values());

      if (this.editFlow) {
        this.populateForm(this.editFlow);
      }
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['editFlow'] && this.editFlow && this.connectors.length > 0) {
      this.populateForm(this.editFlow);
    }
  }

  private populateForm(flow: Flow): void {
    this.sourceForm.patchValue({
      source_connector: flow.source_connector,
      source_event: flow.source_event,
    });
    this.onSourceConnectorChange();
    this.sourceForm.patchValue({ source_event: flow.source_event });
    this.onSourceEventChange();

    this.destForm.patchValue({
      destination_connector: flow.destination_connector,
      destination_action: flow.destination_action,
    });
    this.onDestConnectorChange();
    this.destForm.patchValue({ destination_action: flow.destination_action });
    this.onDestActionChange();

    this.mappingForm.patchValue({ name: flow.name });

    this.fieldMappings.clear();
    for (const m of flow.field_mapping) {
      this.fieldMappings.push(this.fb.group({
        from: [m.from || ''],
        to: [m.to || ''],
        from_custom: [''],
        to_custom: [''],
        sources: [m.sources ?? []],
        transform: [m.transform ?? null],
      }));
    }
  }

  getFlag(code: string): string {
    return COUNTRY_FLAG_MAP[code] ?? code;
  }

  private getSelectedDestinationConnector(): Connector | undefined {
    const connectorName = this.destForm.get('destination_connector')?.value;
    return this.connectors.find(c => c.name === connectorName);
  }

  getActionDisplayLabel(action: string): string {
    const label = this.getSelectedDestinationConnector()?.action_metadata?.[action]?.label?.trim();
    return label ? `${label} (${action})` : action;
  }

  getActionDescription(action: string): string {
    return this.getSelectedDestinationConnector()?.action_metadata?.[action]?.description?.trim() ?? '';
  }

  getSelectedActionDescription(): string {
    const action = this.destForm.get('destination_action')?.value;
    return action ? this.getActionDescription(action) : '';
  }

  onSourceConnectorChange(): void {
    const name = this.sourceForm.get('source_connector')?.value;
    const connector = this.connectors.find(c => c.name === name);
    this.sourceEvents = connector?.events ?? [];
    this.sourceFieldDefs = [];
  }

  onSourceEventChange(): void {
    const connectorName = this.sourceForm.get('source_connector')?.value;
    const eventName = this.sourceForm.get('source_event')?.value;
    const connector = this.connectors.find(c => c.name === connectorName);
    this.sourceFieldDefs = connector?.event_fields?.[eventName] ?? [];
  }

  onDestConnectorChange(): void {
    const name = this.destForm.get('destination_connector')?.value;
    const connector = this.connectors.find(c => c.name === name);
    this.destActions = connector?.actions ?? [];
    this.destFieldDefs = [];
  }

  onDestActionChange(): void {
    const connectorName = this.destForm.get('destination_connector')?.value;
    const actionName = this.destForm.get('destination_action')?.value;
    const connector = this.connectors.find(c => c.name === connectorName);
    this.destFieldDefs = connector?.action_fields?.[actionName] ?? [];
    if (connectorName && actionName) {
      const requestId = ++this.schemaRequestId;
      this.api.getConnectorActionSchema(connectorName, actionName, connector?.version).pipe(
        takeUntil(this.destroy$),
      ).subscribe({
        next: schema => {
          if (requestId !== this.schemaRequestId) return;
          this.destFieldDefs = schema.input_fields.length > 0 ? schema.input_fields : this.destFieldDefs;
        },
        error: () => {
          if (requestId !== this.schemaRequestId) return;
          this.destFieldDefs = connector?.action_fields?.[actionName] ?? [];
        },
      });
    }
  }

  get missingRequiredFields(): string[] {
    const mappedTo = new Set(
      this.fieldMappings.controls.map(c => (c as FormGroup).get('to')?.value).filter(Boolean)
    );
    return this.destFieldDefs
      .filter(f => f.required && !mappedTo.has(f.field))
      .map(f => f.label);
  }

  getFromValue(index: number): string {
    return (this.fieldMappings.at(index) as FormGroup).get('from')?.value ?? '';
  }

  getToValue(index: number): string {
    return (this.fieldMappings.at(index) as FormGroup).get('to')?.value ?? '';
  }

  addMapping(): void {
    this.fieldMappings.push(this.fb.group({
      from: [''], to: [''], from_custom: [''], to_custom: [''],
      sources: [[]], transform: [null],
    }));
  }

  removeMapping(index: number): void {
    this.fieldMappings.removeAt(index);
  }

  onVisualMappingsChange(mappings: FieldMapping[]): void {
    this.fieldMappings.clear();
    for (const mapping of mappings) {
      this.fieldMappings.push(this.fb.group({
        from: [mapping.from || ''],
        to: [mapping.to || ''],
        from_custom: [''],
        to_custom: [''],
        sources: [mapping.sources ?? []],
        transform: [mapping.transform ?? null],
      }));
    }
  }

  saveFlow(): void {
    this.saving = true;
    const rawMapping: any[] = this.mappingForm.value.field_mapping ?? [];
    const resolvedMapping = rawMapping.map(m => {
      const entry: any = {
        from: m.from === '__custom__' ? (m.from_custom ?? '') : m.from,
        to: m.to === '__custom__' ? (m.to_custom ?? '') : m.to,
      };
      if (m.sources?.length) entry.sources = m.sources;
      if (m.transform) entry.transform = m.transform;
      return entry;
    });
    const body = {
      ...this.mappingForm.value,
      ...this.sourceForm.value,
      ...this.destForm.value,
      field_mapping: resolvedMapping,
    };

    if (this.editFlow) {
      this.api.updateFlow(this.editFlow.id, body).subscribe({
        next: (flow) => {
          this.saving = false;
          this.snackBar.open('Flow updated', 'OK', { duration: 3000 });
          this.flowUpdated.emit(flow);
        },
        error: () => {
          this.saving = false;
          this.snackBar.open('Failed to update flow', 'Retry', { duration: 5000 });
        },
      });
    } else {
      this.api.createFlow(body).subscribe({
        next: (flow) => {
          this.saving = false;
          this.snackBar.open('Flow created', 'OK', { duration: 3000 });
          this.flowCreated.emit(flow);
        },
        error: () => {
          this.saving = false;
          this.snackBar.open('Failed to create flow', 'Retry', { duration: 5000 });
        },
      });
    }
  }

  private compareSemver(a: string, b: string): number {
    const pa = a.split(/[^0-9]+/).filter(Boolean).map(Number);
    const pb = b.split(/[^0-9]+/).filter(Boolean).map(Number);
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
      const diff = (pa[i] ?? 0) - (pb[i] ?? 0);
      if (diff !== 0) return diff;
    }
    return 0;
  }
}
