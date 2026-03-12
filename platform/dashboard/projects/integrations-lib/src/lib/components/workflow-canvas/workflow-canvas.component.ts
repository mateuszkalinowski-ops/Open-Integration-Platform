import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatBadgeModule } from '@angular/material/badge';
import { Connector } from '../../models/connector.model';
import {
  WorkflowNode,
  WorkflowEdge,
  WorkflowNodeType,
  NODE_TYPE_DEFINITIONS,
  NodeTypeDefinition,
  WorkflowNodeResult,
} from '../../models';

const NODE_WIDTH = 300;
const NODE_HEIGHT = 88;
const CANVAS_SIZE = 6000;
const CANVAS_HALF = CANVAS_SIZE / 2;

interface DragState {
  nodeId: string;
  offsetX: number;
  offsetY: number;
}

interface ConnectionDraft {
  sourceNodeId: string;
  sourceHandle: string;
  mouseX: number;
  mouseY: number;
}

interface CanvasTransform {
  x: number;
  y: number;
  scale: number;
}

interface InlineAddMenu {
  edgeId: string;
  x: number;
  y: number;
}

@Component({
  selector: 'pinquark-workflow-canvas',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatChipsModule,
    MatBadgeModule,
  ],
  template: `
    <div class="wfc">
      <!-- Toolbar -->
      <div class="wfc-toolbar">
        <div class="wfc-toolbar__left">
          <button mat-icon-button matTooltip="Zoom In" (click)="zoomIn()" class="wfc-toolbar__btn">
            <mat-icon>add</mat-icon>
          </button>
          <div class="wfc-toolbar__zoom-display">{{ (transform.scale * 100) | number:'1.0-0' }}%</div>
          <button mat-icon-button matTooltip="Zoom Out" (click)="zoomOut()" class="wfc-toolbar__btn">
            <mat-icon>remove</mat-icon>
          </button>
          <div class="wfc-toolbar__divider"></div>
          <button mat-icon-button matTooltip="Fit View" (click)="fitView()" class="wfc-toolbar__btn">
            <mat-icon>fit_screen</mat-icon>
          </button>
        </div>
        @if (!readonly) {
          <div class="wfc-toolbar__right">
            <button mat-flat-button class="wfc-toolbar__add-btn" (click)="openStepPicker($event)">
              <mat-icon>add</mat-icon>
              <span>Add step</span>
            </button>
          </div>
        }
      </div>

      <!-- Canvas -->
      <div
        class="wfc-canvas"
        #canvasEl
        (mousedown)="onCanvasMouseDown($event)"
        (mousemove)="onCanvasMouseMove($event)"
        (mouseup)="onCanvasMouseUp($event)"
        (contextmenu)="$event.preventDefault()"
      >
        <div
          class="wfc-canvas__inner"
          [style.transform]="'translate(' + transform.x + 'px, ' + transform.y + 'px) scale(' + transform.scale + ')'"
        >
          <!-- Grid -->
          <svg class="wfc-canvas__grid">
            <defs>
              <pattern id="wfc-grid-sm" width="24" height="24" patternUnits="userSpaceOnUse">
                <circle cx="12" cy="12" r="0.8" fill="rgba(0,0,0,0.08)" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#wfc-grid-sm)" />
          </svg>

          <!-- Edges -->
          <svg class="wfc-canvas__edges">
            @for (edge of edges; track edge.id) {
              <g>
                <!-- Shadow path for wider hit area -->
                <path
                  [attr.d]="getEdgePath(edge)"
                  fill="none"
                  stroke="transparent"
                  stroke-width="20"
                  stroke-linecap="round"
                  class="wfc-edge-hit"
                  (click)="selectEdge(edge, $event)"
                />
                <path
                  [attr.d]="getEdgePath(edge)"
                  fill="none"
                  [attr.stroke]="getEdgeColor(edge)"
                  [attr.stroke-width]="getEdgeStrokeWidth(edge)"
                  stroke-linecap="round"
                  class="wfc-edge-path"
                  [class.wfc-edge-path--selected]="selectedEdgeId === edge.id"
                />
                <!-- Animated flow dot on success edges -->
                @if (getNodeStatus(edge.source) === 'success' && getNodeStatus(edge.target) === 'success') {
                  <circle r="4" fill="#4caf50">
                    <animateMotion [attr.path]="getEdgePath(edge)" dur="1.5s" repeatCount="indefinite" />
                  </circle>
                }
                @if (edge.sourceHandle && edge.sourceHandle !== 'default') {
                  <text
                    [attr.x]="getEdgeLabelPos(edge).x"
                    [attr.y]="getEdgeLabelPos(edge).y"
                    text-anchor="middle"
                    class="wfc-edge-label"
                  >{{ edge.sourceHandle }}</text>
                }
                <!-- Delete button on selected edge -->
                @if (!readonly && selectedEdgeId === edge.id) {
                  <g class="wfc-edge-del" (click)="deleteEdge(edge.id, $event)">
                    <circle
                      [attr.cx]="getEdgeMidpoint(edge).x"
                      [attr.cy]="getEdgeMidpoint(edge).y"
                      r="14"
                      fill="#ef4444"
                      class="wfc-edge-del__bg"
                    />
                    <line
                      [attr.x1]="getEdgeMidpoint(edge).x - 5"
                      [attr.y1]="getEdgeMidpoint(edge).y - 5"
                      [attr.x2]="getEdgeMidpoint(edge).x + 5"
                      [attr.y2]="getEdgeMidpoint(edge).y + 5"
                      stroke="#fff" stroke-width="2" stroke-linecap="round"
                    />
                    <line
                      [attr.x1]="getEdgeMidpoint(edge).x + 5"
                      [attr.y1]="getEdgeMidpoint(edge).y - 5"
                      [attr.x2]="getEdgeMidpoint(edge).x - 5"
                      [attr.y2]="getEdgeMidpoint(edge).y + 5"
                      stroke="#fff" stroke-width="2" stroke-linecap="round"
                    />
                  </g>
                }
                <!-- Plus button to insert node on edge -->
                @if (!readonly && selectedEdgeId !== edge.id) {
                  <g
                    class="wfc-edge-add"
                    (click)="showInlineAdd(edge, $event)"
                  >
                    <circle
                      [attr.cx]="getEdgeMidpoint(edge).x"
                      [attr.cy]="getEdgeMidpoint(edge).y"
                      r="12"
                      class="wfc-edge-add__bg"
                    />
                    <line
                      [attr.x1]="getEdgeMidpoint(edge).x - 5"
                      [attr.y1]="getEdgeMidpoint(edge).y"
                      [attr.x2]="getEdgeMidpoint(edge).x + 5"
                      [attr.y2]="getEdgeMidpoint(edge).y"
                      stroke="#6366f1" stroke-width="2" stroke-linecap="round"
                    />
                    <line
                      [attr.x1]="getEdgeMidpoint(edge).x"
                      [attr.y1]="getEdgeMidpoint(edge).y - 5"
                      [attr.x2]="getEdgeMidpoint(edge).x"
                      [attr.y2]="getEdgeMidpoint(edge).y + 5"
                      stroke="#6366f1" stroke-width="2" stroke-linecap="round"
                    />
                  </g>
                }
              </g>
            }
            @if (connectionDraft) {
              <path
                [attr.d]="getDraftEdgePath()"
                fill="none"
                stroke="#6366f1"
                stroke-width="2.5"
                stroke-dasharray="8 5"
                stroke-linecap="round"
              />
            }
          </svg>

          <!-- Nodes -->
          @for (node of nodes; track node.id; let i = $index) {
            <div
              class="wfc-node"
              [class.wfc-node--selected]="selectedNodeId === node.id"
              [class.wfc-node--success]="getNodeStatus(node.id) === 'success'"
              [class.wfc-node--failed]="getNodeStatus(node.id) === 'failed'"
              [class.wfc-node--filtered]="getNodeStatus(node.id) === 'filtered'"
              [class.wfc-node--running]="getNodeStatus(node.id) === 'running'"
              [class.wfc-node--unexecuted]="nodeResults.length > 0 && getNodeStatus(node.id) === null"
              [class.wfc-node--drop-target]="connectionDraft && connectionDraft.sourceNodeId !== node.id"
              [class.wfc-node--readonly]="readonly"
              [class.wfc-node--trigger]="node.type === 'trigger'"
              [style.left.px]="node.position.x + HALF"
              [style.top.px]="node.position.y + HALF"
              (mousedown)="onNodeMouseDown($event, node)"
              (mouseup)="onNodeMouseUp($event, node)"
              (dblclick)="onNodeDoubleClick(node)"
            >
              <!-- Step number -->
              <div class="wfc-node__step" [style.background]="getNodeAccentColor(node)">
                {{ getNodeIndex(node) }}
              </div>

              <!-- Color accent bar -->
              <div class="wfc-node__accent" [style.background]="getNodeAccentColor(node)"></div>

              <div class="wfc-node__content">
                <!-- Header row -->
                <div class="wfc-node__header">
                  @if (getConnectorLogo(node)) {
                    <img class="wfc-node__logo" [src]="getConnectorLogo(node)" [alt]="getConnectorName(node)" />
                  } @else {
                    <div class="wfc-node__icon-wrap" [style.background]="getNodeAccentColor(node) + '14'">
                      <mat-icon class="wfc-node__icon" [style.color]="getNodeAccentColor(node)">{{ getNodeDef(node.type)?.icon || 'help' }}</mat-icon>
                    </div>
                  }
                  <div class="wfc-node__info">
                    <span class="wfc-node__type-label">{{ getNodeTypeLabel(node) }}</span>
                    <span class="wfc-node__summary">{{ node.label || getNodeSummary(node) }}</span>
                  </div>
                  <div class="wfc-node__badges">
                    @if (getNodeBadge(node)) {
                      <span class="wfc-node__badge" [style.background]="getNodeBadgeColor(node)">{{ getNodeBadge(node) }}</span>
                    }
                    @if (getNodeDuration(node.id) !== null) {
                      <span class="wfc-node__duration">{{ getNodeDuration(node.id) }}ms</span>
                    }
                  </div>
                </div>

                <!-- Status indicator -->
                @if (getNodeStatus(node.id)) {
                  <div class="wfc-node__status wfc-node__status--{{ getNodeStatus(node.id) }}">
                    <mat-icon>{{ getStatusIcon(node.id) }}</mat-icon>
                  </div>
                }
              </div>

              @if (!readonly) {
                <!-- Node action buttons -->
                @if (node.type === 'action' || node.type === 'transform') {
                  <button class="wfc-node__mapper-btn" (click)="onOpenMapper(node, $event)" matTooltip="Open Visual Mapper">
                    <mat-icon>device_hub</mat-icon>
                  </button>
                }
                <button class="wfc-node__menu" (click)="deleteNode(node.id, $event)" matTooltip="Delete step">
                  <mat-icon>close</mat-icon>
                </button>
                <!-- Input handles -->
                @for (handle of getInputHandles(node); track handle) {
                  <div
                    class="wfc-handle wfc-handle--input"
                    [attr.data-handle]="handle"
                  ></div>
                }
                <!-- Output handles -->
                @for (handle of getOutputHandles(node); track handle; let hi = $index) {
                  <div
                    class="wfc-handle wfc-handle--output"
                    [style.left.%]="getOutputHandlePosition(node, hi)"
                    [attr.data-handle]="handle"
                    [matTooltip]="handle !== 'default' ? handle : ''"
                    (mousedown)="onHandleMouseDown($event, node, handle)"
                  >
                    @if (handle !== 'default' && getOutputHandles(node).length > 1) {
                      <span class="wfc-handle__label">{{ handle }}</span>
                    }
                  </div>
                }
              }
            </div>
          }
        </div>

        <!-- Unified step picker (outside transformed inner, overlays on canvas) -->
        @if (stepPickerOpen) {
          <div
            class="wfc-sp"
            [style.left.px]="stepPickerPos.x"
            [style.top.px]="stepPickerPos.y"
            (mousedown)="$event.stopPropagation()"
          >
            <div class="wfc-sp__bar">
              <mat-icon class="wfc-sp__bar-icon">add_circle</mat-icon>
              <span class="wfc-sp__bar-title">{{ inlineAddMenu ? 'Insert step' : 'Add step' }}</span>
              <span class="wfc-sp__bar-count">{{ totalNodeCount }} types</span>
              <button class="wfc-sp__bar-close" (click)="closeStepPicker()"><mat-icon>close</mat-icon></button>
            </div>
            <div class="wfc-sp__body">
              @for (cat of insertCategories; track cat.name) {
                <div class="wfc-sp__section">
                  <div class="wfc-sp__section-label">{{ cat.name }}</div>
                  <div class="wfc-sp__list">
                    @for (def of cat.defs; track def.type) {
                      <button class="wfc-sp__item" (click)="pickStep(def.type)">
                        <span class="wfc-sp__dot" [style.background]="def.color">
                          <mat-icon>{{ def.icon }}</mat-icon>
                        </span>
                        <span class="wfc-sp__name">{{ def.label }}</span>
                        <span class="wfc-sp__desc">{{ def.description }}</span>
                      </button>
                    }
                  </div>
                </div>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    /* ── Layout ── */
    .wfc {
      width: 100%; height: 100%;
      display: flex; flex-direction: column;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Toolbar ── */
    .wfc-toolbar {
      display: flex; justify-content: space-between; align-items: center;
      padding: 8px 16px;
      background: #fff;
      border-bottom: 1px solid #e2e8f0;
      z-index: 10;
    }
    .wfc-toolbar__left, .wfc-toolbar__right { display: flex; align-items: center; gap: 2px; }
    .wfc-toolbar__btn { color: #64748b; }
    .wfc-toolbar__btn:hover { color: #334155; }
    .wfc-toolbar__zoom-display {
      font-size: 12px; font-weight: 600; color: #64748b;
      min-width: 44px; text-align: center;
      padding: 4px 8px;
      background: #f1f5f9; border-radius: 6px;
    }
    .wfc-toolbar__divider { width: 1px; height: 24px; background: #e2e8f0; margin: 0 8px; }
    .wfc-toolbar__add-btn {
      background: #6366f1 !important; color: #fff !important;
      border-radius: 8px !important; font-weight: 600 !important;
      font-size: 13px !important; letter-spacing: 0 !important;
      padding: 0 16px !important; height: 36px !important;
    }
    .wfc-toolbar__add-btn mat-icon { font-size: 18px; width: 18px; height: 18px; margin-right: 4px; }
    .wfc-toolbar__add-btn:hover { background: #4f46e5 !important; }

    /* ── Canvas ── */
    .wfc-canvas {
      flex: 1; overflow: hidden; cursor: grab; position: relative;
      background: #f8fafc;
    }
    .wfc-canvas:active { cursor: grabbing; }
    .wfc-canvas__inner { position: absolute; transform-origin: 0 0; width: 0; height: 0; }
    .wfc-canvas__grid {
      position: absolute; top: 0; left: 0;
      width: 6000px; height: 6000px;
      pointer-events: none;
    }
    .wfc-canvas__edges {
      position: absolute; top: 0; left: 0;
      width: 6000px; height: 6000px;
      overflow: visible; pointer-events: none;
    }

    /* ── Edges ── */
    .wfc-edge-hit { pointer-events: stroke; cursor: pointer; }
    .wfc-edge-path { pointer-events: none; transition: stroke-width 0.15s; }
    .wfc-edge-path--selected { filter: drop-shadow(0 0 4px rgba(99,102,241,0.4)); }
    .wfc-edge-label {
      fill: #64748b; font-size: 11px; font-weight: 600;
      font-family: 'Inter', sans-serif;
    }

    /* Edge delete button */
    .wfc-edge-del { pointer-events: all; cursor: pointer; }
    .wfc-edge-del__bg { transition: r 0.15s; }
    .wfc-edge-del:hover .wfc-edge-del__bg { r: 16; }

    /* Edge add (+) button */
    .wfc-edge-add {
      pointer-events: all; cursor: pointer;
      opacity: 0; transition: opacity 0.2s;
    }
    .wfc-canvas:hover .wfc-edge-add { opacity: 1; }
    .wfc-edge-add__bg {
      fill: #fff; stroke: #e2e8f0; stroke-width: 2;
      transition: stroke 0.15s, fill 0.15s, r 0.15s;
    }
    .wfc-edge-add:hover .wfc-edge-add__bg {
      stroke: #6366f1; fill: #eef2ff; r: 14;
    }

    /* ── Step picker ── */
    .wfc-sp {
      position: absolute; z-index: 20;
      background: #fff; border-radius: 10px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.16), 0 0 0 1px rgba(0,0,0,0.06);
      width: 340px; display: flex; flex-direction: column;
      max-height: min(520px, calc(100% - 80px)); overflow: hidden;
    }
    .wfc-sp__bar {
      display: flex; align-items: center; gap: 6px;
      padding: 8px 10px; border-bottom: 1px solid #e2e8f0;
      background: #f8fafc; border-radius: 10px 10px 0 0; flex-shrink: 0;
    }
    .wfc-sp__bar-icon { font-size: 18px; width: 18px; height: 18px; color: #6366f1; }
    .wfc-sp__bar-title { font-size: 13px; font-weight: 700; color: #1e293b; }
    .wfc-sp__bar-count { font-size: 11px; color: #94a3b8; margin-left: auto; }
    .wfc-sp__bar-close {
      background: none; border: none; cursor: pointer; display: flex;
      padding: 2px; border-radius: 4px; color: #94a3b8;
    }
    .wfc-sp__bar-close:hover { background: #e2e8f0; color: #475569; }
    .wfc-sp__bar-close mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .wfc-sp__body { overflow-y: auto; padding: 4px 6px 6px; }
    .wfc-sp__section { margin-bottom: 2px; }
    .wfc-sp__section-label {
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.08em; color: #94a3b8; padding: 6px 6px 3px;
    }
    .wfc-sp__list { display: flex; flex-direction: column; gap: 1px; }
    .wfc-sp__item {
      display: grid; grid-template-columns: 26px 1fr; grid-template-rows: auto auto;
      column-gap: 8px; row-gap: 0;
      padding: 6px 8px; border-radius: 6px;
      border: none; background: transparent; cursor: pointer;
      text-align: left; transition: background 0.12s;
    }
    .wfc-sp__item:hover { background: #f1f5f9; }
    .wfc-sp__dot {
      grid-row: 1 / 3; align-self: center;
      width: 26px; height: 26px; border-radius: 7px;
      display: flex; align-items: center; justify-content: center;
    }
    .wfc-sp__dot mat-icon { color: #fff; font-size: 15px; width: 15px; height: 15px; }
    .wfc-sp__name { font-size: 12px; font-weight: 600; color: #1e293b; line-height: 1.3; }
    .wfc-sp__desc {
      font-size: 10px; color: #94a3b8; line-height: 1.3;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    /* ── Nodes ── */
    .wfc-node {
      position: absolute;
      width: 300px;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      border: 2px solid #e2e8f0;
      cursor: move;
      user-select: none;
      transition: border-color 0.2s, box-shadow 0.2s;
      z-index: 5;
      display: flex;
      overflow: visible;
    }
    .wfc-node:hover {
      border-color: #cbd5e1;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    }
    .wfc-node--selected {
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99,102,241,0.15), 0 4px 12px rgba(0,0,0,0.08);
    }
    .wfc-node--drop-target { cursor: crosshair; }
    .wfc-node--drop-target:hover {
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99,102,241,0.2), 0 4px 20px rgba(99,102,241,0.15);
    }
    .wfc-node--success {
      border-color: #22c55e;
      box-shadow: 0 0 0 3px rgba(34,197,94,0.12), 0 4px 12px rgba(0,0,0,0.06);
    }
    .wfc-node--failed {
      border-color: #ef4444;
      box-shadow: 0 0 0 3px rgba(239,68,68,0.12), 0 4px 12px rgba(0,0,0,0.06);
    }
    .wfc-node--filtered {
      border-color: #f59e0b;
      box-shadow: 0 0 0 3px rgba(245,158,11,0.12), 0 4px 12px rgba(0,0,0,0.06);
    }
    .wfc-node--running {
      border-color: #6366f1;
      animation: wfc-pulse 1.8s ease-in-out infinite;
    }
    @keyframes wfc-pulse {
      0%, 100% { box-shadow: 0 0 0 3px rgba(99,102,241,0.12), 0 4px 12px rgba(0,0,0,0.06); }
      50% { box-shadow: 0 0 0 6px rgba(99,102,241,0.2), 0 4px 20px rgba(99,102,241,0.12); }
    }
    .wfc-node--unexecuted {
      opacity: 0.45;
      border-color: #e2e8f0;
    }
    .wfc-node--readonly { cursor: default; }
    .wfc-node--readonly:hover { border-color: #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }

    /* Trigger node special style */
    .wfc-node--trigger { border-style: solid; }

    /* Step number */
    .wfc-node__step {
      position: absolute; top: -12px; left: -12px;
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 700; color: #fff;
      box-shadow: 0 2px 6px rgba(0,0,0,0.15);
      z-index: 7;
      border: 2.5px solid #fff;
    }

    /* Accent bar */
    .wfc-node__accent {
      width: 4px; min-height: 100%; border-radius: 12px 0 0 12px;
      flex-shrink: 0;
    }

    /* Content */
    .wfc-node__content {
      flex: 1; padding: 12px 14px; min-width: 0; position: relative;
    }
    .wfc-node__header {
      display: flex; align-items: center; gap: 10px;
    }
    .wfc-node__logo {
      width: 36px; height: 36px; border-radius: 10px;
      object-fit: contain; flex-shrink: 0;
      background: #fff; border: 1px solid #e2e8f0;
      padding: 3px;
    }
    .wfc-node__icon-wrap {
      width: 36px; height: 36px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .wfc-node__icon { font-size: 20px; width: 20px; height: 20px; }
    .wfc-node__info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
    .wfc-node__type-label {
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.6px; color: #94a3b8;
      line-height: 1;
    }
    .wfc-node__summary {
      font-size: 13px; font-weight: 500; color: #1e293b;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      line-height: 1.3;
    }

    /* Badges */
    .wfc-node__badges { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
    .wfc-node__badge {
      font-size: 10px; font-weight: 700; padding: 2px 7px;
      border-radius: 4px; color: #fff;
      text-transform: uppercase; letter-spacing: 0.3px;
    }
    .wfc-node__duration {
      font-size: 10px; font-weight: 600; color: #94a3b8;
      font-variant-numeric: tabular-nums;
    }

    /* Status indicator */
    .wfc-node__status {
      position: absolute; right: -10px; top: 50%; transform: translateY(-50%);
      width: 24px; height: 24px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      border: 2.5px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      z-index: 8;
    }
    .wfc-node__status mat-icon { font-size: 14px; width: 14px; height: 14px; color: #fff; }
    .wfc-node__status--success { background: #22c55e; }
    .wfc-node__status--failed { background: #ef4444; }
    .wfc-node__status--filtered { background: #f59e0b; }
    .wfc-node__status--running { background: #6366f1; }

    /* Node action buttons */
    .wfc-node__menu, .wfc-node__mapper-btn {
      position: absolute; top: 6px;
      background: none; border: none; cursor: pointer;
      color: #cbd5e1; padding: 2px;
      border-radius: 6px; display: flex;
      opacity: 0; transition: opacity 0.15s, color 0.15s, background 0.15s;
      z-index: 8;
    }
    .wfc-node__menu { right: 6px; }
    .wfc-node__mapper-btn { right: 26px; }
    .wfc-node:hover .wfc-node__menu, .wfc-node:hover .wfc-node__mapper-btn { opacity: 1; }
    .wfc-node__menu:hover { background: #fee2e2; color: #ef4444; }
    .wfc-node__mapper-btn:hover { background: #e0e7ff; color: #6366f1; }
    .wfc-node__menu mat-icon, .wfc-node__mapper-btn mat-icon { font-size: 16px; width: 16px; height: 16px; }

    /* ── Handles ── */
    .wfc-handle {
      position: absolute;
      width: 14px; height: 14px;
      background: #fff;
      border: 2.5px solid #cbd5e1;
      border-radius: 50%;
      cursor: crosshair;
      z-index: 6;
      transition: transform 0.15s, background 0.15s, border-color 0.15s, box-shadow 0.15s;
    }
    .wfc-handle:hover {
      transform: scale(1.4);
      background: #6366f1; border-color: #6366f1;
      box-shadow: 0 0 0 4px rgba(99,102,241,0.2);
    }
    .wfc-handle--input { top: -7px; left: 50%; margin-left: -7px; }
    .wfc-handle--output { bottom: -7px; margin-left: -7px; }
    .wfc-handle__label {
      position: absolute; bottom: -17px; left: 50%; transform: translateX(-50%);
      font-size: 9px; font-weight: 600; color: #64748b;
      white-space: nowrap; pointer-events: none;
      background: #fff; padding: 0 4px; border-radius: 3px;
    }

    /* (legacy add-menu styles removed — replaced by wfc-step-picker) */
  `],
})
export class WorkflowCanvasComponent implements OnInit, OnChanges, OnDestroy {
  @Input() nodes: WorkflowNode[] = [];
  @Input() edges: WorkflowEdge[] = [];
  @Input() nodeResults: WorkflowNodeResult[] = [];
  @Input() connectors: Connector[] = [];
  @Input() readonly = false;
  @Output() nodesChange = new EventEmitter<WorkflowNode[]>();
  @Output() edgesChange = new EventEmitter<WorkflowEdge[]>();
  @Output() nodeSelected = new EventEmitter<WorkflowNode | null>();
  @Output() nodeDoubleClicked = new EventEmitter<WorkflowNode>();
  @Output() openNodeMapper = new EventEmitter<WorkflowNode>();

  @ViewChild('canvasEl', { static: true }) canvasEl!: ElementRef<HTMLDivElement>;

  readonly HALF = CANVAS_HALF;

  transform: CanvasTransform = { x: 0, y: 0, scale: 1 };
  selectedNodeId: string | null = null;
  selectedEdgeId: string | null = null;
  inlineAddMenu: InlineAddMenu | null = null;

  dragState: DragState | null = null;
  connectionDraft: ConnectionDraft | null = null;
  isPanning = false;
  panStart = { x: 0, y: 0 };

  readonly nodeDefs: Map<string, NodeTypeDefinition>;
  readonly nodeCategories: { name: string; defs: NodeTypeDefinition[] }[];
  readonly insertCategories: { name: string; defs: NodeTypeDefinition[] }[];
  readonly totalNodeCount: number;

  stepPickerOpen = false;
  stepPickerPos = { x: 0, y: 0 };

  private nodeIdCounter = 0;
  private boundMouseMove: ((e: MouseEvent) => void) | null = null;
  private boundMouseUp: ((e: MouseEvent) => void) | null = null;
  private boundKeyDown: ((e: KeyboardEvent) => void) | null = null;

  constructor() {
    this.nodeDefs = new Map(NODE_TYPE_DEFINITIONS.map(d => [d.type, d]));

    const cats = new Map<string, NodeTypeDefinition[]>();
    for (const def of NODE_TYPE_DEFINITIONS) {
      const list = cats.get(def.category) ?? [];
      list.push(def);
      cats.set(def.category, list);
    }
    const catOrder = ['trigger', 'action', 'logic', 'data', 'flow'];
    const catLabels: Record<string, string> = {
      trigger: 'Triggers',
      action: 'Actions',
      logic: 'Logic',
      data: 'Data',
      flow: 'Flow Control',
    };
    this.nodeCategories = catOrder
      .filter(c => cats.has(c))
      .map(c => ({ name: catLabels[c] || c, defs: cats.get(c)! }));

    this.insertCategories = catOrder
      .filter(c => cats.has(c))
      .map(c => ({ name: catLabels[c] || c, defs: cats.get(c)! }));

    this.totalNodeCount = this.insertCategories.reduce((s, c) => s + c.defs.length, 0);
  }

  ngOnInit(): void {
    this.boundMouseMove = (e: MouseEvent) => this.onDocMouseMove(e);
    this.boundMouseUp = (e: MouseEvent) => this.onDocMouseUp(e);
    this.boundKeyDown = (e: KeyboardEvent) => this.onDocKeyDown(e);
    document.addEventListener('mousemove', this.boundMouseMove);
    document.addEventListener('mouseup', this.boundMouseUp);
    document.addEventListener('keydown', this.boundKeyDown);

    if (this.nodes.length === 0) {
      this.fitView();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['nodes'] && this.nodes.length > 0) {
      this.nodeIdCounter = Math.max(
        this.nodeIdCounter,
        ...this.nodes.map(n => {
          const match = n.id.match(/\d+$/);
          return match ? parseInt(match[0], 10) : 0;
        })
      );
      if (this.readonly) {
        setTimeout(() => this.fitView(), 50);
      }
    }
  }

  ngOnDestroy(): void {
    if (this.boundMouseMove) document.removeEventListener('mousemove', this.boundMouseMove);
    if (this.boundMouseUp) document.removeEventListener('mouseup', this.boundMouseUp);
    if (this.boundKeyDown) document.removeEventListener('keydown', this.boundKeyDown);
  }

  // ── Node helpers ──

  getNodeDef(type: WorkflowNodeType): NodeTypeDefinition | undefined {
    return this.nodeDefs.get(type);
  }

  getNodeStatus(nodeId: string): string | null {
    const r = this.nodeResults.find(nr => nr.node_id === nodeId);
    return r?.status ?? null;
  }

  getNodeAccentColor(node: WorkflowNode): string {
    if (this.nodeResults.length > 0 && this.getNodeStatus(node.id) === null) {
      return '#94a3b8';
    }
    return this.getNodeDef(node.type)?.color || '#64748b';
  }

  getNodeIndex(node: WorkflowNode): number {
    return this.nodes.indexOf(node) + 1;
  }

  getConnectorLogo(node: WorkflowNode): string | null {
    const name = node.config?.['connector_name'] as string;
    if (!name) return null;
    const c = this.connectors.find(cn => cn.name === name);
    return c?.logo_url || null;
  }

  getConnectorName(node: WorkflowNode): string {
    return (node.config?.['connector_name'] as string) || '';
  }

  getNodeTypeLabel(node: WorkflowNode): string {
    const cfg = node.config;
    switch (node.type) {
      case 'trigger':
        return cfg['connector_name'] ? `Trigger · ${cfg['connector_name']}` : 'Trigger';
      case 'action':
        return cfg['connector_name'] ? `Action · ${cfg['connector_name']}` : 'Action';
      case 'think':
        return 'AI Agent';
      case 'http_request':
        return cfg['method'] ? `HTTP ${cfg['method']}` : 'HTTP Request';
      default:
        return this.getNodeDef(node.type)?.label || node.type;
    }
  }

  getNodeSummary(node: WorkflowNode): string {
    const cfg = node.config;
    switch (node.type) {
      case 'trigger':
        return cfg['event'] ? String(cfg['event']).replace(/\./g, ' → ') : 'Configure trigger...';
      case 'action':
        return cfg['action'] ? String(cfg['action']).replace(/\./g, ' → ') : 'Configure action...';
      case 'condition':
        return (cfg['conditions'] as unknown[])?.length ? `${(cfg['conditions'] as unknown[]).length} condition(s)` : 'Configure...';
      case 'switch':
        return cfg['field'] ? `Switch on ${cfg['field']}` : 'Configure...';
      case 'transform':
        return (cfg['mappings'] as unknown[])?.length ? `${(cfg['mappings'] as unknown[]).length} mapping(s)` : 'Configure...';
      case 'delay':
        return cfg['seconds'] ? `Wait ${cfg['seconds']}s` : 'Configure...';
      case 'loop':
        return cfg['array_field'] ? `Loop over ${cfg['array_field']}` : 'Configure...';
      case 'http_request':
        return cfg['url'] ? `${cfg['url']}` : 'Configure...';
      case 'set_variable':
        return cfg['variable_name'] ? `Set ${cfg['variable_name']}` : 'Configure...';
      case 'filter':
        return (cfg['conditions'] as unknown[])?.length ? `${(cfg['conditions'] as unknown[]).length} filter(s)` : 'Configure...';
      case 'think': {
        if (cfg['prompt']) {
          const p = String(cfg['prompt']);
          return p.length > 50 ? p.slice(0, 50) + '...' : p;
        }
        return 'Configure AI prompt...';
      }
      case 'sub_workflow':
        return cfg['workflow_id'] ? `Workflow: ${cfg['workflow_id']}` : 'Select a workflow...';
      case 'error_handler':
        return (cfg['catch_from'] as string[])?.length ? `Monitoring ${(cfg['catch_from'] as string[]).length} node(s)` : 'Configure error handler...';
      case 'batch':
        return cfg['source'] ? `Batch over ${cfg['source']}` : 'Configure batch source...';
      default:
        return this.getNodeDef(node.type)?.description || node.type;
    }
  }

  getNodeBadge(node: WorkflowNode): string | null {
    if (node.type === 'trigger') {
      const cfg = node.config;
      if (cfg['trigger_type'] === 'schedule') return 'Scheduled';
      if (cfg['connector_name']) return 'Real time';
      return null;
    }
    if (node.type === 'think') return 'AI';
    if (node.type === 'parallel') return 'Parallel';
    if (node.type === 'loop') return 'Batch';
    return null;
  }

  getNodeBadgeColor(node: WorkflowNode): string {
    if (node.type === 'trigger') return '#059669';
    if (node.type === 'think') return '#7c3aed';
    return '#6366f1';
  }

  getNodeDuration(nodeId: string): number | null {
    const r = this.nodeResults.find(nr => nr.node_id === nodeId);
    return r?.duration_ms ?? null;
  }

  getStatusIcon(nodeId: string): string {
    const status = this.getNodeStatus(nodeId);
    switch (status) {
      case 'success': return 'check';
      case 'failed': return 'close';
      case 'filtered': return 'filter_alt';
      case 'running': return 'sync';
      default: return '';
    }
  }

  getInputHandles(node: WorkflowNode): string[] {
    return this.getNodeDef(node.type)?.handles.inputs ?? [];
  }

  getOutputHandles(node: WorkflowNode): string[] {
    const def = this.getNodeDef(node.type);
    if (!def) return ['default'];

    if (node.type === 'switch') {
      const cases = (node.config['cases'] as Array<{ value: string; handle: string }>) ?? [];
      const handles = cases.map(c => c.handle || c.value || 'case');
      handles.push(((node.config['default_handle'] as string) ?? 'default'));
      return handles.length > 0 ? handles : ['default'];
    }

    return def.handles.outputs;
  }

  getOutputHandlePosition(node: WorkflowNode, index: number): number {
    const handles = this.getOutputHandles(node);
    if (handles.length <= 1) return 50;
    const step = 100 / (handles.length + 1);
    return step * (index + 1);
  }

  // ── Node CRUD ──

  addNode(type: WorkflowNodeType): void {
    this.inlineAddMenu = null;
    this.nodeIdCounter++;
    const id = `node_${this.nodeIdCounter}`;
    const rect = this.canvasEl.nativeElement.getBoundingClientRect();
    const centerX = (rect.width / 2 - this.transform.x) / this.transform.scale - CANVAS_HALF;
    const centerY = (rect.height / 2 - this.transform.y) / this.transform.scale - CANVAS_HALF;

    const newNode: WorkflowNode = {
      id,
      type,
      label: '',
      position: { x: centerX - NODE_WIDTH / 2 + Math.random() * 40, y: centerY - NODE_HEIGHT / 2 + Math.random() * 40 },
      config: this.getDefaultConfig(type),
    };
    this.nodes = [...this.nodes, newNode];
    this.nodesChange.emit(this.nodes);
    this.selectNode(newNode);
  }

  insertNodeOnEdge(type: WorkflowNodeType): void {
    if (!this.inlineAddMenu) return;
    const edge = this.edges.find(e => e.id === this.inlineAddMenu!.edgeId);
    if (!edge) { this.inlineAddMenu = null; return; }

    const srcNode = this.nodes.find(n => n.id === edge.source);
    const tgtNode = this.nodes.find(n => n.id === edge.target);
    if (!srcNode || !tgtNode) { this.inlineAddMenu = null; return; }

    this.nodeIdCounter++;
    const id = `node_${this.nodeIdCounter}`;
    const midX = (srcNode.position.x + tgtNode.position.x) / 2;
    const midY = (srcNode.position.y + tgtNode.position.y) / 2;

    const newNode: WorkflowNode = {
      id,
      type,
      label: '',
      position: { x: midX, y: midY },
      config: this.getDefaultConfig(type),
    };

    this.edges = this.edges.filter(e => e.id !== edge.id);
    const edgeToNew: WorkflowEdge = {
      id: `edge_${Date.now()}_a`,
      source: edge.source,
      target: id,
      sourceHandle: edge.sourceHandle,
      label: '',
    };
    const edgeFromNew: WorkflowEdge = {
      id: `edge_${Date.now()}_b`,
      source: id,
      target: edge.target,
      sourceHandle: 'default',
      label: '',
    };

    this.nodes = [...this.nodes, newNode];
    this.edges = [...this.edges, edgeToNew, edgeFromNew];
    this.inlineAddMenu = null;
    this.nodesChange.emit(this.nodes);
    this.edgesChange.emit(this.edges);
    this.selectNode(newNode);
  }

  showInlineAdd(edge: WorkflowEdge, event: MouseEvent): void {
    event.stopPropagation();
    const mid = this.getEdgeMidpoint(edge);
    this.inlineAddMenu = { edgeId: edge.id, x: mid.x, y: mid.y };
    const canvasX = (mid.x + CANVAS_HALF) * this.transform.scale + this.transform.x;
    const canvasY = (mid.y + CANVAS_HALF) * this.transform.scale + this.transform.y;
    this.stepPickerPos = { x: canvasX - 190, y: canvasY + 20 };
    this.stepPickerOpen = true;
  }

  openStepPicker(event: MouseEvent): void {
    event.stopPropagation();
    const canvasRect = this.canvasEl.nativeElement.getBoundingClientRect();
    this.inlineAddMenu = null;
    this.stepPickerPos = { x: canvasRect.width - 400, y: 10 };
    this.stepPickerOpen = true;
  }

  closeStepPicker(): void {
    this.stepPickerOpen = false;
    this.inlineAddMenu = null;
  }

  pickStep(type: WorkflowNodeType): void {
    if (this.inlineAddMenu) {
      this.insertNodeOnEdge(type);
    } else {
      this.addNode(type);
    }
    this.stepPickerOpen = false;
  }

  onOpenMapper(node: WorkflowNode, event: MouseEvent): void {
    event.stopPropagation();
    this.openNodeMapper.emit(node);
  }

  deleteNode(nodeId: string, event: MouseEvent): void {
    event.stopPropagation();
    this.nodes = this.nodes.filter(n => n.id !== nodeId);
    this.edges = this.edges.filter(e => e.source !== nodeId && e.target !== nodeId);
    if (this.selectedNodeId === nodeId) {
      this.selectedNodeId = null;
      this.nodeSelected.emit(null);
    }
    this.nodesChange.emit(this.nodes);
    this.edgesChange.emit(this.edges);
  }

  deleteSelectedEdge(): void {
    if (!this.selectedEdgeId) return;
    this.edges = this.edges.filter(e => e.id !== this.selectedEdgeId);
    this.selectedEdgeId = null;
    this.edgesChange.emit(this.edges);
  }

  selectNode(node: WorkflowNode): void {
    this.selectedNodeId = node.id;
    this.selectedEdgeId = null;
    this.inlineAddMenu = null;
    this.nodeSelected.emit(node);
  }

  selectEdge(edge: WorkflowEdge, event: MouseEvent): void {
    event.stopPropagation();
    this.selectedEdgeId = edge.id;
    this.selectedNodeId = null;
    this.inlineAddMenu = null;
    this.nodeSelected.emit(null);
  }

  deleteEdge(edgeId: string, event: MouseEvent): void {
    event.stopPropagation();
    this.edges = this.edges.filter(e => e.id !== edgeId);
    this.selectedEdgeId = null;
    this.edgesChange.emit(this.edges);
  }

  getEdgeMidpoint(edge: WorkflowEdge): { x: number; y: number } {
    const src = this.nodes.find(n => n.id === edge.source);
    const tgt = this.nodes.find(n => n.id === edge.target);
    if (!src || !tgt) return { x: 0, y: 0 };

    const srcHandles = this.getOutputHandles(src);
    const handleIndex = srcHandles.indexOf(edge.sourceHandle);
    const hPos = handleIndex >= 0 ? this.getOutputHandlePosition(src, handleIndex) : 50;

    const sx = this.nodeLeft(src) + (NODE_WIDTH * hPos) / 100;
    const sy = this.nodeTop(src) + NODE_HEIGHT;
    const tx = this.nodeLeft(tgt) + NODE_WIDTH / 2;
    const ty = this.nodeTop(tgt);

    return { x: (sx + tx) / 2, y: (sy + ty) / 2 };
  }

  // ── Mouse events ──

  onCanvasMouseDown(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (target === this.canvasEl.nativeElement || target.closest('.wfc-canvas__grid') || target.tagName === 'svg') {
      this.isPanning = true;
      this.panStart = { x: event.clientX - this.transform.x, y: event.clientY - this.transform.y };
      this.selectedNodeId = null;
      this.selectedEdgeId = null;
      this.inlineAddMenu = null;
      this.stepPickerOpen = false;
      this.nodeSelected.emit(null);
    }
  }

  onCanvasMouseMove(event: MouseEvent): void {
    if (this.isPanning) {
      this.transform = {
        ...this.transform,
        x: event.clientX - this.panStart.x,
        y: event.clientY - this.panStart.y,
      };
    }
  }

  onCanvasMouseUp(_event: MouseEvent): void {
    this.isPanning = false;
  }

  onNodeMouseDown(event: MouseEvent, node: WorkflowNode): void {
    if ((event.target as HTMLElement).closest('.wfc-handle') || (event.target as HTMLElement).closest('.wfc-node__menu') || (event.target as HTMLElement).closest('.wfc-node__mapper-btn')) return;
    event.stopPropagation();

    if (this.connectionDraft) return;

    this.selectNode(node);
    if (this.readonly) return;
    this.dragState = {
      nodeId: node.id,
      offsetX: (event.clientX - this.transform.x) / this.transform.scale - node.position.x - CANVAS_HALF,
      offsetY: (event.clientY - this.transform.y) / this.transform.scale - node.position.y - CANVAS_HALF,
    };
  }

  onNodeMouseUp(event: MouseEvent, targetNode: WorkflowNode): void {
    if (!this.connectionDraft) return;
    if (this.connectionDraft.sourceNodeId === targetNode.id) return;
    event.stopPropagation();

    const existing = this.edges.find(
      e =>
        e.source === this.connectionDraft!.sourceNodeId &&
        e.target === targetNode.id &&
        e.sourceHandle === this.connectionDraft!.sourceHandle
    );
    if (!existing) {
      const newEdge: WorkflowEdge = {
        id: `edge_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        source: this.connectionDraft.sourceNodeId,
        target: targetNode.id,
        sourceHandle: this.connectionDraft.sourceHandle,
        label: '',
      };
      this.edges = [...this.edges, newEdge];
      this.edgesChange.emit(this.edges);
    }
    this.connectionDraft = null;
  }

  onNodeDoubleClick(node: WorkflowNode): void {
    this.nodeDoubleClicked.emit(node);
  }

  onHandleMouseDown(event: MouseEvent, node: WorkflowNode, handle: string): void {
    if (this.readonly) return;
    event.stopPropagation();
    event.preventDefault();
    const rect = this.canvasEl.nativeElement.getBoundingClientRect();
    this.connectionDraft = {
      sourceNodeId: node.id,
      sourceHandle: handle,
      mouseX: (event.clientX - rect.left - this.transform.x) / this.transform.scale,
      mouseY: (event.clientY - rect.top - this.transform.y) / this.transform.scale,
    };
  }

  private onDocMouseMove(event: MouseEvent): void {
    if (this.dragState) {
      const x = (event.clientX - this.transform.x) / this.transform.scale - this.dragState.offsetX - CANVAS_HALF;
      const y = (event.clientY - this.transform.y) / this.transform.scale - this.dragState.offsetY - CANVAS_HALF;
      this.nodes = this.nodes.map(n =>
        n.id === this.dragState!.nodeId ? { ...n, position: { x, y } } : n
      );
      this.nodesChange.emit(this.nodes);
    }
    if (this.connectionDraft) {
      const rect = this.canvasEl.nativeElement.getBoundingClientRect();
      this.connectionDraft = {
        ...this.connectionDraft,
        mouseX: (event.clientX - rect.left - this.transform.x) / this.transform.scale,
        mouseY: (event.clientY - rect.top - this.transform.y) / this.transform.scale,
      };
    }
  }

  private onDocMouseUp(_event: MouseEvent): void {
    this.dragState = null;
    this.connectionDraft = null;
  }

  private onDocKeyDown(event: KeyboardEvent): void {
    if (this.readonly) return;
    const tag = (event.target as HTMLElement)?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    if (event.key === 'Delete' || event.key === 'Backspace') {
      if (this.selectedEdgeId) {
        event.preventDefault();
        this.deleteSelectedEdge();
      }
    }
    if (event.key === 'Escape') {
      this.selectedEdgeId = null;
      this.selectedNodeId = null;
      this.connectionDraft = null;
      this.inlineAddMenu = null;
      this.stepPickerOpen = false;
      this.nodeSelected.emit(null);
    }
  }

  // ── Edge geometry ──

  private nodeLeft(n: WorkflowNode): number { return n.position.x + CANVAS_HALF; }
  private nodeTop(n: WorkflowNode): number { return n.position.y + CANVAS_HALF; }

  getEdgeColor(edge: WorkflowEdge): string {
    if (this.selectedEdgeId === edge.id) return '#6366f1';
    if (this.nodeResults.length === 0) return '#cbd5e1';
    const srcStatus = this.getNodeStatus(edge.source);
    const tgtStatus = this.getNodeStatus(edge.target);
    if (srcStatus === 'success' && tgtStatus === 'success') return '#22c55e';
    if (srcStatus === 'failed' || tgtStatus === 'failed') return '#ef4444';
    if (srcStatus === 'success' && tgtStatus !== null) return '#22c55e';
    return '#e2e8f0';
  }

  getEdgeStrokeWidth(edge: WorkflowEdge): number {
    if (this.selectedEdgeId === edge.id) return 3;
    if (this.nodeResults.length === 0) return 2.5;
    const srcStatus = this.getNodeStatus(edge.source);
    const tgtStatus = this.getNodeStatus(edge.target);
    if (srcStatus && tgtStatus) return 3;
    return 2;
  }

  getEdgePath(edge: WorkflowEdge): string {
    const src = this.nodes.find(n => n.id === edge.source);
    const tgt = this.nodes.find(n => n.id === edge.target);
    if (!src || !tgt) return '';

    const srcHandles = this.getOutputHandles(src);
    const handleIndex = srcHandles.indexOf(edge.sourceHandle);
    const hPos = handleIndex >= 0 ? this.getOutputHandlePosition(src, handleIndex) : 50;

    const sx = this.nodeLeft(src) + (NODE_WIDTH * hPos) / 100;
    const sy = this.nodeTop(src) + NODE_HEIGHT;
    const tx = this.nodeLeft(tgt) + NODE_WIDTH / 2;
    const ty = this.nodeTop(tgt);

    return this.bezier(sx, sy, tx, ty);
  }

  getEdgeLabelPos(edge: WorkflowEdge): { x: number; y: number } {
    const src = this.nodes.find(n => n.id === edge.source);
    const tgt = this.nodes.find(n => n.id === edge.target);
    if (!src || !tgt) return { x: 0, y: 0 };

    const srcHandles = this.getOutputHandles(src);
    const handleIndex = srcHandles.indexOf(edge.sourceHandle);
    const hPos = handleIndex >= 0 ? this.getOutputHandlePosition(src, handleIndex) : 50;

    const sx = this.nodeLeft(src) + (NODE_WIDTH * hPos) / 100;
    const sy = this.nodeTop(src) + NODE_HEIGHT;
    const tx = this.nodeLeft(tgt) + NODE_WIDTH / 2;
    const ty = this.nodeTop(tgt);

    return { x: (sx + tx) / 2, y: (sy + ty) / 2 - 10 };
  }

  getDraftEdgePath(): string {
    if (!this.connectionDraft) return '';
    const src = this.nodes.find(n => n.id === this.connectionDraft!.sourceNodeId);
    if (!src) return '';

    const srcHandles = this.getOutputHandles(src);
    const handleIndex = srcHandles.indexOf(this.connectionDraft.sourceHandle);
    const hPos = handleIndex >= 0 ? this.getOutputHandlePosition(src, handleIndex) : 50;

    const sx = this.nodeLeft(src) + (NODE_WIDTH * hPos) / 100;
    const sy = this.nodeTop(src) + NODE_HEIGHT;
    const tx = this.connectionDraft.mouseX;
    const ty = this.connectionDraft.mouseY;

    return this.bezier(sx, sy, tx, ty);
  }

  private bezier(sx: number, sy: number, tx: number, ty: number): string {
    const dy = Math.abs(ty - sy);
    const cp = Math.max(60, dy * 0.45);
    return `M ${sx} ${sy} C ${sx} ${sy + cp}, ${tx} ${ty - cp}, ${tx} ${ty}`;
  }

  // ── Zoom ──

  zoomIn(): void {
    this.setZoom(Math.min(3, this.transform.scale * 1.2));
  }

  zoomOut(): void {
    this.setZoom(Math.max(0.15, this.transform.scale / 1.2));
  }

  fitView(): void {
    if (this.nodes.length === 0) {
      const rect = this.canvasEl.nativeElement.getBoundingClientRect();
      this.transform = { x: rect.width / 2, y: rect.height / 3, scale: 1 };
      return;
    }
    const rect = this.canvasEl.nativeElement.getBoundingClientRect();
    const xs = this.nodes.map(n => n.position.x);
    const ys = this.nodes.map(n => n.position.y);
    const minX = Math.min(...xs) + CANVAS_HALF;
    const maxX = Math.max(...xs) + CANVAS_HALF + NODE_WIDTH;
    const minY = Math.min(...ys) + CANVAS_HALF;
    const maxY = Math.max(...ys) + CANVAS_HALF + NODE_HEIGHT;
    const graphW = maxX - minX + 120;
    const graphH = maxY - minY + 120;
    const scale = Math.min(rect.width / graphW, rect.height / graphH, 1.2);
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    this.transform = {
      scale,
      x: rect.width / 2 - cx * scale,
      y: rect.height / 2 - cy * scale,
    };
  }

  private setZoom(scale: number): void {
    const rect = this.canvasEl.nativeElement.getBoundingClientRect();
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const ratio = scale / this.transform.scale;
    this.transform = {
      scale,
      x: cx - (cx - this.transform.x) * ratio,
      y: cy - (cy - this.transform.y) * ratio,
    };
  }

  private getDefaultConfig(type: WorkflowNodeType): Record<string, unknown> {
    switch (type) {
      case 'trigger':
        return { connector_name: '', event: '', filter: {} };
      case 'action':
        return { connector_name: '', action: '', field_mapping: [], on_error: 'stop' };
      case 'condition':
        return { conditions: [{ field: '', operator: 'eq', value: '' }], logic: 'and' };
      case 'switch':
        return { field: '', cases: [{ value: '', handle: 'case_1' }], default_handle: 'default' };
      case 'transform':
        return { mappings: [], expressions: {} };
      case 'filter':
        return { conditions: [{ field: '', operator: 'eq', value: '' }], logic: 'and' };
      case 'delay':
        return { seconds: 5 };
      case 'loop':
        return { array_field: '', item_variable: 'item', index_variable: 'index', max_iterations: 100 };
      case 'http_request':
        return { url: '', method: 'GET', headers: {}, body: {}, timeout_seconds: 30 };
      case 'set_variable':
        return { variable_name: '', value: '' };
      case 'think':
        return { connector_name: 'ai-agent', action: 'agent.analyze', prompt: '', output_schema_json: '', temperature: 0.1, redact_pii: true, on_error: 'stop' };
      case 'merge':
        return { strategy: 'wait_all' };
      case 'response':
        return { body: {} };
      case 'sub_workflow':
        return { workflow_id: '', timeout_seconds: 60, max_depth: 5, input_mapping: {}, on_error: 'stop' };
      case 'error_handler':
        return { catch_from: [], on_error: 'continue' };
      case 'batch':
        return { source: '', concurrency: 5, throttle_ms: 0, max_items: 1000, on_item_error: 'continue' };
      default:
        return {};
    }
  }

  updateNode(updated: WorkflowNode): void {
    this.nodes = this.nodes.map(n => (n.id === updated.id ? updated : n));
    this.nodesChange.emit(this.nodes);
  }
}
