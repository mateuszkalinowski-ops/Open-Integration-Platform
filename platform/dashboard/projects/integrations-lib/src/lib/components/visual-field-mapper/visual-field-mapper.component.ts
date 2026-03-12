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
          <div class="vfm__search">
            <mat-icon class="vfm__search-icon">search</mat-icon>
            <input class="vfm__search-input" [(ngModel)]="searchSource" placeholder="Filter fields..." />
            @if (searchSource) {
              <button class="vfm__search-clear" (click)="searchSource = ''"><mat-icon>close</mat-icon></button>
            }
          </div>
          <div class="vfm__field-list">
            @for (field of filteredSourceFields; track field.field) {
              <button type="button" class="vfm__field"
                [class.vfm__field--selected]="pendingSource?.field === field.field"
                [class.vfm__field--array]="isArrayField(field.field)"
                (click)="selectSource(field)">
                @if (isArrayField(field.field)) {
                  <mat-icon class="vfm__arr-icon">view_list</mat-icon>
                }
                <div class="vfm__field-text">
                  <span class="vfm__field-name">{{ field.label }}</span>
                  <span class="vfm__field-key">{{ field.field }}</span>
                </div>
                <span class="vfm__field-type">{{ field.type }}</span>
              </button>
            }
            <button type="button" class="vfm__field vfm__field--static"
              [class.vfm__field--selected]="pendingSource?.field === '__custom__'"
              (click)="selectSource({ field: '__custom__', label: 'Static value', type: 'static' })">
              <div class="vfm__field-text">
                <span class="vfm__field-name">Static value</span>
                <span class="vfm__field-key">Custom constant or expression</span>
              </div>
              <mat-icon class="vfm__field-static-icon">edit_note</mat-icon>
            </button>
          </div>
        </div>

        <div class="vfm__col vfm__col--center">
          <div class="vfm__col-head">
            <span class="vfm__col-title">Mappings</span>
            <span class="vfm__col-count">{{ mappings.length }}</span>
            <button mat-icon-button class="vfm__add-mapping" (click)="addEmptyMapping()" matTooltip="Add mapping manually">
              <mat-icon>add</mat-icon>
            </button>
          </div>
          <div class="vfm__search">
            <mat-icon class="vfm__search-icon">search</mat-icon>
            <input class="vfm__search-input" [(ngModel)]="searchMapping" placeholder="Filter mappings..." />
            @if (searchMapping) {
              <button class="vfm__search-clear" (click)="searchMapping = ''"><mat-icon>close</mat-icon></button>
            }
          </div>
          @if (mappings.length === 0) {
            <div class="vfm__empty">
              <mat-icon>device_hub</mat-icon>
              <span>No mappings yet. Click a source then a target, or use + to add manually.</span>
            </div>
          } @else {
            <div class="vfm__field-list">
              @for (item of filteredMappings; track mappingKey(item.mapping, item.originalIndex)) {
                <div class="vfm__mc" [class.vfm__mc--expanded]="expandedMappingIndex === item.originalIndex">
                  <!-- Collapsed summary row -->
                  <div class="vfm__mc-summary" (click)="toggleMappingExpand(item.originalIndex)">
                    <mat-icon class="vfm__mc-chevron">{{ expandedMappingIndex === item.originalIndex ? 'expand_more' : 'chevron_right' }}</mat-icon>
                    <span class="vfm__mc-from" [matTooltip]="displaySource(item.mapping)">{{ displaySource(item.mapping) }}</span>
                    <mat-icon class="vfm__mc-arrow">east</mat-icon>
                    <span class="vfm__mc-to" [matTooltip]="displayTarget(item.mapping)">{{ displayTarget(item.mapping) }}</span>
                    @if (getTransformCount(item.mapping) > 0) {
                      <span class="vfm__mc-fx">fx{{ getTransformCount(item.mapping) }}</span>
                    }
                    <button mat-icon-button class="vfm__mc-del" (click)="removeMapping(item.originalIndex); $event.stopPropagation()" matTooltip="Remove">
                      <mat-icon>delete_outline</mat-icon>
                    </button>
                  </div>

                  <!-- Expanded editor -->
                  @if (expandedMappingIndex === item.originalIndex) {
                    <div class="vfm__mc-body" (click)="$event.stopPropagation()">
                      <!-- Sources -->
                      <div class="vfm__mc-section">
                        <span class="vfm__mc-label">Sources</span>
                        @for (src of getMappingSources(item.mapping); track $index; let si = $index) {
                          <div class="vfm__mc-src-row">
                            @if (si > 0) { <span class="vfm__mc-plus">+</span> }
                            <mat-form-field appearance="outline" class="vfm__mc-ff">
                              <mat-label>{{ getMappingSources(item.mapping).length > 1 ? 'Source ' + (si + 1) : 'Source' }}</mat-label>
                              <mat-select [value]="src" (selectionChange)="onSourceFieldChange(item.originalIndex, si, $event.value)">
                                @for (f of sourceFields; track f.field) {
                                  <mat-option [value]="f.field">{{ f.label }} ({{ f.field }})</mat-option>
                                }
                                @if (getMappingSources(item.mapping).length === 1) {
                                  <mat-option value="__custom__">-- Static value --</mat-option>
                                }
                              </mat-select>
                            </mat-form-field>
                            @if (src === '__custom__' && getMappingSources(item.mapping).length === 1) {
                              <mat-form-field appearance="outline" class="vfm__mc-ff vfm__mc-ff--sm">
                                <mat-label>Value</mat-label>
                                <input matInput [value]="item.mapping.from_custom || ''" (input)="onCustomSourceChange(item.originalIndex, $any($event.target).value)" placeholder="Static value" />
                              </mat-form-field>
                            }
                            @if (getMappingSources(item.mapping).length > 1) {
                              <button mat-icon-button class="vfm__mc-rm" (click)="removeMappingSource(item.originalIndex, si)"><mat-icon>close</mat-icon></button>
                            }
                          </div>
                        }
                        <button mat-button class="vfm__mc-add-btn" (click)="addMappingSource(item.originalIndex)"><mat-icon>add</mat-icon> Add source</button>
                      </div>

                      <!-- Target -->
                      <div class="vfm__mc-section">
                        <span class="vfm__mc-label">Target</span>
                        <div class="vfm__mc-src-row">
                          <mat-form-field appearance="outline" class="vfm__mc-ff">
                            <mat-label>Target field</mat-label>
                            <mat-select [value]="item.mapping.to" (selectionChange)="onTargetFieldChange(item.originalIndex, $event.value)">
                              @for (f of destinationFields; track f.field) {
                                <mat-option [value]="f.field">{{ f.label }}@if (f.required) { *} ({{ f.field }})</mat-option>
                              }
                              @if (destinationFields.length === 0) {
                                @for (f of sourceFields; track f.field) {
                                  <mat-option [value]="f.field">{{ f.label }} ({{ f.field }})</mat-option>
                                }
                              }
                              <mat-option value="__custom__">-- Custom path --</mat-option>
                            </mat-select>
                          </mat-form-field>
                          @if (item.mapping.to === '__custom__') {
                            <mat-form-field appearance="outline" class="vfm__mc-ff vfm__mc-ff--sm">
                              <mat-label>Path</mat-label>
                              <input matInput [value]="item.mapping.to_custom || ''" (input)="onCustomTargetChange(item.originalIndex, $any($event.target).value)" placeholder="target.path" />
                            </mat-form-field>
                          }
                        </div>
                      </div>

                      <!-- Transforms -->
                      <div class="vfm__mc-section">
                        <span class="vfm__mc-label">Transforms</span>
                        @for (step of getTransformSteps(item.mapping); track $index; let si = $index) {
                          <div class="vfm__mc-tx">
                            <span class="vfm__mc-tx-badge">fx{{ si + 1 }}</span>
                            <mat-form-field appearance="outline" class="vfm__mc-ff vfm__mc-ff--type">
                              <mat-label>Type</mat-label>
                              <mat-select [value]="step.type" (selectionChange)="updateTransformType(item.originalIndex, si, $event.value)">
                                @for (tt of transformTypes; track tt.value) { <mat-option [value]="tt.value">{{ tt.label }}</mat-option> }
                              </mat-select>
                            </mat-form-field>
                            @for (cfgKey of getTransformConfigFields(step.type); track cfgKey) {
                              <mat-form-field appearance="outline" class="vfm__mc-ff vfm__mc-ff--cfg">
                                <mat-label>{{ cfgKey }}</mat-label>
                                <input matInput [value]="step[cfgKey] ?? ''" (change)="updateTransformConfig(item.originalIndex, si, cfgKey, $event)" />
                              </mat-form-field>
                            }
                            <button mat-icon-button class="vfm__mc-rm" (click)="removeTransformStep(item.originalIndex, si)"><mat-icon>close</mat-icon></button>
                          </div>
                        }
                        <button mat-button class="vfm__mc-add-btn" (click)="addTransformStep(item.originalIndex)"><mat-icon>functions</mat-icon> Add transform</button>
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
          }
        </div>

        <div class="vfm__col">
          <div class="vfm__col-head">
            <span class="vfm__col-title">{{ destinationLabel }}</span>
            <span class="vfm__col-count">{{ destinationFields.length }}</span>
          </div>
          <div class="vfm__search">
            <mat-icon class="vfm__search-icon">search</mat-icon>
            <input class="vfm__search-input" [(ngModel)]="searchDest" placeholder="Filter fields..." />
            @if (searchDest) {
              <button class="vfm__search-clear" (click)="searchDest = ''"><mat-icon>close</mat-icon></button>
            }
          </div>
          <div class="vfm__field-list">
            @for (field of filteredDestFields; track field.field) {
              <button type="button" class="vfm__field"
                [class.vfm__field--mapped]="isMappedTarget(field.field)"
                [class.vfm__field--array]="isArrayField(field.field)"
                (click)="connectTo(field)">
                @if (isArrayField(field.field)) {
                  <mat-icon class="vfm__arr-icon">view_list</mat-icon>
                }
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
            <div class="vfm__preview-col">
              <div class="vfm__preview-col-head">
                <span>Sample input (JSON)</span>
                <div class="vfm__preview-btns">
                  <button mat-stroked-button class="vfm__preview-gen" (click)="generateSampleJson()" [disabled]="aiLoading">
                    <mat-icon>auto_awesome</mat-icon> Generate
                  </button>
                  <button mat-stroked-button class="vfm__preview-gen vfm__preview-run" (click)="generatePreview()">
                    <mat-icon>play_arrow</mat-icon> Run preview
                  </button>
                </div>
              </div>
              <textarea class="vfm__preview-textarea" rows="8" [(ngModel)]="sampleInputJson" placeholder='{ "field": "value" }'></textarea>
            </div>
            <div class="vfm__preview-col">
              <div class="vfm__preview-col-head">
                <span>Mapped output</span>
              </div>
              <div class="vfm__preview-out">
                @if (previewError) { <div class="vfm__preview-err">{{ previewError }}</div> }
                <pre>{{ previewOutputJson }}</pre>
              </div>
            </div>
          </div>
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

    .vfm__layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 1.2fr) minmax(0, 1fr); gap: 8px; align-items: start; }

    .vfm__col { border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; display: flex; flex-direction: column; max-height: 520px; }
    .vfm__col--center { background: #f8fafc; }
    .vfm__col-head { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
    .vfm__col-title { font-size: 12px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.04em; }
    .vfm__col-count { font-size: 11px; font-weight: 700; color: #64748b; background: #f1f5f9; padding: 2px 7px; border-radius: 999px; }

    .vfm__search { display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-bottom: 1px solid #e2e8f0; background: #f8fafc; flex-shrink: 0; }
    .vfm__search-icon { width: 16px; height: 16px; font-size: 16px; color: #94a3b8; flex-shrink: 0; }
    .vfm__search-input { border: none; outline: none; background: transparent; font-size: 12px; color: #334155; flex: 1; min-width: 0; padding: 4px 0; }
    .vfm__search-input::placeholder { color: #94a3b8; }
    .vfm__search-clear { border: none; background: none; cursor: pointer; padding: 0; display: flex; align-items: center; color: #94a3b8; flex-shrink: 0; }
    .vfm__search-clear:hover { color: #64748b; }
    .vfm__search-clear mat-icon { width: 14px; height: 14px; font-size: 14px; }

    .vfm__field-list { display: flex; flex-direction: column; gap: 4px; padding: 6px; overflow-y: auto; flex: 1; min-height: 0; }

    .vfm__field { display: flex; align-items: center; gap: 8px; width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; padding: 7px 10px; cursor: pointer; text-align: left; transition: border-color 0.15s, background 0.15s; flex-shrink: 0; }
    .vfm__field:hover { border-color: #93c5fd; background: #f8fbff; }
    .vfm__field--selected { border-color: #2563eb; background: #eff6ff; }
    .vfm__field--mapped { border-color: #86efac; background: #f0fdf4; }
    .vfm__field-text { min-width: 0; flex: 1; display: flex; flex-direction: column; }
    .vfm__field-name { font-size: 12px; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .vfm__field-key { font-size: 11px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .vfm__field-type { font-size: 10px; color: #94a3b8; white-space: nowrap; flex-shrink: 0; }
    .vfm__field--array { border-left: 3px solid #3b82f6; }
    .vfm__arr-icon { width: 16px; height: 16px; font-size: 16px; color: #3b82f6; flex-shrink: 0; }
    .vfm__field--static { border-style: dashed; border-color: #cbd5e1; background: #f8fafc; }
    .vfm__field--static:hover { border-color: #6366f1; background: #eef2ff; }
    .vfm__field--static.vfm__field--selected { border-color: #6366f1; background: #e0e7ff; }
    .vfm__field-static-icon { width: 18px; height: 18px; font-size: 18px; color: #6366f1; flex-shrink: 0; }
    .vfm__req { color: #dc2626; margin-left: 2px; }

    .vfm__add-mapping { width: 24px !important; height: 24px !important; }
    .vfm__add-mapping mat-icon { font-size: 18px; width: 18px; height: 18px; }

    .vfm__empty { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 28px 12px; color: #94a3b8; font-size: 12px; }
    .vfm__empty mat-icon { width: 20px; height: 20px; font-size: 20px; }

    .vfm__mc { border: 1px solid #e2e8f0; border-radius: 6px; background: #fff; overflow: hidden; transition: border-color 0.15s; flex-shrink: 0; }
    .vfm__mc--expanded { border-color: #93c5fd; }
    .vfm__mc-summary { display: flex; align-items: center; gap: 6px; padding: 8px 10px; cursor: pointer; transition: background 0.12s; min-height: 36px; }
    .vfm__mc-summary:hover { background: #f8fbff; }
    .vfm__mc-chevron { width: 16px; height: 16px; font-size: 16px; color: #94a3b8; flex-shrink: 0; }
    .vfm__mc-from, .vfm__mc-to { flex: 1; min-width: 0; font-size: 12px; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .vfm__mc-arrow { width: 12px; height: 12px; font-size: 12px; color: #94a3b8; flex-shrink: 0; }
    .vfm__mc-fx { font-size: 10px; font-weight: 700; color: #6366f1; background: #eef2ff; padding: 1px 5px; border-radius: 999px; flex-shrink: 0; }
    .vfm__mc-del { width: 24px !important; height: 24px !important; flex-shrink: 0; opacity: 0; transition: opacity 0.12s; }
    .vfm__mc-summary:hover .vfm__mc-del { opacity: 1; }
    .vfm__mc-del mat-icon { font-size: 15px; width: 15px; height: 15px; }

    .vfm__mc-body { padding: 0 10px 10px; border-top: 1px solid #e2e8f0; background: #fafbfc; }
    .vfm__mc-section { padding-top: 8px; }
    .vfm__mc-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8; display: block; margin-bottom: 4px; }
    .vfm__mc-src-row { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 2px; }
    .vfm__mc-plus { font-size: 11px; font-weight: 700; color: #64748b; margin-right: 2px; }
    .vfm__mc-ff { flex: 1; min-width: 120px; }
    .vfm__mc-ff--sm { max-width: 140px; }
    .vfm__mc-ff--type { max-width: 160px; flex: 0 0 auto; }
    .vfm__mc-ff--cfg { min-width: 100px; }
    .vfm__mc-rm { width: 24px !important; height: 24px !important; flex-shrink: 0; }
    .vfm__mc-rm mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .vfm__mc-add-btn { font-size: 11px; height: 28px; line-height: 28px; }
    .vfm__mc-add-btn mat-icon { font-size: 14px; width: 14px; height: 14px; margin-right: 2px; }
    .vfm__mc-tx { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; }
    .vfm__mc-tx-badge { font-size: 10px; font-weight: 700; color: #6366f1; background: #eef2ff; padding: 2px 6px; border-radius: 4px; flex-shrink: 0; }

    .vfm__preview { border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; }
    .vfm__preview-toggle { padding: 8px 12px; cursor: pointer; font-size: 12px; font-weight: 600; color: #475569; display: flex; align-items: center; gap: 6px; list-style: none; }
    .vfm__preview-toggle::-webkit-details-marker { display: none; }
    .vfm__preview-toggle mat-icon { width: 16px; height: 16px; font-size: 16px; }
    .vfm__preview-body { padding: 8px 12px 12px; border-top: 1px solid #e2e8f0; }
    .vfm__preview-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px; }
    .vfm__preview-col { display: flex; flex-direction: column; }
    .vfm__preview-col-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.04em; }
    .vfm__preview-btns { display: flex; gap: 6px; }
    .vfm__preview-gen { font-size: 11px !important; height: 28px !important; line-height: 28px !important; padding: 0 10px !important; }
    .vfm__preview-gen mat-icon { font-size: 14px; width: 14px; height: 14px; margin-right: 4px; }
    .vfm__preview-run { color: #2563eb !important; border-color: #2563eb !important; }
    .vfm__preview-textarea { width: 100%; box-sizing: border-box; min-height: 180px; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; background: #fff; color: #1e293b; font-size: 12px; font-family: 'JetBrains Mono', 'Fira Code', monospace; line-height: 1.5; resize: vertical; outline: none; transition: border-color 0.15s; }
    .vfm__preview-textarea:focus { border-color: #93c5fd; }
    .vfm__preview-textarea::placeholder { color: #cbd5e1; }
    .vfm__preview-out { min-height: 180px; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; background: #fff; color: #1e293b; overflow: auto; font-size: 12px; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
    .vfm__preview-out pre { margin: 0; white-space: pre-wrap; word-break: break-word; line-height: 1.5; }
    .vfm__preview-err { color: #dc2626; font-size: 11px; padding: 6px 8px; margin-bottom: 4px; background: #fef2f2; border-radius: 4px; border: 1px solid #fecaca; }

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
  expandedMappingIndex = -1;
  transformTypes: TransformTypeDef[] = TRANSFORM_TYPES;
  sampleInputJson = '{}';
  previewOutputJson = '{}';
  previewError = '';
  aiLoading = false;

  searchSource = '';
  searchMapping = '';
  searchDest = '';

  get filteredSourceFields(): ConnectorFieldDef[] {
    if (!this.searchSource) return this.sourceFields;
    const q = this.searchSource.toLowerCase();
    return this.sourceFields.filter(f => f.label.toLowerCase().includes(q) || f.field.toLowerCase().includes(q));
  }

  get filteredDestFields(): ConnectorFieldDef[] {
    const sorted = [...this.destinationFields].sort((a, b) => {
      if (a.required && !b.required) return -1;
      if (!a.required && b.required) return 1;
      return 0;
    });
    if (!this.searchDest) return sorted;
    const q = this.searchDest.toLowerCase();
    return sorted.filter(f => f.label.toLowerCase().includes(q) || f.field.toLowerCase().includes(q));
  }

  get filteredMappings(): { mapping: FieldMapping; originalIndex: number }[] {
    const all = this.mappings.map((m, i) => ({ mapping: m, originalIndex: i }));
    if (!this.searchMapping) return all;
    const q = this.searchMapping.toLowerCase();
    return all.filter(({ mapping }) => {
      const src = this.displaySource(mapping).toLowerCase();
      const tgt = this.displayTarget(mapping).toLowerCase();
      return src.includes(q) || tgt.includes(q);
    });
  }

  constructor(
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar,
  ) {}

  isArrayField(field: string): boolean {
    return field.includes('[]');
  }

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
    if (this.pendingSource.field !== '__custom__') {
      delete base.from_custom;
    }
    delete base.sources;

    if (existingIndex >= 0) {
      next[existingIndex] = base;
    } else {
      next.push(base);
    }

    this.pendingSource = null;
    this.emitMappings(next);
  }

  toggleMappingExpand(index: number): void {
    this.expandedMappingIndex = this.expandedMappingIndex === index ? -1 : index;
  }

  addEmptyMapping(): void {
    const next = [...this.mappings, { from: '', to: '' } as FieldMapping];
    this.emitMappings(next);
    this.expandedMappingIndex = next.length - 1;
  }

  getMappingSources(mapping: FieldMapping): string[] {
    if (mapping.sources?.length) return mapping.sources;
    return [mapping.from || ''];
  }

  onSourceFieldChange(mappingIndex: number, sourceIndex: number, value: string): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const sources = [...this.getMappingSources(mapping)];

    if (sources.length === 1 && sourceIndex === 0) {
      mapping.from = value;
      delete mapping.sources;
      if (value !== '__custom__') delete mapping.from_custom;
    } else {
      sources[sourceIndex] = value;
      mapping.sources = sources;
      mapping.from = sources[0];
    }
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  onCustomSourceChange(mappingIndex: number, value: string): void {
    const next = [...this.mappings];
    next[mappingIndex] = { ...next[mappingIndex], from_custom: value };
    this.emitMappings(next);
  }

  addMappingSource(mappingIndex: number): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const sources = [...this.getMappingSources(mapping)];
    sources.push('');
    mapping.sources = sources;
    mapping.from = sources[0];
    delete mapping.from_custom;
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  removeMappingSource(mappingIndex: number, sourceIndex: number): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    const sources = [...this.getMappingSources(mapping)];
    sources.splice(sourceIndex, 1);
    if (sources.length <= 1) {
      mapping.from = sources[0] || '';
      delete mapping.sources;
    } else {
      mapping.sources = sources;
      mapping.from = sources[0];
    }
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  onTargetFieldChange(mappingIndex: number, value: string): void {
    const next = [...this.mappings];
    const mapping = { ...next[mappingIndex] };
    mapping.to = value;
    if (value !== '__custom__') delete mapping.to_custom;
    next[mappingIndex] = mapping;
    this.emitMappings(next);
  }

  onCustomTargetChange(mappingIndex: number, value: string): void {
    const next = [...this.mappings];
    next[mappingIndex] = { ...next[mappingIndex], to_custom: value };
    this.emitMappings(next);
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

  generateSampleJson(): void {
    const sample: Record<string, unknown> = {};
    for (const field of this.sourceFields) {
      const path = field.field;
      if (path.includes('[]')) continue;
      const t = (field.type || 'string').toLowerCase();
      let val: unknown;
      if (t === 'integer' || t === 'number' || t === 'int') {
        val = Math.floor(Math.random() * 9000) + 1000;
      } else if (t === 'boolean' || t === 'bool') {
        val = true;
      } else if (t === 'date') {
        val = '2026-01-15';
      } else if (t === 'datetime') {
        val = '2026-01-15T10:30:00Z';
      } else if (t === 'float' || t === 'decimal') {
        val = Math.round(Math.random() * 1000) / 100;
      } else {
        val = this.sampleValueForLabel(field.label, field.field);
      }
      this.assignPath(sample, path, val);
    }
    this.sampleInputJson = JSON.stringify(sample, null, 2);
  }

  private sampleValueForLabel(label: string, field: string): string {
    const l = (label + ' ' + field).toLowerCase();
    if (l.includes('email')) return 'jan.kowalski@example.com';
    if (l.includes('phone') || l.includes('tel')) return '+48 600 123 456';
    if (l.includes('city') || l.includes('miasto')) return 'Warszawa';
    if (l.includes('street') || l.includes('ulica') || l.includes('address')) return 'ul. Marszałkowska 1';
    if (l.includes('zip') || l.includes('postal') || l.includes('kod')) return '00-001';
    if (l.includes('country') || l.includes('kraj')) return 'PL';
    if (l.includes('name') || l.includes('nazwa') || l.includes('imie')) return 'Jan Kowalski';
    if (l.includes('symbol') || l.includes('code') || l.includes('kod')) return 'DOC-2026-001';
    if (l.includes('currency') || l.includes('waluta')) return 'PLN';
    if (l.includes('price') || l.includes('cena') || l.includes('amount') || l.includes('kwota')) return '129.99';
    if (l.includes('quantity') || l.includes('ilosc') || l.includes('qty')) return '5';
    if (l.includes('status')) return 'active';
    if (l.includes('type') || l.includes('typ')) return 'standard';
    if (l.includes('description') || l.includes('opis')) return 'Sample description';
    if (l.includes('url') || l.includes('link')) return 'https://example.com';
    if (l.includes('id')) return 'ID-' + Math.floor(Math.random() * 90000 + 10000);
    return 'sample_' + field.split('.').pop();
  }

  generatePreview(): void {
    this.previewError = '';
    try {
      const input = JSON.parse(this.sampleInputJson || '{}') as Record<string, unknown>;
      const output: Record<string, unknown> = {};
      for (const mapping of this.mappings) {
        const target = this.resolveTarget(mapping);
        if (!target) continue;
        if (!mapping.sources?.length) {
          const source = mapping.from === '__custom__' ? mapping.from_custom ?? '' : mapping.from;
          if (!source || source === 'undefined') {
            this.assignPath(output, target, null);
            continue;
          }
        }
        let value = this.resolveMappingValue(input, mapping);
        value = this.applyTransforms(value, mapping);
        this.assignPath(output, target, value ?? null);
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
    if (mapping.sources?.length) {
      return mapping.sources.map(path => this.readPathWithFallback(input, path));
    }
    const source = mapping.from === '__custom__' ? mapping.from_custom ?? '' : mapping.from;
    if (!source || source === 'undefined') {
      return null;
    }
    const resolved = this.readPathWithFallback(input, source);
    if (resolved !== null && resolved !== undefined) return resolved;
    const isKnownField = this.sourceFields.some(f => f.field === source);
    if (!isKnownField) return source;
    return null;
  }

  private readPathWithFallback(input: Record<string, unknown>, path: string): unknown {
    const direct = this.readPath(input, path);
    if (direct !== null && direct !== undefined) return direct;
    const key = path.replace(/\[\]/g, '').replace(/\./g, '_');
    if (key in input) return input[key];
    const lastSegment = path.split('.').pop()?.replace('[]', '') || '';
    if (lastSegment && lastSegment !== key && lastSegment in input) return input[lastSegment];
    return undefined;
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
