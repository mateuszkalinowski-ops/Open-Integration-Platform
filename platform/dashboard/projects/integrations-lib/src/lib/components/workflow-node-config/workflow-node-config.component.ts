import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import {
  Connector,
  ConnectorFieldDef,
  WorkflowNode,
  CONDITION_OPERATORS,
  TRANSFORM_TYPES,
  NODE_TYPE_DEFINITIONS,
  ConditionRule,
  FieldMapping,
  TransformStep,
  COUNTRY_FLAG_MAP,
} from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';

@Component({
  selector: 'pinquark-workflow-node-config',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatExpansionModule,
    MatSlideToggleModule,
    MatDividerModule,
    MatChipsModule,
  ],
  template: `
    @if (node) {
      <div class="wnc">
        <div class="wnc__header" [style.border-left-color]="getNodeColor()">
          <mat-icon [style.color]="getNodeColor()">{{ getNodeIcon() }}</mat-icon>
          <div class="wnc__header-text">
            <span class="wnc__type">{{ getNodeTypeLabel() }}</span>
            <span class="wnc__desc">{{ getNodeDescription() }}</span>
          </div>
          <button mat-icon-button (click)="close.emit()"><mat-icon>close</mat-icon></button>
        </div>

        <div class="wnc__body">
          <!-- Common: Label -->
          <mat-form-field appearance="outline" class="wnc__field">
            <mat-label>Label</mat-label>
            <input matInput [(ngModel)]="node.label" (ngModelChange)="emitChange()" placeholder="Node display name" />
          </mat-form-field>

          <!-- TRIGGER -->
          @if (node.type === 'trigger') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Source Connector</mat-label>
              <mat-select [(ngModel)]="cfg['connector_name']" (ngModelChange)="onTriggerConnectorChange()" (openedChange)="onSelectOpen('trigConn', $event)">
                <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['trigConn'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['trigConn'] = $any($event.target).value" placeholder="Search..." /></div>
                @for (c of connectors; track c.name) {
                  @if (matchesFilter('trigConn', c.display_name + ' ' + c.name)) {
                  <mat-option [value]="c.name">@if (c.country) {{{ getFlag(c.country) }} }{{ c.display_name }}</mat-option>
                  }
                }
              </mat-select>
            </mat-form-field>
            @if (credentialNames.length > 0) {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Credentials</mat-label>
                <mat-select [(ngModel)]="cfg['credential_name']" (ngModelChange)="emitChange()">
                  @for (cn of credentialNames; track cn) {
                    <mat-option [value]="cn">
                      <mat-icon style="font-size: 16px; height: 16px; width: 16px; vertical-align: middle; margin-right: 4px;">vpn_key</mat-icon>
                      {{ cn }}
                    </mat-option>
                  }
                </mat-select>
              </mat-form-field>
            } @else if (cfg['connector_name'] && !loadingCredentialNames) {
              <p class="wnc__hint">No credentials configured for this connector.</p>
            }
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Event</mat-label>
              <mat-select [(ngModel)]="cfg['event']" (ngModelChange)="onTriggerEventChange()" (openedChange)="onSelectOpen('trigEvent', $event)">
                <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['trigEvent'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['trigEvent'] = $any($event.target).value" placeholder="Search..." /></div>
                @for (e of triggerEvents; track e) {
                  @if (matchesFilter('trigEvent', e)) {
                  <mat-option [value]="e">{{ e }}</mat-option>
                  }
                }
              </mat-select>
            </mat-form-field>
          }

          <!-- ACTION -->
          @if (node.type === 'action') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Destination Connector</mat-label>
              <mat-select [(ngModel)]="cfg['connector_name']" (ngModelChange)="onActionConnectorChange(); emitChange()" (openedChange)="onSelectOpen('actConn', $event)">
                <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['actConn'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['actConn'] = $any($event.target).value" placeholder="Search..." /></div>
                @for (c of connectors; track c.name) {
                  @if (matchesFilter('actConn', c.display_name + ' ' + c.name)) {
                  <mat-option [value]="c.name">@if (c.country) {{{ getFlag(c.country) }} }{{ c.display_name }}</mat-option>
                  }
                }
              </mat-select>
            </mat-form-field>
            @if (credentialNames.length > 0) {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Credentials</mat-label>
                <mat-select [(ngModel)]="cfg['credential_name']" (ngModelChange)="emitChange()">
                  @for (cn of credentialNames; track cn) {
                    <mat-option [value]="cn">
                      <mat-icon style="font-size: 16px; height: 16px; width: 16px; vertical-align: middle; margin-right: 4px;">vpn_key</mat-icon>
                      {{ cn }}
                    </mat-option>
                  }
                </mat-select>
              </mat-form-field>
            } @else if (cfg['connector_name'] && !loadingCredentialNames) {
              <p class="wnc__hint">No credentials configured for this connector.</p>
            }
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Action</mat-label>
              <mat-select [(ngModel)]="cfg['action']" (ngModelChange)="onActionChange()" (openedChange)="onSelectOpen('actAction', $event)">
                <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['actAction'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['actAction'] = $any($event.target).value" placeholder="Search..." /></div>
                @for (a of actionActions; track a) {
                  @if (matchesFilter('actAction', a)) {
                  <mat-option [value]="a">{{ a }}</mat-option>
                  }
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>On Error</mat-label>
              <mat-select [(ngModel)]="cfg['on_error']" (ngModelChange)="emitChange()">
                <mat-option value="stop">Stop Workflow</mat-option>
                <mat-option value="continue">Continue</mat-option>
                <mat-option value="retry">Retry</mat-option>
              </mat-select>
            </mat-form-field>

            <!-- Unified Field Mapping -->
            <div class="wnc__section-title">
              <span>Field Mapping</span>
              <button mat-icon-button (click)="addFieldMapping()"><mat-icon>add</mat-icon></button>
            </div>
            <ng-container *ngFor="let m of asFieldMappings(cfg['field_mapping']); let i = index">
              <div class="wnc__mc">
                <div class="wnc__mc-row">
                  <div class="wnc__mc-sources">
                    <ng-container *ngFor="let src of getMappingSources(m); let si = index">
                      <div class="wnc__mc-src-item" [class.wnc__mc-src-extra]="si > 0">
                        @if (si > 0) { <span class="wnc__mc-plus">+</span> }
                        @if (sourceFieldDefs.length > 0) {
                          <mat-form-field appearance="outline" class="wnc__mc-src-ff">
                            <mat-label>{{ getMappingSources(m).length > 1 ? 'Source ' + (si + 1) : 'Source' }}</mat-label>
                            <mat-select [value]="src" (selectionChange)="onSourceChange(m, si, $event.value)" (openedChange)="onSelectOpen('srcField', $event)">
                              <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['srcField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['srcField'] = $any($event.target).value" placeholder="Search..." /></div>
                              @for (f of sourceFieldDefs; track f.field) {
                                @if (matchesFilter('srcField', f.label + ' ' + f.field)) {
                                <mat-option [value]="f.field">{{ f.label }}</mat-option>
                                }
                              }
                              @if (getMappingSources(m).length === 1) {
                                <mat-option value="__custom__">-- Static value --</mat-option>
                              }
                            </mat-select>
                          </mat-form-field>
                        } @else {
                          <mat-form-field appearance="outline" class="wnc__mc-src-ff">
                            <mat-label>{{ getMappingSources(m).length > 1 ? 'Source ' + (si + 1) : 'Source' }}</mat-label>
                            <input matInput [value]="src === '__custom__' ? '' : src" (input)="onSourceChange(m, si, $any($event.target).value)" placeholder="path.to.field" />
                          </mat-form-field>
                        }
                        @if (src === '__custom__' && getMappingSources(m).length === 1) {
                          <mat-form-field appearance="outline" class="wnc__mc-custom">
                            <mat-label>Value</mat-label>
                            <input matInput [(ngModel)]="m.from_custom" (ngModelChange)="emitChange()" placeholder="Static value" />
                          </mat-form-field>
                        }
                        @if (getMappingSources(m).length > 1) {
                          <button mat-icon-button class="wnc__mc-rm-src" (click)="removeMappingSource(m, si)"><mat-icon [style.font-size.px]="16">close</mat-icon></button>
                        }
                      </div>
                    </ng-container>
                    <button mat-button class="wnc__mc-add-src" (click)="addMappingSource(m)"><mat-icon [style.font-size.px]="14">add</mat-icon>Add source</button>
                  </div>
                  <mat-icon class="wnc__mapping-arrow">arrow_forward</mat-icon>
                  @if (destFieldDefs.length > 0 || sourceFieldDefs.length > 0) {
                    <mat-form-field appearance="outline" class="wnc__mc-to">
                      <mat-label>Target</mat-label>
                      <mat-select [(ngModel)]="m.to" (ngModelChange)="emitChange()" (openedChange)="onSelectOpen('destField', $event)">
                        <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['destField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['destField'] = $any($event.target).value" placeholder="Search..." /></div>
                        @if (destFieldDefs.length > 0) {
                          @for (f of destFieldDefs; track f.field) {
                            @if (matchesFilter('destField', f.label + ' ' + f.field)) {
                            <mat-option [value]="f.field">{{ f.label }}@if (f.required) { *}</mat-option>
                            }
                          }
                        } @else {
                          @for (f of sourceFieldDefs; track f.field) {
                            @if (matchesFilter('destField', f.label + ' ' + f.field)) {
                            <mat-option [value]="f.field">{{ f.label }}</mat-option>
                            }
                          }
                        }
                        <mat-option value="__custom__">-- Custom --</mat-option>
                      </mat-select>
                    </mat-form-field>
                    @if (m.to === '__custom__') {
                      <mat-form-field appearance="outline" class="wnc__mc-custom">
                        <input matInput [(ngModel)]="m.to_custom" (ngModelChange)="emitChange()" placeholder="target.path" />
                      </mat-form-field>
                    }
                  } @else {
                    <mat-form-field appearance="outline" class="wnc__mc-to">
                      <mat-label>Target</mat-label>
                      <input matInput [(ngModel)]="m.to" (ngModelChange)="emitChange()" placeholder="target.path" />
                    </mat-form-field>
                  }
                  <button mat-icon-button (click)="removeFieldMapping(i)"><mat-icon>delete</mat-icon></button>
                </div>
                <!-- Transform pipeline -->
                <ng-container *ngFor="let step of getTransformSteps(m); let ti = index">
                  <div class="wnc__ts">
                    <span class="wnc__ts-badge">fx{{ ti + 1 }}</span>
                    <mat-form-field appearance="outline" class="wnc__ts-type">
                      <mat-select [value]="step.type" (selectionChange)="onStepTypeChange(m, ti, $event.value)" (openedChange)="onSelectOpen('transform', $event)">
                        <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['transform'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['transform'] = $any($event.target).value" placeholder="Search..." /></div>
                        @for (tt of transformTypes; track tt.value) {
                          @if (matchesFilter('transform', tt.label + ' ' + tt.value)) {
                          <mat-option [value]="tt.value">{{ tt.label }}</mat-option>
                          }
                        }
                      </mat-select>
                    </mat-form-field>
                    <ng-container [ngSwitch]="step.type">
                      <ng-container *ngSwitchCase="'template'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Template</mat-label><input matInput [value]="step['template'] || ''" (input)="setStepProp(m,ti,'template',$any($event.target).value)" placeholder="{{'{'}}{{'{'}}0{{'}'}}{{'}'}} {{'{'}}{{'{'}}1{{'}'}}{{'}'}}" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'format'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Template</mat-label><input matInput [value]="step['template'] || ''" (input)="setStepProp(m,ti,'template',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'regex_extract'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Pattern</mat-label><input matInput [value]="step['pattern'] || ''" (input)="setStepProp(m,ti,'pattern',$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Group</mat-label><input matInput type="number" [value]="step['group'] ?? 0" (input)="setStepProp(m,ti,'group',+$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'regex_replace'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Pattern</mat-label><input matInput [value]="step['pattern'] || ''" (input)="setStepProp(m,ti,'pattern',$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Replacement</mat-label><input matInput [value]="step['replacement'] || ''" (input)="setStepProp(m,ti,'replacement',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'join'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Separator</mat-label><input matInput [value]="step['separator'] || ''" (input)="setStepProp(m,ti,'separator',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'split'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Separator</mat-label><input matInput [value]="step['separator'] || ''" (input)="setStepProp(m,ti,'separator',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'concat'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Separator</mat-label><input matInput [value]="step['separator'] || ''" (input)="setStepProp(m,ti,'separator',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'replace'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Find</mat-label><input matInput [value]="step['old'] || ''" (input)="setStepProp(m,ti,'old',$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Replace with</mat-label><input matInput [value]="step['new'] || ''" (input)="setStepProp(m,ti,'new',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'substring'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Start</mat-label><input matInput type="number" [value]="step['start'] ?? 0" (input)="setStepProp(m,ti,'start',+$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>End</mat-label><input matInput type="number" [value]="step['end'] ?? ''" (input)="setStepProp(m,ti,'end',$any($event.target).value ? +$any($event.target).value : null)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'date_format'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Input format</mat-label><input matInput [value]="step['input_format'] || ''" (input)="setStepProp(m,ti,'input_format',$any($event.target).value)" placeholder="%Y-%m-%d" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Output format</mat-label><input matInput [value]="step['output_format'] || ''" (input)="setStepProp(m,ti,'output_format',$any($event.target).value)" placeholder="%d.%m.%Y" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'math'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Op</mat-label><mat-select [value]="step['operation'] || 'add'" (selectionChange)="setStepProp(m,ti,'operation',$event.value)"><mat-option value="add">+</mat-option><mat-option value="sub">-</mat-option><mat-option value="mul">*</mat-option><mat-option value="div">/</mat-option></mat-select></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Operand</mat-label><input matInput type="number" [value]="step['operand'] ?? 0" (input)="setStepProp(m,ti,'operand',+$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'prepend'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Prefix</mat-label><input matInput [value]="step['value'] || ''" (input)="setStepProp(m,ti,'value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'append'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Suffix</mat-label><input matInput [value]="step['value'] || ''" (input)="setStepProp(m,ti,'value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'default'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Default</mat-label><input matInput [value]="step['default_value'] || ''" (input)="setStepProp(m,ti,'default_value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'coalesce'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Default</mat-label><input matInput [value]="step['default_value'] || ''" (input)="setStepProp(m,ti,'default_value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'map'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Map (JSON)</mat-label><textarea matInput [value]="getStepMapJson(step)" (input)="setStepMapJson(m,ti,$any($event.target).value)" rows="2" placeholder='{{"{"}} "old": "new" {{"}"}}' ></textarea></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'lookup'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Table (JSON)</mat-label><textarea matInput [value]="getStepMapJson(step)" (input)="setStepMapJson(m,ti,$any($event.target).value)" rows="2" placeholder='{{"{"}} "old": "new" {{"}"}}' ></textarea></mat-form-field></ng-container>
                    </ng-container>
                    <button mat-icon-button class="wnc__ts-rm" (click)="removeTransformStep(m, ti)"><mat-icon [style.font-size.px]="16">close</mat-icon></button>
                  </div>
                </ng-container>
                <button mat-button class="wnc__mc-add-fx" (click)="addTransformStep(m)"><mat-icon [style.font-size.px]="14">functions</mat-icon>Add transform</button>
              </div>
            </ng-container>
          }

          <!-- CONDITION / FILTER -->
          @if (node.type === 'condition' || node.type === 'filter') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Logic</mat-label>
              <mat-select [(ngModel)]="cfg['logic']" (ngModelChange)="emitChange()">
                <mat-option value="and">ALL conditions must match (AND)</mat-option>
                <mat-option value="or">ANY condition must match (OR)</mat-option>
              </mat-select>
            </mat-form-field>
            <div class="wnc__section-title">
              <span>Conditions</span>
              <button mat-icon-button (click)="addCondition()"><mat-icon>add</mat-icon></button>
            </div>
            @for (c of asConditions(cfg['conditions']); track $index; let i = $index) {
              <div class="wnc__condition-row">
                @if (sourceFieldDefs.length > 0) {
                  <mat-form-field appearance="outline" class="wnc__cond-field">
                    <mat-label>Field</mat-label>
                    <mat-select [(ngModel)]="c.field" (ngModelChange)="emitChange()" (openedChange)="onSelectOpen('condField', $event)">
                      <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['condField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['condField'] = $any($event.target).value" placeholder="Search..." /></div>
                      @for (f of sourceFieldDefs; track f.field) {
                        @if (matchesFilter('condField', f.label + ' ' + f.field)) {
                        <mat-option [value]="f.field">{{ f.label }}</mat-option>
                        }
                      }
                      <mat-option value="__custom__">-- Custom value --</mat-option>
                    </mat-select>
                  </mat-form-field>
                  @if (c.field === '__custom__') {
                    <mat-form-field appearance="outline" class="wnc__cond-custom">
                      <input matInput [(ngModel)]="c.field_custom" (ngModelChange)="emitChange()" placeholder="path" />
                    </mat-form-field>
                  }
                } @else {
                  <mat-form-field appearance="outline" class="wnc__cond-field">
                    <mat-label>Field</mat-label>
                    <input matInput [(ngModel)]="c.field" (ngModelChange)="emitChange()" placeholder="data.path" />
                  </mat-form-field>
                }
                <mat-form-field appearance="outline" class="wnc__cond-op">
                  <mat-label>Operator</mat-label>
                  <mat-select [(ngModel)]="c.operator" (ngModelChange)="emitChange()" (openedChange)="onSelectOpen('condOp', $event)">
                    <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['condOp'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['condOp'] = $any($event.target).value" placeholder="Search..." /></div>
                    @for (op of conditionOperators; track op.value) {
                      @if (matchesFilter('condOp', op.label + ' ' + op.value)) {
                      <mat-option [value]="op.value">{{ op.label }}</mat-option>
                      }
                    }
                  </mat-select>
                </mat-form-field>
                @if (!isUnaryOperator(c.operator)) {
                  <mat-form-field appearance="outline" class="wnc__cond-val">
                    <mat-label>Value</mat-label>
                    <input matInput [(ngModel)]="c.value" (ngModelChange)="emitChange()" />
                  </mat-form-field>
                }
                <button mat-icon-button (click)="removeCondition(i)"><mat-icon>delete</mat-icon></button>
              </div>
            }
          }

          <!-- SWITCH -->
          @if (node.type === 'switch') {
            @if (sourceFieldDefs.length > 0) {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Field to switch on</mat-label>
                <mat-select [(ngModel)]="cfg['field']" (ngModelChange)="emitChange()" (openedChange)="onSelectOpen('switchField', $event)">
                  <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['switchField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['switchField'] = $any($event.target).value" placeholder="Search..." /></div>
                  @for (f of sourceFieldDefs; track f.field) {
                    @if (matchesFilter('switchField', f.label + ' ' + f.field)) {
                    <mat-option [value]="f.field">{{ f.label }} ({{ f.field }})</mat-option>
                    }
                  }
                  <mat-option value="__custom__">-- Custom value --</mat-option>
                </mat-select>
              </mat-form-field>
              @if (cfg['field'] === '__custom__') {
                <mat-form-field appearance="outline" class="wnc__field">
                  <mat-label>Custom path</mat-label>
                  <input matInput [(ngModel)]="cfg['field_custom']" (ngModelChange)="emitChange()" placeholder="data.status" />
                </mat-form-field>
              }
            } @else {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Field to switch on</mat-label>
                <input matInput [(ngModel)]="cfg['field']" (ngModelChange)="emitChange()" placeholder="data.status" />
              </mat-form-field>
            }
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Default Handle</mat-label>
              <input matInput [(ngModel)]="cfg['default_handle']" (ngModelChange)="emitChange()" />
            </mat-form-field>
            <div class="wnc__section-title">
              <span>Cases</span>
              <button mat-icon-button (click)="addSwitchCase()"><mat-icon>add</mat-icon></button>
            </div>
            @for (c of asSwitchCases(cfg['cases']); track $index; let i = $index) {
              <div class="wnc__mapping-row">
                <mat-form-field appearance="outline" class="wnc__mapping-field">
                  <mat-label>Value</mat-label>
                  <input matInput [(ngModel)]="c.value" (ngModelChange)="emitChange()" />
                </mat-form-field>
                <mat-icon class="wnc__mapping-arrow">arrow_forward</mat-icon>
                <mat-form-field appearance="outline" class="wnc__mapping-field">
                  <mat-label>Handle</mat-label>
                  <input matInput [(ngModel)]="c.handle" (ngModelChange)="emitChange()" />
                </mat-form-field>
                <button mat-icon-button (click)="removeSwitchCase(i)"><mat-icon>delete</mat-icon></button>
              </div>
            }
          }

          <!-- TRANSFORM -->
          @if (node.type === 'transform') {
            <div class="wnc__section-title">
              <span>Field Mappings</span>
              <button mat-icon-button (click)="addTransformMapping()"><mat-icon>add</mat-icon></button>
            </div>
            <ng-container *ngFor="let m of asFieldMappings(cfg['mappings']); let i = index">
              <div class="wnc__mc">
                <div class="wnc__mc-row">
                  <div class="wnc__mc-sources">
                    <ng-container *ngFor="let src of getMappingSources(m); let si = index">
                      <div class="wnc__mc-src-item" [class.wnc__mc-src-extra]="si > 0">
                        @if (si > 0) { <span class="wnc__mc-plus">+</span> }
                        @if (sourceFieldDefs.length > 0) {
                          <mat-form-field appearance="outline" class="wnc__mc-src-ff">
                            <mat-label>{{ getMappingSources(m).length > 1 ? 'Source ' + (si + 1) : 'Source' }}</mat-label>
                            <mat-select [value]="src" (selectionChange)="onSourceChange(m, si, $event.value)" (openedChange)="onSelectOpen('srcField', $event)">
                              <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['srcField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['srcField'] = $any($event.target).value" placeholder="Search..." /></div>
                              @for (f of sourceFieldDefs; track f.field) {
                                @if (matchesFilter('srcField', f.label + ' ' + f.field)) {
                                <mat-option [value]="f.field">{{ f.label }}</mat-option>
                                }
                              }
                              @if (getMappingSources(m).length === 1) {
                                <mat-option value="__custom__">-- Static value --</mat-option>
                              }
                            </mat-select>
                          </mat-form-field>
                        } @else {
                          <mat-form-field appearance="outline" class="wnc__mc-src-ff">
                            <mat-label>{{ getMappingSources(m).length > 1 ? 'Source ' + (si + 1) : 'Source' }}</mat-label>
                            <input matInput [value]="src === '__custom__' ? '' : src" (input)="onSourceChange(m, si, $any($event.target).value)" placeholder="path.to.field" />
                          </mat-form-field>
                        }
                        @if (src === '__custom__' && getMappingSources(m).length === 1) {
                          <mat-form-field appearance="outline" class="wnc__mc-custom">
                            <mat-label>Value</mat-label>
                            <input matInput [(ngModel)]="m.from_custom" (ngModelChange)="emitChange()" placeholder="Static value" />
                          </mat-form-field>
                        }
                        @if (getMappingSources(m).length > 1) {
                          <button mat-icon-button class="wnc__mc-rm-src" (click)="removeMappingSource(m, si)"><mat-icon [style.font-size.px]="16">close</mat-icon></button>
                        }
                      </div>
                    </ng-container>
                    <button mat-button class="wnc__mc-add-src" (click)="addMappingSource(m)"><mat-icon [style.font-size.px]="14">add</mat-icon>Add source</button>
                  </div>
                  <mat-icon class="wnc__mapping-arrow">arrow_forward</mat-icon>
                  @if (destFieldDefs.length > 0 || sourceFieldDefs.length > 0) {
                    <mat-form-field appearance="outline" class="wnc__mc-to">
                      <mat-label>Target</mat-label>
                      <mat-select [(ngModel)]="m.to" (ngModelChange)="emitChange()" (openedChange)="onSelectOpen('destField', $event)">
                        <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['destField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['destField'] = $any($event.target).value" placeholder="Search..." /></div>
                        @for (f of destFieldDefs.length > 0 ? destFieldDefs : sourceFieldDefs; track f.field) {
                          @if (matchesFilter('destField', f.label + ' ' + f.field)) {
                          <mat-option [value]="f.field">{{ f.label }}</mat-option>
                          }
                        }
                        <mat-option value="__custom__">-- Custom --</mat-option>
                      </mat-select>
                    </mat-form-field>
                    @if (m.to === '__custom__') {
                      <mat-form-field appearance="outline" class="wnc__mc-custom">
                        <input matInput [(ngModel)]="m.to_custom" (ngModelChange)="emitChange()" placeholder="new.field.name" />
                      </mat-form-field>
                    }
                  } @else {
                    <mat-form-field appearance="outline" class="wnc__mc-to">
                      <mat-label>Target</mat-label>
                      <input matInput [(ngModel)]="m.to" (ngModelChange)="emitChange()" placeholder="new.field.name" />
                    </mat-form-field>
                  }
                  <button mat-icon-button (click)="removeTransformMapping(i)"><mat-icon>delete</mat-icon></button>
                </div>
                <!-- Transform pipeline -->
                <ng-container *ngFor="let step of getTransformSteps(m); let ti = index">
                  <div class="wnc__ts">
                    <span class="wnc__ts-badge">fx{{ ti + 1 }}</span>
                    <mat-form-field appearance="outline" class="wnc__ts-type">
                      <mat-select [value]="step.type" (selectionChange)="onStepTypeChange(m, ti, $event.value)" (openedChange)="onSelectOpen('transform', $event)">
                        <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['transform'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['transform'] = $any($event.target).value" placeholder="Search..." /></div>
                        @for (tt of transformTypes; track tt.value) {
                          @if (matchesFilter('transform', tt.label + ' ' + tt.value)) {
                          <mat-option [value]="tt.value">{{ tt.label }}</mat-option>
                          }
                        }
                      </mat-select>
                    </mat-form-field>
                    <ng-container [ngSwitch]="step.type">
                      <ng-container *ngSwitchCase="'template'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Template</mat-label><input matInput [value]="step['template'] || ''" (input)="setStepProp(m,ti,'template',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'format'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Template</mat-label><input matInput [value]="step['template'] || ''" (input)="setStepProp(m,ti,'template',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'regex_extract'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Pattern</mat-label><input matInput [value]="step['pattern'] || ''" (input)="setStepProp(m,ti,'pattern',$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Group</mat-label><input matInput type="number" [value]="step['group'] ?? 0" (input)="setStepProp(m,ti,'group',+$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'regex_replace'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Pattern</mat-label><input matInput [value]="step['pattern'] || ''" (input)="setStepProp(m,ti,'pattern',$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Replacement</mat-label><input matInput [value]="step['replacement'] || ''" (input)="setStepProp(m,ti,'replacement',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'join'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Separator</mat-label><input matInput [value]="step['separator'] || ''" (input)="setStepProp(m,ti,'separator',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'split'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Separator</mat-label><input matInput [value]="step['separator'] || ''" (input)="setStepProp(m,ti,'separator',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'concat'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Separator</mat-label><input matInput [value]="step['separator'] || ''" (input)="setStepProp(m,ti,'separator',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'replace'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Find</mat-label><input matInput [value]="step['old'] || ''" (input)="setStepProp(m,ti,'old',$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Replace with</mat-label><input matInput [value]="step['new'] || ''" (input)="setStepProp(m,ti,'new',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'substring'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Start</mat-label><input matInput type="number" [value]="step['start'] ?? 0" (input)="setStepProp(m,ti,'start',+$any($event.target).value)" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>End</mat-label><input matInput type="number" [value]="step['end'] ?? ''" (input)="setStepProp(m,ti,'end',$any($event.target).value ? +$any($event.target).value : null)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'date_format'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Input format</mat-label><input matInput [value]="step['input_format'] || ''" (input)="setStepProp(m,ti,'input_format',$any($event.target).value)" placeholder="%Y-%m-%d" /></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Output format</mat-label><input matInput [value]="step['output_format'] || ''" (input)="setStepProp(m,ti,'output_format',$any($event.target).value)" placeholder="%d.%m.%Y" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'math'"><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Op</mat-label><mat-select [value]="step['operation'] || 'add'" (selectionChange)="setStepProp(m,ti,'operation',$event.value)"><mat-option value="add">+</mat-option><mat-option value="sub">-</mat-option><mat-option value="mul">*</mat-option><mat-option value="div">/</mat-option></mat-select></mat-form-field><mat-form-field appearance="outline" class="wnc__ts-cfg-sm"><mat-label>Operand</mat-label><input matInput type="number" [value]="step['operand'] ?? 0" (input)="setStepProp(m,ti,'operand',+$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'prepend'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Prefix</mat-label><input matInput [value]="step['value'] || ''" (input)="setStepProp(m,ti,'value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'append'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Suffix</mat-label><input matInput [value]="step['value'] || ''" (input)="setStepProp(m,ti,'value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'default'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Default</mat-label><input matInput [value]="step['default_value'] || ''" (input)="setStepProp(m,ti,'default_value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'coalesce'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Default</mat-label><input matInput [value]="step['default_value'] || ''" (input)="setStepProp(m,ti,'default_value',$any($event.target).value)" /></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'map'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Map (JSON)</mat-label><textarea matInput [value]="getStepMapJson(step)" (input)="setStepMapJson(m,ti,$any($event.target).value)" rows="2" placeholder='{{"{"}} "old": "new" {{"}"}}' ></textarea></mat-form-field></ng-container>
                      <ng-container *ngSwitchCase="'lookup'"><mat-form-field appearance="outline" class="wnc__ts-cfg"><mat-label>Table (JSON)</mat-label><textarea matInput [value]="getStepMapJson(step)" (input)="setStepMapJson(m,ti,$any($event.target).value)" rows="2" placeholder='{{"{"}} "old": "new" {{"}"}}' ></textarea></mat-form-field></ng-container>
                    </ng-container>
                    <button mat-icon-button class="wnc__ts-rm" (click)="removeTransformStep(m, ti)"><mat-icon [style.font-size.px]="16">close</mat-icon></button>
                  </div>
                </ng-container>
                <button mat-button class="wnc__mc-add-fx" (click)="addTransformStep(m)"><mat-icon [style.font-size.px]="14">functions</mat-icon>Add transform</button>
              </div>
            </ng-container>
          }

          <!-- DELAY -->
          @if (node.type === 'delay') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Seconds</mat-label>
              <input matInput type="number" [(ngModel)]="cfg['seconds']" (ngModelChange)="emitChange()" />
            </mat-form-field>
          }

          <!-- LOOP -->
          @if (node.type === 'loop') {
            @if (sourceFieldDefs.length > 0) {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Array Field</mat-label>
                <mat-select [(ngModel)]="cfg['array_field']" (ngModelChange)="emitChange()" (openedChange)="onSelectOpen('loopField', $event)">
                  <div class="wnc__search-wrap"><mat-icon>search</mat-icon><input [value]="selectFilter['loopField'] || ''" (keydown)="$event.stopPropagation()" (input)="selectFilter['loopField'] = $any($event.target).value" placeholder="Search..." /></div>
                  @for (f of sourceFieldDefs; track f.field) {
                    @if (matchesFilter('loopField', f.label + ' ' + f.field)) {
                    <mat-option [value]="f.field">{{ f.label }} ({{ f.field }})</mat-option>
                    }
                  }
                  <mat-option value="__custom__">-- Custom value --</mat-option>
                </mat-select>
              </mat-form-field>
              @if (cfg['array_field'] === '__custom__') {
                <mat-form-field appearance="outline" class="wnc__field">
                  <mat-label>Custom path</mat-label>
                  <input matInput [(ngModel)]="cfg['array_field_custom']" (ngModelChange)="emitChange()" placeholder="data.items" />
                </mat-form-field>
              }
            } @else {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Array Field</mat-label>
                <input matInput [(ngModel)]="cfg['array_field']" (ngModelChange)="emitChange()" placeholder="data.items" />
              </mat-form-field>
            }
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Item Variable Name</mat-label>
              <input matInput [(ngModel)]="cfg['item_variable']" (ngModelChange)="emitChange()" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Index Variable Name</mat-label>
              <input matInput [(ngModel)]="cfg['index_variable']" (ngModelChange)="emitChange()" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Max Iterations</mat-label>
              <input matInput type="number" [(ngModel)]="cfg['max_iterations']" (ngModelChange)="emitChange()" />
            </mat-form-field>
          }

          <!-- HTTP REQUEST -->
          @if (node.type === 'http_request') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Method</mat-label>
              <mat-select [(ngModel)]="cfg['method']" (ngModelChange)="emitChange()">
                <mat-option value="GET">GET</mat-option>
                <mat-option value="POST">POST</mat-option>
                <mat-option value="PUT">PUT</mat-option>
                <mat-option value="PATCH">PATCH</mat-option>
                <mat-option value="DELETE">DELETE</mat-option>
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>URL</mat-label>
              <input matInput [(ngModel)]="cfg['url']" (ngModelChange)="emitChange()" [placeholder]="'https://api.example.com/\u007B\u007Bdata.id\u007D\u007D'" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Timeout (seconds)</mat-label>
              <input matInput type="number" [(ngModel)]="cfg['timeout_seconds']" (ngModelChange)="emitChange()" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Request Body (JSON)</mat-label>
              <textarea matInput [(ngModel)]="httpBodyJson" (ngModelChange)="onHttpBodyChange()" rows="4" [placeholder]="'{&quot;key&quot;: &quot;\u007B\u007Bdata.value\u007D\u007D&quot;}'"></textarea>
            </mat-form-field>
          }

          <!-- SET VARIABLE -->
          @if (node.type === 'set_variable') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Variable Name</mat-label>
              <input matInput [(ngModel)]="cfg['variable_name']" (ngModelChange)="emitChange()" />
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Value</mat-label>
              <input matInput [(ngModel)]="cfg['value']" (ngModelChange)="emitChange()" [placeholder]="'\u007B\u007Bdata.field\u007D\u007D or literal'" />
            </mat-form-field>
          }

          <!-- MERGE -->
          @if (node.type === 'merge') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Strategy</mat-label>
              <mat-select [(ngModel)]="cfg['strategy']" (ngModelChange)="emitChange()">
                <mat-option value="wait_all">Wait for All</mat-option>
                <mat-option value="first">First to Complete</mat-option>
              </mat-select>
            </mat-form-field>
          }

          <!-- PARALLEL -->
          @if (node.type === 'parallel') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Timeout (seconds)</mat-label>
              <input matInput type="number" [(ngModel)]="cfg['timeout_seconds']" (ngModelChange)="emitChange()" min="1" max="120" />
              <mat-hint>Max time to wait for all branches to complete</mat-hint>
            </mat-form-field>
            <p class="wnc__hint">
              Connect multiple action nodes as successors. Each branch executes simultaneously.
              Results are collected into <code>parallel_results</code> variable for the Aggregate node.
            </p>
          }

          <!-- AGGREGATE -->
          @if (node.type === 'aggregate') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Aggregation Strategy</mat-label>
              <mat-select [(ngModel)]="cfg['strategy']" (ngModelChange)="emitChange()">
                <mat-option value="min_price">Cheapest (Min Price)</mat-option>
                <mat-option value="max_price">Most Expensive (Max Price)</mat-option>
                <mat-option value="concat">Concatenate All</mat-option>
                <mat-option value="first">First Result</mat-option>
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Price Field</mat-label>
              <input matInput [(ngModel)]="cfg['price_field']" (ngModelChange)="emitChange()" placeholder="price" />
              <mat-hint>Field name containing the price value in product objects</mat-hint>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Source Variable</mat-label>
              <input matInput [(ngModel)]="cfg['source_variable']" (ngModelChange)="emitChange()" placeholder="parallel_results" />
              <mat-hint>Variable containing parallel branch results</mat-hint>
            </mat-form-field>
          }

          <!-- RESPONSE -->
          @if (node.type === 'response') {
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Response Body (JSON)</mat-label>
              <textarea matInput [(ngModel)]="responseBodyJson" (ngModelChange)="onResponseBodyChange()" rows="4" [placeholder]="'{&quot;result&quot;: &quot;\u007B\u007Bdata.status\u007D\u007D&quot;}'"></textarea>
            </mat-form-field>
          }

          <!-- THINK (AI Agent) -->
          @if (node.type === 'think') {
            @if (credentialNames.length > 0) {
              <mat-form-field appearance="outline" class="wnc__field">
                <mat-label>Credentials (AI Agent)</mat-label>
                <mat-select [(ngModel)]="cfg['credential_name']" (ngModelChange)="emitChange()">
                  @for (cn of credentialNames; track cn) {
                    <mat-option [value]="cn">
                      <mat-icon style="font-size: 16px; height: 16px; width: 16px; vertical-align: middle; margin-right: 4px;">vpn_key</mat-icon>
                      {{ cn }}
                    </mat-option>
                  }
                </mat-select>
              </mat-form-field>
            } @else if (!loadingCredentialNames) {
              <p class="wnc__hint">No AI Agent credentials configured. Add a Gemini API key in Credentials.</p>
            }
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>AI Action</mat-label>
              <mat-select [(ngModel)]="cfg['action']" (ngModelChange)="emitChange()">
                <mat-option value="agent.analyze">Analyze (custom prompt)</mat-option>
                <mat-option value="agent.analyze_risk">Risk Analysis</mat-option>
                <mat-option value="agent.recommend_courier">Courier Recommendation</mat-option>
                <mat-option value="agent.classify_priority">Priority Classification</mat-option>
                <mat-option value="agent.extract_data">Data Extraction</mat-option>
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Prompt</mat-label>
              <textarea matInput [(ngModel)]="cfg['prompt']" (ngModelChange)="emitChange()" rows="5"
                placeholder="Describe what the AI should analyze...&#10;Example: Classify this order's priority and suggest the best courier based on weight, destination and urgency."></textarea>
              <mat-hint>The AI receives workflow data + this prompt</mat-hint>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Output Schema (JSON) — optional</mat-label>
              <textarea matInput [(ngModel)]="cfg['output_schema_json']" (ngModelChange)="emitChange()" rows="4"
                [placeholder]="'{&quot;priority&quot;: &quot;string&quot;, &quot;courier&quot;: &quot;string&quot;, &quot;reasoning&quot;: &quot;string&quot;}'"></textarea>
              <mat-hint>Define the structure of AI response — ensures structured JSON output</mat-hint>
            </mat-form-field>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>Temperature (0.0 = precise, 1.0 = creative)</mat-label>
              <input matInput type="number" [(ngModel)]="cfg['temperature']" (ngModelChange)="emitChange()" min="0" max="1" step="0.1" />
            </mat-form-field>
            <div class="wnc__toggle-row">
              <mat-slide-toggle
                [checked]="cfg['redact_pii'] !== false"
                (change)="cfg['redact_pii'] = $event.checked; emitChange()"
                color="primary">
                RODO / GDPR — redact personal data
              </mat-slide-toggle>
              <p class="wnc__hint" style="margin-top: 4px;">
                When enabled, personal data (names, emails, phone numbers, addresses, PESEL, NIP, bank accounts)
                is automatically replaced with [RODO_REDACTED] before sending to the AI model.
                Original data remains available for downstream nodes.
              </p>
            </div>
            <mat-form-field appearance="outline" class="wnc__field">
              <mat-label>On Error</mat-label>
              <mat-select [(ngModel)]="cfg['on_error']" (ngModelChange)="emitChange()">
                <mat-option value="stop">Stop Workflow</mat-option>
                <mat-option value="continue">Continue</mat-option>
              </mat-select>
            </mat-form-field>
          }

          <!-- Data reference help -->
          <mat-expansion-panel class="wnc__help">
            <mat-expansion-panel-header>
              <mat-panel-title>Data Path Reference</mat-panel-title>
            </mat-expansion-panel-header>
            <div class="wnc__help-content">
              <p><strong>Trigger data:</strong> <code>field_name</code> or <code>nested.path</code></p>
              <p><strong>Variables:</strong> <code>vars.my_variable</code></p>
              <p><strong>Node output:</strong> <code>nodes.node_id.field</code></p>
              <p><strong>Think (AI) output:</strong> <code>nodes.think_node_id.field</code> — available as source fields</p>
              <p><strong>Templates:</strong> <code>{{'{{field_name}}'}}</code> or <code>{{'{{nodes.node_id.field}}'}}</code></p>
              <p><strong>Array access:</strong> <code>items.0.name</code></p>
            </div>
          </mat-expansion-panel>
        </div>
      </div>
    }
  `,
  styles: [`
    .wnc { display: flex; flex-direction: column; height: 100%; background: #fff; }
    .wnc__header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid #e0e0e0; border-left: 4px solid #666; }
    .wnc__header-text { flex: 1; }
    .wnc__type { display: block; font-weight: 600; font-size: 14px; }
    .wnc__desc { display: block; font-size: 11px; color: #888; }
    .wnc__body { flex: 1; overflow-y: auto; padding: 16px; }
    .wnc__field { width: 100%; margin-bottom: 4px; }
    .wnc__section-title { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 13px; margin: 12px 0 8px; color: #555; }
    .wnc__hint { color: #888; font-size: 12px; margin: 0 0 8px; }
    .wnc__toggle-row { margin: 8px 0 16px; padding: 10px 12px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; }
    .wnc__help { margin-top: 16px; }
    .wnc__help-content p { margin: 4px 0; font-size: 12px; }
    .wnc__help-content code { background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 11px; }
    .wnc__mapping-arrow { color: #999; font-size: 18px; flex-shrink: 0; align-self: center; margin-top: -16px; }
    .wnc__condition-row { display: flex; gap: 4px; align-items: flex-start; margin-bottom: 4px; flex-wrap: wrap; }
    .wnc__cond-field { flex: 2; min-width: 100px; }
    .wnc__cond-op { flex: 2; min-width: 120px; }
    .wnc__cond-val { flex: 1.5; min-width: 80px; }
    .wnc__cond-custom { flex: 1; min-width: 60px; }
    .wnc__mapping-row { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; flex-wrap: wrap; }
    .wnc__mapping-field { flex: 1; min-width: 80px; }
    .wnc__mapping-custom { flex: 0.8; min-width: 60px; }

    /* Mapping card */
    .wnc__mc { margin-bottom: 8px; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; }
    .wnc__mc-row { display: flex; align-items: flex-start; gap: 4px; flex-wrap: wrap; }
    .wnc__mc-sources { flex: 1.2; min-width: 120px; display: flex; flex-direction: column; gap: 2px; }
    .wnc__mc-src-item { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
    .wnc__mc-src-extra { margin-top: -4px; }
    .wnc__mc-plus { font-size: 12px; font-weight: 700; color: #1565c0; margin-right: 2px; }
    .wnc__mc-src-ff { flex: 1; min-width: 100px; }
    .wnc__mc-custom { flex: 1; min-width: 80px; }
    .wnc__mc-rm-src { width: 28px; height: 28px; line-height: 28px; margin-top: -12px; }
    .wnc__mc-add-src { font-size: 11px; color: #1565c0; padding: 0 4px; min-height: 24px; line-height: 24px; align-self: flex-start; }
    .wnc__mc-add-src mat-icon { margin-right: 2px; vertical-align: middle; }
    .wnc__mc-to { flex: 1; min-width: 100px; }
    .wnc__mc-fx { flex: 0 0 120px; min-width: 100px; }

    /* Transform step pipeline */
    .wnc__ts { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-top: 4px; padding: 6px 8px; background: #f4f7ff; border-left: 3px solid #1565c0; border-radius: 0 6px 6px 0; }
    .wnc__ts-badge { font-size: 10px; font-weight: 700; color: #1565c0; min-width: 22px; text-align: center; }
    .wnc__ts-type { flex: 0 0 140px; min-width: 120px; }
    .wnc__ts-cfg { flex: 1 1 140px; min-width: 100px; }
    .wnc__ts-cfg-sm { flex: 0 0 90px; min-width: 70px; }
    .wnc__ts-rm { width: 28px; height: 28px; line-height: 28px; flex-shrink: 0; }
    .wnc__mc-add-fx { font-size: 11px; color: #1565c0; padding: 0 4px; min-height: 24px; line-height: 24px; margin-top: 2px; }
    .wnc__mc-add-fx mat-icon { margin-right: 2px; vertical-align: middle; }

    /* Search inside mat-select dropdowns */
    ::ng-deep .wnc__search-wrap { display: flex; align-items: center; padding: 8px 16px; border-bottom: 1px solid #e0e0e0; position: sticky; top: 0; z-index: 1; background: #fff; }
    ::ng-deep .wnc__search-wrap mat-icon { color: #999; font-size: 18px; height: 18px; width: 18px; margin-right: 8px; flex-shrink: 0; }
    ::ng-deep .wnc__search-wrap input { flex: 1; border: none; outline: none; font-size: 13px; padding: 4px 0; background: transparent; }
  `],
})
export class WorkflowNodeConfigComponent implements OnChanges {
  @Input() node: WorkflowNode | null = null;
  @Input() connectors: Connector[] = [];
  @Input() allNodes: WorkflowNode[] = [];
  @Output() nodeChange = new EventEmitter<WorkflowNode>();
  @Output() close = new EventEmitter<void>();

  cfg: Record<string, unknown> = {};
  triggerEvents: string[] = [];
  actionActions: string[] = [];
  sourceFieldDefs: ConnectorFieldDef[] = [];
  destFieldDefs: ConnectorFieldDef[] = [];
  credentialNames: string[] = [];
  loadingCredentialNames = false;
  httpBodyJson = '';
  responseBodyJson = '';
  selectFilter: Record<string, string> = {};
  private _lastNodeId = '';
  private _selfEmit = false;

  readonly conditionOperators = CONDITION_OPERATORS;
  readonly transformTypes = TRANSFORM_TYPES;

  constructor(private readonly api: PinquarkApiService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['node'] && this.node) {
      if (this._selfEmit) {
        this._selfEmit = false;
        return;
      }
      this._lastNodeId = this.node.id;
      this.cfg = this.node.config;
      this.updateConnectorLists();
      this.updateFieldDefs();
      if (this.node.type === 'think') {
        this.loadCredentialNames('ai-agent');
      }
      if ((this.node.type === 'action' || this.node.type === 'trigger') && this.cfg['connector_name']) {
        this.loadCredentialNames(this.cfg['connector_name'] as string);
      } else {
        this.credentialNames = [];
      }
      if (this.node.type === 'http_request') {
        try { this.httpBodyJson = JSON.stringify(this.cfg['body'] || {}, null, 2); } catch { this.httpBodyJson = '{}'; }
      }
      if (this.node.type === 'response') {
        try { this.responseBodyJson = JSON.stringify(this.cfg['body'] || {}, null, 2); } catch { this.responseBodyJson = '{}'; }
      }
    }
  }

  trackByField(_index: number, item: ConnectorFieldDef): string {
    return item.field;
  }

  onSelectOpen(key: string, opened: boolean): void {
    if (!opened) {
      this.selectFilter[key] = '';
    } else {
      setTimeout(() => {
        const input = document.querySelector<HTMLInputElement>('.cdk-overlay-container .wnc__search-wrap input');
        input?.focus();
      });
    }
  }

  matchesFilter(key: string, text: string): boolean {
    const q = (this.selectFilter[key] || '').trim().toLowerCase();
    return !q || text.toLowerCase().includes(q);
  }

  // ── Mapping sources ──

  getMappingSources(m: FieldMapping): string[] {
    if (m.sources && m.sources.length > 0) return m.sources;
    return [m.from || ''];
  }

  onSourceChange(m: FieldMapping, idx: number, value: string): void {
    const sources = [...this.getMappingSources(m)];
    sources[idx] = value;
    if (sources.length === 1) {
      m.from = value;
      delete m.sources;
    } else {
      m.sources = sources;
      m.from = sources[0] || '';
    }
    this.emitChange();
  }

  addMappingSource(m: FieldMapping): void {
    const sources = [...this.getMappingSources(m), ''];
    m.sources = sources;
    m.from = sources[0] || '';
    this.emitChange();
  }

  removeMappingSource(m: FieldMapping, idx: number): void {
    const sources = [...this.getMappingSources(m)];
    sources.splice(idx, 1);
    if (sources.length <= 1) {
      m.from = sources[0] || '';
      delete m.sources;
    } else {
      m.sources = sources;
      m.from = sources[0] || '';
    }
    this.emitChange();
  }

  // ── Transform pipeline ──

  getTransformSteps(m: FieldMapping): TransformStep[] {
    if (!m.transform) return [];
    return Array.isArray(m.transform) ? m.transform : [m.transform];
  }

  addTransformStep(m: FieldMapping): void {
    const steps = this.getTransformSteps(m);
    const updated = [...steps, { type: 'uppercase' } as TransformStep];
    m.transform = updated.length === 1 ? updated[0] : updated;
    this.emitChange();
  }

  removeTransformStep(m: FieldMapping, idx: number): void {
    const steps = [...this.getTransformSteps(m)];
    steps.splice(idx, 1);
    if (steps.length === 0) {
      delete m.transform;
    } else if (steps.length === 1) {
      m.transform = steps[0];
    } else {
      m.transform = steps;
    }
    this.emitChange();
  }

  onStepTypeChange(m: FieldMapping, idx: number, type: string): void {
    const steps = [...this.getTransformSteps(m)];
    steps[idx] = { type } as TransformStep;
    m.transform = steps.length === 1 ? steps[0] : steps;
    this.emitChange();
  }

  setStepProp(m: FieldMapping, idx: number, key: string, value: unknown): void {
    const steps = this.getTransformSteps(m);
    (steps[idx] as Record<string, unknown>)[key] = value;
    this.emitChange();
  }

  getStepMapJson(step: TransformStep): string {
    const vals = step['values'] || step['table'] || {};
    try { return JSON.stringify(vals, null, 2); } catch { return '{}'; }
  }

  setStepMapJson(m: FieldMapping, idx: number, json: string): void {
    try {
      const parsed = JSON.parse(json);
      this.setStepProp(m, idx, 'values', parsed);
    } catch { /* keep raw */ }
  }

  getNodeColor(): string {
    return NODE_TYPE_DEFINITIONS.find(d => d.type === this.node?.type)?.color || '#666';
  }

  getNodeIcon(): string {
    return NODE_TYPE_DEFINITIONS.find(d => d.type === this.node?.type)?.icon || 'help';
  }

  getNodeTypeLabel(): string {
    return NODE_TYPE_DEFINITIONS.find(d => d.type === this.node?.type)?.label || this.node?.type || '';
  }

  getNodeDescription(): string {
    return NODE_TYPE_DEFINITIONS.find(d => d.type === this.node?.type)?.description || '';
  }

  getFlag(code: string): string {
    return COUNTRY_FLAG_MAP[code] ?? code;
  }

  emitChange(): void {
    if (this.node) {
      this._selfEmit = true;
      this.nodeChange.emit({ ...this.node, config: { ...this.cfg } });
    }
  }

  isUnaryOperator(op: string): boolean {
    return ['exists', 'not_exists', 'is_empty', 'is_not_empty'].includes(op);
  }

  // ── Trigger ──

  onTriggerConnectorChange(): void {
    const c = this.connectors.find(cn => cn.name === this.cfg['connector_name']);
    this.triggerEvents = c?.events ?? [];
    this.cfg['event'] = '';
    this.cfg['credential_name'] = 'default';
    this.sourceFieldDefs = [];
    if (this.cfg['connector_name']) {
      this.loadCredentialNames(this.cfg['connector_name'] as string);
    } else {
      this.credentialNames = [];
    }
    this.emitChange();
  }

  onTriggerEventChange(): void {
    this.updateFieldDefs();
    this.emitChange();
  }

  // ── Action ──

  onActionConnectorChange(): void {
    const c = this.connectors.find(cn => cn.name === this.cfg['connector_name']);
    this.actionActions = c?.actions ?? [];
    this.cfg['action'] = '';
    this.cfg['credential_name'] = 'default';
    this.destFieldDefs = [];
    if (this.cfg['connector_name']) {
      this.loadCredentialNames(this.cfg['connector_name'] as string);
    } else {
      this.credentialNames = [];
    }
    this.emitChange();
  }

  onActionChange(): void {
    this.updateFieldDefs();
    this.emitChange();
  }

  getDestFieldLabel(fieldName: string): string {
    return this.destFieldDefs.find(f => f.field === fieldName)?.label || fieldName;
  }

  getDestFieldType(fieldName: string): string {
    return this.destFieldDefs.find(f => f.field === fieldName)?.type || 'string';
  }

  addFieldMapping(): void {
    if (!Array.isArray(this.cfg['field_mapping'])) this.cfg['field_mapping'] = [];
    (this.cfg['field_mapping'] as FieldMapping[]).push({ from: '', to: '' });
    this.emitChange();
  }

  removeFieldMapping(i: number): void {
    (this.cfg['field_mapping'] as FieldMapping[]).splice(i, 1);
    this.emitChange();
  }

  // ── Condition / Filter ──

  addCondition(): void {
    if (!Array.isArray(this.cfg['conditions'])) this.cfg['conditions'] = [];
    (this.cfg['conditions'] as ConditionRule[]).push({ field: '', operator: 'eq', value: '' });
    this.emitChange();
  }

  removeCondition(i: number): void {
    (this.cfg['conditions'] as ConditionRule[]).splice(i, 1);
    this.emitChange();
  }

  // ── Switch ──

  addSwitchCase(): void {
    if (!Array.isArray(this.cfg['cases'])) this.cfg['cases'] = [];
    const cases = this.cfg['cases'] as Array<{ value: string; handle: string }>;
    cases.push({ value: '', handle: `case_${cases.length + 1}` });
    this.emitChange();
  }

  removeSwitchCase(i: number): void {
    (this.cfg['cases'] as Array<{ value: string; handle: string }>).splice(i, 1);
    this.emitChange();
  }

  // ── Transform ──

  addTransformMapping(): void {
    if (!Array.isArray(this.cfg['mappings'])) this.cfg['mappings'] = [];
    (this.cfg['mappings'] as FieldMapping[]).push({ from: '', to: '' });
    this.emitChange();
  }

  removeTransformMapping(i: number): void {
    (this.cfg['mappings'] as FieldMapping[]).splice(i, 1);
    this.emitChange();
  }

  // ── HTTP ──

  onHttpBodyChange(): void {
    try {
      this.cfg['body'] = JSON.parse(this.httpBodyJson);
    } catch {
      // keep raw
    }
    this.emitChange();
  }

  onResponseBodyChange(): void {
    try {
      this.cfg['body'] = JSON.parse(this.responseBodyJson);
    } catch {
      // keep raw
    }
    this.emitChange();
  }

  // ── Type helpers ──

  asConditions(val: unknown): ConditionRule[] {
    return Array.isArray(val) ? val : [];
  }

  asFieldMappings(val: unknown): FieldMapping[] {
    return Array.isArray(val) ? val : [];
  }

  asSwitchCases(val: unknown): Array<{ value: string; handle: string }> {
    return Array.isArray(val) ? val : [];
  }

  private updateConnectorLists(): void {
    if (!this.node) return;
    if (this.node.type === 'trigger') {
      const c = this.connectors.find(cn => cn.name === this.cfg['connector_name']);
      this.triggerEvents = c?.events ?? [];
    }
    if (this.node.type === 'action') {
      const c = this.connectors.find(cn => cn.name === this.cfg['connector_name']);
      this.actionActions = c?.actions ?? [];
    }
  }

  private updateFieldDefs(): void {
    if (!this.node) return;

    this.sourceFieldDefs = this.getSourceFieldsFromTriggers();

    if (this.node.type === 'action') {
      const connectorName = this.cfg['connector_name'] as string;
      const actionName = this.cfg['action'] as string;
      const c = this.connectors.find(cn => cn.name === connectorName);
      this.destFieldDefs = c?.action_fields?.[actionName] ?? [];
    } else if (this.node.type === 'trigger') {
      const connectorName = this.cfg['connector_name'] as string;
      const eventName = this.cfg['event'] as string;
      const c = this.connectors.find(cn => cn.name === connectorName);
      this.sourceFieldDefs = c?.event_fields?.[eventName] ?? [];
      this.destFieldDefs = [];
    } else {
      this.destFieldDefs = [];
    }
  }

  private getSourceFieldsFromTriggers(): ConnectorFieldDef[] {
    const fields: ConnectorFieldDef[] = [];
    const seen = new Set<string>();

    const triggerNodes = this.allNodes.filter(n => n.type === 'trigger');
    for (const tn of triggerNodes) {
      const connectorName = tn.config['connector_name'] as string;
      const eventName = tn.config['event'] as string;
      if (!connectorName || !eventName) continue;

      const c = this.connectors.find(cn => cn.name === connectorName);
      const eventFields = c?.event_fields?.[eventName] ?? [];
      for (const f of eventFields) {
        if (!seen.has(f.field)) {
          seen.add(f.field);
          fields.push(f);
        }
      }
    }

    const actionNodes = this.allNodes.filter(
      n => n.type === 'action' && n.id !== this.node?.id,
    );
    for (const an of actionNodes) {
      const connectorName = an.config['connector_name'] as string;
      const actionName = an.config['action'] as string;
      if (!connectorName || !actionName) continue;

      const c = this.connectors.find(cn => cn.name === connectorName);
      const outFields = c?.output_fields?.[actionName] ?? [];
      if (outFields.length === 0) continue;

      const displayLabel = an.label || `${connectorName}/${actionName}`;
      for (const f of outFields) {
        const fieldPath = `nodes.${an.id}.${f.field}`;
        if (!seen.has(fieldPath)) {
          seen.add(fieldPath);
          fields.push({
            field: fieldPath,
            label: `[${displayLabel}] ${f.label}`,
            type: f.type,
          });
        }
      }
    }

    const thinkNodes = this.allNodes.filter(
      n => n.type === 'think' && n.id !== this.node?.id,
    );
    for (const tn of thinkNodes) {
      const schemaJson = tn.config['output_schema_json'] as string;
      if (!schemaJson) continue;
      try {
        const schema = JSON.parse(schemaJson);
        if (schema && typeof schema === 'object' && !Array.isArray(schema)) {
          const typeDef = NODE_TYPE_DEFINITIONS.find(d => d.type === tn.type);
          const typeLabel = typeDef?.label || tn.type;
          const displayLabel = tn.label ? `${typeLabel}: ${tn.label}` : typeLabel;
          for (const [key, fieldType] of Object.entries(schema)) {
            const fieldPath = `nodes.${tn.id}.${key}`;
            if (!seen.has(fieldPath)) {
              seen.add(fieldPath);
              fields.push({
                field: fieldPath,
                label: `[${displayLabel}] ${key}`,
                type: typeof fieldType === 'string' ? fieldType : 'string',
              });
            }
          }
        }
      } catch {
        // invalid JSON — skip
      }
    }

    return fields;
  }

  private loadCredentialNames(connectorName: string): void {
    this.loadingCredentialNames = true;
    this.credentialNames = [];
    this.api.listCredentialNames(connectorName).subscribe({
      next: (names: string[]) => {
        this.credentialNames = names;
        this.loadingCredentialNames = false;
        if (names.length > 0 && !this.cfg['credential_name']) {
          this.cfg['credential_name'] = 'default';
        }
      },
      error: () => {
        this.loadingCredentialNames = false;
        this.credentialNames = [];
      },
    });
  }
}
