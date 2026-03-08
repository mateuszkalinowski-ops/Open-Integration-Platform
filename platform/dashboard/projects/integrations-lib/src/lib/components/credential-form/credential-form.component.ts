import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSelectModule } from '@angular/material/select';

import { Connector, ConfigFieldType, CredentialStoreRequest, CredentialValidationResult } from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';

@Component({
  selector: 'pinquark-credential-form',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatSlideToggleModule,
    MatSelectModule,
  ],
  template: `
    <div class="credential-form" *ngIf="connector">
      <h3>{{ editMode ? 'Edit' : 'Add' }} credentials: {{ connector.display_name }}</h3>

      <form [formGroup]="form" (ngSubmit)="save()">
        <!-- Credential Name -->
        <div class="credential-form__name-section">
          <mat-form-field appearance="outline" class="credential-form__field">
            <mat-label>Credential name</mat-label>
            <input matInput [ngModel]="credentialName" (ngModelChange)="credentialName = $event"
                   [ngModelOptions]="{standalone: true}"
                   placeholder="e.g. Production, Sandbox, Client-X" />
            <mat-hint>Assign a unique name to distinguish this credential set from others</mat-hint>
          </mat-form-field>
        </div>

        @if (editMode && existingKeys.length > 0) {
          <p class="credential-form__hint">
            Saved keys: <strong>{{ existingKeys.join(', ') }}</strong>.
            Enter new values to overwrite.
          </p>
        }

        @for (row of requiredFieldRows; track $index) {
          <div [class.credential-form__inline-row]="row.length > 1">
            @for (field of row; track field) {
              <ng-container [ngTemplateOutlet]="fieldTpl"
                            [ngTemplateOutletContext]="{ field: field, required: true }">
              </ng-container>
            }
          </div>
        }

        @for (row of optionalFieldRows; track $index) {
          <div [class.credential-form__inline-row]="row.length > 1">
            @for (field of row; track field) {
              <ng-container [ngTemplateOutlet]="fieldTpl"
                            [ngTemplateOutletContext]="{ field: field, required: false }">
              </ng-container>
            }
          </div>
        }

        <ng-template #fieldTpl let-field="field" let-required="required">
          @if (getFieldType(field)?.type === 'boolean') {
            <div class="credential-form__toggle-row">
              <mat-slide-toggle [formControlName]="field" color="primary">
                {{ getFieldLabel(field) }}{{ required ? ' *' : '' }}
              </mat-slide-toggle>
            </div>
          } @else if (getFieldType(field)?.type === 'select') {
            <mat-form-field appearance="outline" class="credential-form__field">
              <mat-label>{{ getFieldLabel(field) }}{{ required ? ' *' : '' }}</mat-label>
              <mat-select [formControlName]="field">
                @for (opt of getFieldType(field)?.options ?? []; track opt.value) {
                  <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
          } @else {
            <mat-form-field appearance="outline" class="credential-form__field">
              <mat-label>{{ getFieldLabel(field) }}{{ required ? ' *' : '' }}</mat-label>
              <input matInput [formControlName]="field"
                     [type]="isSecretField(field) && !showPasswords ? 'password' : 'text'"
                     [placeholder]="editMode && isSecretField(field) && existingKeys.includes(field) ? '(saved — enter new value to overwrite)' : ''" />
            </mat-form-field>
          }
        </ng-template>

        @if (validationResult) {
          <div class="credential-form__validation"
               [class.credential-form__validation--success]="validationResult.status === 'success'"
               [class.credential-form__validation--failed]="validationResult.status === 'failed'"
               [class.credential-form__validation--unsupported]="validationResult.status === 'unsupported'">
            <mat-icon>{{ validationResult.status === 'success' ? 'check_circle' : validationResult.status === 'failed' ? 'error' : 'info' }}</mat-icon>
            <span>{{ validationResult.message }}</span>
            @if (validationResult.response_time_ms) {
              <span class="credential-form__validation-time">({{ validationResult.response_time_ms }}ms)</span>
            }
          </div>
        }

        <div class="credential-form__actions">
          <button mat-icon-button type="button" (click)="showPasswords = !showPasswords">
            <mat-icon>{{ showPasswords ? 'visibility_off' : 'visibility' }}</mat-icon>
          </button>
          <div>
            <button mat-button type="button" (click)="cancelled.emit()" style="margin-right: 8px;">Cancel</button>
            <button mat-stroked-button type="button"
                    (click)="testConnection()"
                    [disabled]="validating"
                    style="margin-right: 8px;">
              <mat-icon style="font-size: 18px; height: 18px; width: 18px; margin-right: 4px;">wifi_tethering</mat-icon>
              {{ validating ? 'Testing...' : 'Test connection' }}
            </button>
            <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || saving || !credentialName.trim()">
              {{ saving ? 'Saving...' : (editMode ? 'Save changes' : 'Save credentials') }}
            </button>
          </div>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .credential-form__field { width: 100%; margin-bottom: 8px; }
    .credential-form__name-section {
      margin-bottom: 20px;
      padding: 16px;
      background: #e3f2fd;
      border-radius: 8px;
      border-left: 4px solid #1565c0;
    }
    .credential-form__name-section .credential-form__field { margin-bottom: 0; }
    .credential-form__toggle-row {
      margin-bottom: 16px;
      padding: 12px 16px;
      border: 1px solid rgba(0, 0, 0, 0.12);
      border-radius: 4px;
      background: #fafafa;
    }
    .credential-form__inline-row {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
    .credential-form__inline-row .credential-form__field { flex: 1; min-width: 0; }
    .credential-form__inline-row .credential-form__toggle-row { flex: 1; min-width: 0; }
    .credential-form__actions { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
    .credential-form__hint { color: rgba(0,0,0,0.54); font-size: 13px; margin-bottom: 12px; }
    .credential-form__validation {
      display: flex; align-items: center; gap: 8px;
      padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px;
    }
    .credential-form__validation--success { background: #e8f5e9; color: #2e7d32; }
    .credential-form__validation--failed { background: #fbe9e7; color: #c62828; }
    .credential-form__validation--unsupported { background: #fff3e0; color: #e65100; }
    .credential-form__validation mat-icon { font-size: 20px; height: 20px; width: 20px; }
    .credential-form__validation-time { opacity: 0.7; font-size: 12px; }
  `],
})
export class CredentialFormComponent implements OnInit {
  @Input() connector!: Connector;
  @Input() connectorName = '';
  @Input() credentialName = 'default';
  @Input() editMode = false;
  @Input() existingKeys: string[] = [];
  @Input() existingValues: Record<string, string> = {};
  @Output() saved = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();

  form!: FormGroup;
  showPasswords = false;
  saving = false;
  validating = false;
  validationResult: CredentialValidationResult | null = null;
  requiredFieldRows: string[][] = [];
  optionalFieldRows: string[][] = [];
  private originalCredentialName = '';

  constructor(
    private readonly fb: FormBuilder,
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.originalCredentialName = this.credentialName;
    const controls: Record<string, unknown[]> = {};
    const fieldTypes = this.connector?.config_schema?.field_types ?? {};

    for (const field of this.connector?.config_schema?.required ?? []) {
      const ft = fieldTypes[field];
      if (ft?.type === 'boolean') {
        const val = this.existingValues[field];
        controls[field] = [val === 'true' || val === '1' || ft.default === true];
      } else {
        const prefill = this.existingValues[field] ?? (ft?.default != null ? String(ft.default) : '');
        controls[field] = [
          prefill,
          this.editMode && this.existingKeys.includes(field) ? [] : Validators.required,
        ];
      }
    }
    for (const field of this.connector?.config_schema?.optional ?? []) {
      const ft = fieldTypes[field];
      if (ft?.type === 'boolean') {
        const val = this.existingValues[field];
        controls[field] = [val === 'true' || val === '1' || (val == null && ft.default === true)];
      } else {
        const prefill = this.existingValues[field] ?? (ft?.default != null ? String(ft.default) : '');
        controls[field] = [prefill];
      }
    }
    this.form = this.fb.group(controls);

    this.requiredFieldRows = this.buildFieldRows(this.connector?.config_schema?.required ?? []);
    this.optionalFieldRows = this.buildFieldRows(this.connector?.config_schema?.optional ?? []);
  }

  buildFieldRows(fields: string[]): string[][] {
    const rows: string[][] = [];
    const fieldTypes = this.connector?.config_schema?.field_types ?? {};
    let currentRow: string[] = [];
    let currentRowId: string | undefined;

    for (const field of fields) {
      const ft = fieldTypes[field];
      const rowId = ft?.row;

      if (rowId && rowId === currentRowId) {
        currentRow.push(field);
      } else {
        if (currentRow.length > 0) {
          rows.push(currentRow);
        }
        currentRow = [field];
        currentRowId = rowId;
      }
    }
    if (currentRow.length > 0) {
      rows.push(currentRow);
    }
    return rows;
  }

  getFieldType(field: string): ConfigFieldType | undefined {
    return this.connector?.config_schema?.field_types?.[field];
  }

  getFieldLabel(field: string): string {
    return this.getFieldType(field)?.label ?? field;
  }

  isSecretField(field: string): boolean {
    const lower = field.toLowerCase();
    return ['password', 'secret', 'token', 'key'].some(p => lower.includes(p));
  }

  testConnection(): void {
    this.validating = true;
    this.validationResult = null;

    const fieldTypes = this.connector?.config_schema?.field_types ?? {};
    const credentials: Record<string, string> = {};
    for (const [key, value] of Object.entries(this.form.value)) {
      if (fieldTypes[key]?.type === 'boolean') {
        credentials[key] = value ? 'true' : 'false';
      } else if (value) {
        credentials[key] = value as string;
      }
    }

    const name = this.connectorName || this.connector.name;
    this.api.validateCredentials(name, this.credentialName, Object.keys(credentials).length > 0 ? credentials : undefined).subscribe({
      next: (result) => {
        this.validating = false;
        this.validationResult = result;
      },
      error: () => {
        this.validating = false;
        this.validationResult = { status: 'failed', message: 'Blad walidacji polaczenia' };
      },
    });
  }

  save(): void {
    if (this.form.invalid || !this.credentialName.trim()) return;
    this.saving = true;

    const fieldTypes = this.connector?.config_schema?.field_types ?? {};
    const credentials: Record<string, string> = {};
    for (const [key, value] of Object.entries(this.form.value)) {
      if (fieldTypes[key]?.type === 'boolean') {
        credentials[key] = value ? 'true' : 'false';
      } else if (value) {
        credentials[key] = value as string;
      }
    }

    const nameChanged = this.editMode && this.originalCredentialName !== this.credentialName;

    if (Object.keys(credentials).length === 0 && !nameChanged) {
      this.saving = false;
      this.snackBar.open('No values to save', 'OK', { duration: 3000 });
      return;
    }

    const request: CredentialStoreRequest = {
      connector_name: this.connectorName || this.connector.name,
      credential_name: this.credentialName,
      credentials,
    };
    if (nameChanged) {
      request.old_credential_name = this.originalCredentialName;
    }

    this.api.storeCredentials(request).subscribe({
      next: () => {
        this.saving = false;
        this.originalCredentialName = this.credentialName;
        this.snackBar.open('Credentials saved', 'OK', { duration: 3000 });
        this.saved.emit();
      },
      error: () => {
        this.saving = false;
        this.snackBar.open('Nie udalo sie zapisac credentials', 'Ponow', { duration: 5000 });
      },
    });
  }
}
