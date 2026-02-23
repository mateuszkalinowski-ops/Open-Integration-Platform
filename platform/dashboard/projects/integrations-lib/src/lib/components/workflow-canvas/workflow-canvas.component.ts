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
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatBadgeModule } from '@angular/material/badge';
import {
  WorkflowNode,
  WorkflowEdge,
  WorkflowNodeType,
  NODE_TYPE_DEFINITIONS,
  NodeTypeDefinition,
  WorkflowNodeResult,
} from '../../models';

const NODE_WIDTH = 220;
const NODE_HEIGHT = 72;
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

@Component({
  selector: 'pinquark-workflow-canvas',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatTooltipModule,
    MatChipsModule,
    MatBadgeModule,
  ],
  template: `
    <div class="wf-canvas-wrapper">
      <!-- Toolbar -->
      <div class="wf-toolbar">
        <div class="wf-toolbar__left">
          <button mat-icon-button matTooltip="Zoom In" (click)="zoomIn()">
            <mat-icon>zoom_in</mat-icon>
          </button>
          <button mat-icon-button matTooltip="Zoom Out" (click)="zoomOut()">
            <mat-icon>zoom_out</mat-icon>
          </button>
          <button mat-icon-button matTooltip="Fit View" (click)="fitView()">
            <mat-icon>fit_screen</mat-icon>
          </button>
          <span class="wf-toolbar__zoom">{{ (transform.scale * 100) | number:'1.0-0' }}%</span>
        </div>
        @if (!readonly) {
          <div class="wf-toolbar__right">
            <button mat-icon-button [matMenuTriggerFor]="addNodeMenu" matTooltip="Add Node">
              <mat-icon>add_circle</mat-icon>
            </button>
            <mat-menu #addNodeMenu="matMenu" class="wf-node-menu">
              @for (cat of nodeCategories; track cat.name) {
                <div class="wf-node-menu__category">{{ cat.name }}</div>
                @for (def of cat.defs; track def.type) {
                  <button mat-menu-item (click)="addNode(def.type)">
                    <mat-icon [style.color]="def.color">{{ def.icon }}</mat-icon>
                    <span>{{ def.label }}</span>
                  </button>
                }
              }
            </mat-menu>
          </div>
        }
      </div>

      <!-- Canvas -->
      <div
        class="wf-canvas"
        #canvasEl
        (mousedown)="onCanvasMouseDown($event)"
        (mousemove)="onCanvasMouseMove($event)"
        (mouseup)="onCanvasMouseUp($event)"
        (wheel)="onCanvasWheel($event)"
        (contextmenu)="$event.preventDefault()"
      >
        <div
          class="wf-canvas__inner"
          [style.transform]="'translate(' + transform.x + 'px, ' + transform.y + 'px) scale(' + transform.scale + ')'"
        >
          <!-- Grid pattern background -->
          <svg class="wf-canvas__grid">
            <defs>
              <pattern id="grid-small" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,0,0,0.05)" stroke-width="0.5" />
              </pattern>
              <pattern id="grid-large" width="100" height="100" patternUnits="userSpaceOnUse">
                <rect width="100" height="100" fill="url(#grid-small)" />
                <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(0,0,0,0.1)" stroke-width="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid-large)" />
          </svg>

          <!-- Edges SVG — same coordinate space as node CSS positions -->
          <svg class="wf-canvas__edges">
            @for (edge of edges; track edge.id) {
              <g>
                <path
                  [attr.d]="getEdgePath(edge)"
                  fill="none"
                  [attr.stroke]="getEdgeColor(edge)"
                  [attr.stroke-width]="getEdgeStrokeWidth(edge)"
                  stroke-linecap="round"
                  class="wf-edge-path"
                  (click)="selectEdge(edge, $event)"
                />
                @if (edge.sourceHandle && edge.sourceHandle !== 'default') {
                  <text
                    [attr.x]="getEdgeLabelPos(edge).x"
                    [attr.y]="getEdgeLabelPos(edge).y"
                    text-anchor="middle"
                    fill="#546e7a"
                    font-size="11"
                    font-weight="500"
                  >{{ edge.sourceHandle }}</text>
                }
                @if (!readonly && selectedEdgeId === edge.id) {
                  <g class="wf-edge-delete" (click)="deleteEdge(edge.id, $event)">
                    <circle
                      [attr.cx]="getEdgeMidpoint(edge).x"
                      [attr.cy]="getEdgeMidpoint(edge).y"
                      r="12"
                      fill="#f44336"
                      class="wf-edge-delete__bg"
                    />
                    <line
                      [attr.x1]="getEdgeMidpoint(edge).x - 4"
                      [attr.y1]="getEdgeMidpoint(edge).y - 4"
                      [attr.x2]="getEdgeMidpoint(edge).x + 4"
                      [attr.y2]="getEdgeMidpoint(edge).y + 4"
                      stroke="#fff" stroke-width="2" stroke-linecap="round"
                    />
                    <line
                      [attr.x1]="getEdgeMidpoint(edge).x + 4"
                      [attr.y1]="getEdgeMidpoint(edge).y - 4"
                      [attr.x2]="getEdgeMidpoint(edge).x - 4"
                      [attr.y2]="getEdgeMidpoint(edge).y + 4"
                      stroke="#fff" stroke-width="2" stroke-linecap="round"
                    />
                  </g>
                }
              </g>
            }
            @if (connectionDraft) {
              <path
                [attr.d]="getDraftEdgePath()"
                fill="none"
                stroke="#1976d2"
                stroke-width="2"
                stroke-dasharray="6 4"
                stroke-linecap="round"
              />
            }
          </svg>

          <!-- Nodes -->
          @for (node of nodes; track node.id) {
            <div
              class="wf-node"
              [class.wf-node--selected]="selectedNodeId === node.id"
              [class.wf-node--success]="getNodeStatus(node.id) === 'success'"
              [class.wf-node--failed]="getNodeStatus(node.id) === 'failed'"
              [class.wf-node--filtered]="getNodeStatus(node.id) === 'filtered'"
              [class.wf-node--running]="getNodeStatus(node.id) === 'running'"
              [class.wf-node--unexecuted]="nodeResults.length > 0 && getNodeStatus(node.id) === null"
              [class.wf-node--drop-target]="connectionDraft && connectionDraft.sourceNodeId !== node.id"
              [class.wf-node--readonly]="readonly"
              [style.left.px]="node.position.x + HALF"
              [style.top.px]="node.position.y + HALF"
              (mousedown)="onNodeMouseDown($event, node)"
              (mouseup)="onNodeMouseUp($event, node)"
              (dblclick)="onNodeDoubleClick(node)"
            >
              <div class="wf-node__header" [style.background]="getNodeHeaderColor(node)">
                <mat-icon class="wf-node__icon">{{ getNodeDef(node.type)?.icon || 'help' }}</mat-icon>
                <span class="wf-node__type">{{ getNodeDef(node.type)?.label || node.type }}</span>
                @if (!readonly) {
                  <button class="wf-node__delete" (click)="deleteNode(node.id, $event)" matTooltip="Delete node">
                    <mat-icon>close</mat-icon>
                  </button>
                }
              </div>
              <div class="wf-node__body">
                <span class="wf-node__label">{{ node.label || getNodeSummary(node) }}</span>
              </div>
              @if (!readonly) {
                <!-- Input handles -->
                @for (handle of getInputHandles(node); track handle) {
                  <div
                    class="wf-handle wf-handle--input"
                    [attr.data-handle]="handle"
                  ></div>
                }
                <!-- Output handles -->
                @for (handle of getOutputHandles(node); track handle; let hi = $index) {
                  <div
                    class="wf-handle wf-handle--output"
                    [style.left.%]="getOutputHandlePosition(node, hi)"
                    [attr.data-handle]="handle"
                    [matTooltip]="handle !== 'default' ? handle : ''"
                    (mousedown)="onHandleMouseDown($event, node, handle)"
                  >
                    @if (handle !== 'default' && getOutputHandles(node).length > 1) {
                      <span class="wf-handle__label">{{ handle }}</span>
                    }
                  </div>
                }
              }
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .wf-canvas-wrapper {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      background: #fafafa;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      overflow: hidden;
    }
    .wf-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 12px;
      background: #fff;
      border-bottom: 1px solid #e0e0e0;
      z-index: 10;
    }
    .wf-toolbar__left, .wf-toolbar__right { display: flex; align-items: center; gap: 4px; }
    .wf-toolbar__zoom { font-size: 12px; color: #666; margin-left: 8px; min-width: 40px; }
    .wf-canvas {
      flex: 1;
      overflow: hidden;
      cursor: grab;
      position: relative;
    }
    .wf-canvas:active { cursor: grabbing; }
    .wf-canvas__inner {
      position: absolute;
      transform-origin: 0 0;
      width: 0;
      height: 0;
    }
    .wf-canvas__grid {
      position: absolute;
      top: 0;
      left: 0;
      width: 6000px;
      height: 6000px;
      pointer-events: none;
    }
    .wf-canvas__edges {
      position: absolute;
      top: 0;
      left: 0;
      width: 6000px;
      height: 6000px;
      overflow: visible;
      pointer-events: none;
    }
    .wf-edge-path { pointer-events: stroke; cursor: pointer; }
    .wf-edge-path:hover { stroke-width: 4; }
    .wf-edge-delete { pointer-events: all; cursor: pointer; }
    .wf-edge-delete__bg { transition: r 0.15s, fill 0.15s; }
    .wf-edge-delete:hover .wf-edge-delete__bg { r: 14; fill: #d32f2f; }

    /* Nodes */
    .wf-node {
      position: absolute;
      width: 220px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.12);
      cursor: move;
      user-select: none;
      transition: box-shadow 0.15s;
      z-index: 5;
    }
    .wf-node:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.18); }
    .wf-node--selected {
      box-shadow: 0 0 0 2px #1976d2, 0 4px 16px rgba(0,0,0,0.18);
    }
    .wf-node--drop-target { cursor: crosshair; }
    .wf-node--drop-target:hover {
      box-shadow: 0 0 0 3px #1976d2, 0 4px 20px rgba(25,118,210,0.3);
    }
    .wf-node--success { box-shadow: 0 0 0 3px #4caf50, 0 4px 16px rgba(76,175,80,0.25); }
    .wf-node--failed { box-shadow: 0 0 0 3px #f44336, 0 4px 16px rgba(244,67,54,0.25); }
    .wf-node--filtered { box-shadow: 0 0 0 3px #ff9800, 0 4px 16px rgba(255,152,0,0.25); }
    .wf-node--running { animation: pulse 1.5s ease-in-out infinite; }
    .wf-node--unexecuted {
      opacity: 0.5;
      box-shadow: 0 0 0 2px #9e9e9e, 0 2px 6px rgba(0,0,0,0.08);
    }
    .wf-node--unexecuted .wf-node__header { filter: grayscale(0.7); }
    .wf-node--readonly { cursor: default; }
    .wf-node--readonly:hover { box-shadow: inherit; }
    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 0 2px #2196f3, 0 4px 16px rgba(33,150,243,0.2); }
      50% { box-shadow: 0 0 0 4px #2196f3, 0 4px 20px rgba(33,150,243,0.35); }
    }

    .wf-node__header {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 8px 8px 0 0;
      color: #fff;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .wf-node__icon { font-size: 16px; width: 16px; height: 16px; }
    .wf-node__type { flex: 1; }
    .wf-node__delete {
      background: none;
      border: none;
      color: rgba(255,255,255,0.7);
      cursor: pointer;
      padding: 0;
      display: flex;
      opacity: 0;
      transition: opacity 0.15s;
    }
    .wf-node:hover .wf-node__delete { opacity: 1; }
    .wf-node__delete mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .wf-node__body {
      padding: 10px 12px;
      font-size: 13px;
      color: #333;
      min-height: 28px;
    }
    .wf-node__label {
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Handles — bigger hit targets */
    .wf-handle {
      position: absolute;
      width: 16px;
      height: 16px;
      background: #fff;
      border: 2.5px solid #90a4ae;
      border-radius: 50%;
      cursor: crosshair;
      z-index: 6;
      transition: transform 0.1s, background 0.1s, border-color 0.1s;
    }
    .wf-handle:hover {
      transform: scale(1.5);
      background: #1976d2;
      border-color: #1976d2;
    }
    .wf-handle--input {
      top: -8px;
      left: 50%;
      margin-left: -8px;
    }
    .wf-handle--output {
      bottom: -8px;
      margin-left: -8px;
    }
    .wf-handle__label {
      position: absolute;
      bottom: -16px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 9px;
      color: #666;
      white-space: nowrap;
      pointer-events: none;
    }

    .wf-node-menu .wf-node-menu__category {
      padding: 8px 16px 4px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #999;
    }
  `],
})
export class WorkflowCanvasComponent implements OnInit, OnChanges, OnDestroy {
  @Input() nodes: WorkflowNode[] = [];
  @Input() edges: WorkflowEdge[] = [];
  @Input() nodeResults: WorkflowNodeResult[] = [];
  @Input() readonly = false;
  @Output() nodesChange = new EventEmitter<WorkflowNode[]>();
  @Output() edgesChange = new EventEmitter<WorkflowEdge[]>();
  @Output() nodeSelected = new EventEmitter<WorkflowNode | null>();
  @Output() nodeDoubleClicked = new EventEmitter<WorkflowNode>();

  @ViewChild('canvasEl', { static: true }) canvasEl!: ElementRef<HTMLDivElement>;

  readonly HALF = CANVAS_HALF;

  transform: CanvasTransform = { x: 0, y: 0, scale: 1 };
  selectedNodeId: string | null = null;
  selectedEdgeId: string | null = null;

  dragState: DragState | null = null;
  connectionDraft: ConnectionDraft | null = null;
  isPanning = false;
  panStart = { x: 0, y: 0 };

  readonly nodeDefs: Map<string, NodeTypeDefinition>;
  readonly nodeCategories: { name: string; defs: NodeTypeDefinition[] }[];

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

  getNodeDef(type: WorkflowNodeType): NodeTypeDefinition | undefined {
    return this.nodeDefs.get(type);
  }

  getNodeStatus(nodeId: string): string | null {
    const r = this.nodeResults.find(nr => nr.node_id === nodeId);
    return r?.status ?? null;
  }

  getNodeHeaderColor(node: WorkflowNode): string {
    if (this.nodeResults.length > 0 && this.getNodeStatus(node.id) === null) {
      return '#9e9e9e';
    }
    return this.getNodeDef(node.type)?.color || '#666';
  }

  getNodeSummary(node: WorkflowNode): string {
    const cfg = node.config;
    switch (node.type) {
      case 'trigger':
        return cfg['connector_name'] ? `${cfg['connector_name']} / ${cfg['event'] || ''}` : 'Configure trigger...';
      case 'action':
        return cfg['connector_name'] ? `${cfg['connector_name']} → ${cfg['action'] || ''}` : 'Configure action...';
      case 'condition':
        return (cfg['conditions'] as unknown[])?.length ? `${(cfg['conditions'] as unknown[]).length} condition(s)` : 'Configure condition...';
      case 'switch':
        return cfg['field'] ? `Switch on ${cfg['field']}` : 'Configure switch...';
      case 'transform':
        return (cfg['mappings'] as unknown[])?.length ? `${(cfg['mappings'] as unknown[]).length} mapping(s)` : 'Configure transform...';
      case 'delay':
        return cfg['seconds'] ? `Wait ${cfg['seconds']}s` : 'Configure delay...';
      case 'loop':
        return cfg['array_field'] ? `Loop over ${cfg['array_field']}` : 'Configure loop...';
      case 'http_request':
        return cfg['url'] ? `${cfg['method'] || 'GET'} ${cfg['url']}` : 'Configure request...';
      case 'set_variable':
        return cfg['variable_name'] ? `Set ${cfg['variable_name']}` : 'Configure variable...';
      case 'filter':
        return (cfg['conditions'] as unknown[])?.length ? `${(cfg['conditions'] as unknown[]).length} filter(s)` : 'Configure filter...';
      case 'think': {
        let summary = cfg['prompt'] ? `AI: ${(cfg['prompt'] as string).slice(0, 40)}${(cfg['prompt'] as string).length > 40 ? '...' : ''}` : 'Configure AI agent...';
        if (cfg['output_schema_json']) {
          try {
            const keys = Object.keys(JSON.parse(cfg['output_schema_json'] as string));
            if (keys.length > 0) summary += ` → ${keys.join(', ')}`;
          } catch { /* ignore */ }
        }
        return summary;
      }
      default:
        return node.type;
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

  addNode(type: WorkflowNodeType): void {
    this.nodeIdCounter++;
    const id = `node_${this.nodeIdCounter}`;
    const rect = this.canvasEl.nativeElement.getBoundingClientRect();
    const centerX = (rect.width / 2 - this.transform.x) / this.transform.scale - CANVAS_HALF;
    const centerY = (rect.height / 2 - this.transform.y) / this.transform.scale - CANVAS_HALF;

    const newNode: WorkflowNode = {
      id,
      type,
      label: '',
      position: { x: centerX - 110 + Math.random() * 40, y: centerY - 30 + Math.random() * 40 },
      config: this.getDefaultConfig(type),
    };
    this.nodes = [...this.nodes, newNode];
    this.nodesChange.emit(this.nodes);
    this.selectNode(newNode);
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
    this.nodeSelected.emit(node);
  }

  selectEdge(edge: WorkflowEdge, event: MouseEvent): void {
    event.stopPropagation();
    this.selectedEdgeId = edge.id;
    this.selectedNodeId = null;
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
    if (target === this.canvasEl.nativeElement || target.closest('.wf-canvas__grid') || target.tagName === 'svg') {
      this.isPanning = true;
      this.panStart = { x: event.clientX - this.transform.x, y: event.clientY - this.transform.y };
      this.selectedNodeId = null;
      this.selectedEdgeId = null;
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

  onCanvasWheel(event: WheelEvent): void {
    event.preventDefault();
    const rect = this.canvasEl.nativeElement.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;

    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.15, Math.min(3, this.transform.scale * delta));
    const scaleRatio = newScale / this.transform.scale;

    this.transform = {
      scale: newScale,
      x: mouseX - (mouseX - this.transform.x) * scaleRatio,
      y: mouseY - (mouseY - this.transform.y) * scaleRatio,
    };
  }

  onNodeMouseDown(event: MouseEvent, node: WorkflowNode): void {
    if ((event.target as HTMLElement).closest('.wf-handle') || (event.target as HTMLElement).closest('.wf-node__delete')) return;
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

  /** Releasing mouse on any part of a node completes the connection */
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
      this.nodeSelected.emit(null);
    }
  }

  // ── Edge geometry ──
  // All coordinates are in the same space as node CSS positions:
  //   node CSS left = node.position.x + CANVAS_HALF
  //   SVG is at (0,0), so SVG coords = CSS coords directly

  private nodeLeft(n: WorkflowNode): number { return n.position.x + CANVAS_HALF; }
  private nodeTop(n: WorkflowNode): number { return n.position.y + CANVAS_HALF; }

  getEdgeColor(edge: WorkflowEdge): string {
    if (this.selectedEdgeId === edge.id) return '#1976d2';
    if (this.nodeResults.length === 0) return '#90a4ae';
    const srcStatus = this.getNodeStatus(edge.source);
    const tgtStatus = this.getNodeStatus(edge.target);
    if (srcStatus === 'success' && tgtStatus === 'success') return '#4caf50';
    if (srcStatus === 'failed' || tgtStatus === 'failed') return '#f44336';
    if (srcStatus === 'success' && tgtStatus !== null) return '#4caf50';
    return '#bdbdbd';
  }

  getEdgeStrokeWidth(edge: WorkflowEdge): number {
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

    return { x: (sx + tx) / 2, y: (sy + ty) / 2 - 8 };
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
    const cp = Math.max(50, dy * 0.5);
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
    const graphW = maxX - minX + 100;
    const graphH = maxY - minY + 100;
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
      default:
        return {};
    }
  }

  updateNode(updated: WorkflowNode): void {
    this.nodes = this.nodes.map(n => (n.id === updated.id ? updated : n));
    this.nodesChange.emit(this.nodes);
  }
}
