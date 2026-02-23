import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule } from '@angular/material/stepper';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { forkJoin } from 'rxjs';

import { Connector, ConnectorFieldDef, Flow, COUNTRY_FLAG_MAP } from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';

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
                  <mat-option [value]="a">{{ a }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
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
  `],
})
export class FlowDesignerComponent implements OnInit, OnChanges {
  @Input() editFlow: Flow | null = null;
  @Output() flowCreated = new EventEmitter<Flow>();
  @Output() flowUpdated = new EventEmitter<Flow>();

  connectors: Connector[] = [];
  sourceEvents: string[] = [];
  destActions: string[] = [];
  sourceFieldDefs: ConnectorFieldDef[] = [];
  destFieldDefs: ConnectorFieldDef[] = [];
  saving = false;

  sourceForm: FormGroup;
  destForm: FormGroup;
  mappingForm: FormGroup;

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

  ngOnInit(): void {
    forkJoin({
      connectors: this.api.listConnectors(),
      instances: this.api.listConnectorInstances(),
    }).subscribe(({ connectors, instances }) => {
      const activeKeys = new Set(
        instances.filter(i => i.is_enabled).map(i => `${i.connector_name}:${i.connector_version}`)
      );
      this.connectors = connectors.filter(c => activeKeys.has(`${c.name}:${c.version}`));

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
      }));
    }
  }

  getFlag(code: string): string {
    return COUNTRY_FLAG_MAP[code] ?? code;
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
    this.fieldMappings.push(this.fb.group({ from: [''], to: [''], from_custom: [''], to_custom: [''] }));
  }

  removeMapping(index: number): void {
    this.fieldMappings.removeAt(index);
  }

  saveFlow(): void {
    this.saving = true;
    const rawMapping: { from: string; to: string; from_custom?: string; to_custom?: string }[] =
      this.mappingForm.value.field_mapping ?? [];
    const resolvedMapping = rawMapping.map(m => ({
      from: m.from === '__custom__' ? (m.from_custom ?? '') : m.from,
      to: m.to === '__custom__' ? (m.to_custom ?? '') : m.to,
    }));
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
}
