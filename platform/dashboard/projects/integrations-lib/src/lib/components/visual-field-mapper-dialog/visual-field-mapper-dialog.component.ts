import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { ConnectorFieldDef, FieldMapping } from '../../models';
import { VisualFieldMapperComponent } from '../visual-field-mapper/visual-field-mapper.component';

export interface VisualFieldMapperDialogData {
  title: string;
  description?: string;
  sourceFields: ConnectorFieldDef[];
  destinationFields: ConnectorFieldDef[];
  mappings: FieldMapping[];
  sourceLabel?: string;
  destinationLabel?: string;
  contextHint?: string;
}

@Component({
  selector: 'pinquark-visual-field-mapper-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    VisualFieldMapperComponent,
  ],
  template: `
    <div mat-dialog-title class="vfmd__bar">
      <div class="vfmd__bar-left">
        <mat-icon class="vfmd__bar-icon">device_hub</mat-icon>
        <span class="vfmd__bar-title">{{ data.title }}</span>
        <span class="vfmd__bar-stat">{{ data.sourceFields.length }} in</span>
        <span class="vfmd__bar-stat">{{ draftMappings.length }} mapped</span>
        <span class="vfmd__bar-stat">{{ data.destinationFields.length }} out</span>
      </div>
      <button mat-icon-button (click)="dialogRef.close()" aria-label="Close">
        <mat-icon>close</mat-icon>
      </button>
    </div>

    <mat-dialog-content class="vfmd__body">
      <pinquark-visual-field-mapper
        [heading]="''"
        [description]="''"
        [sourceFields]="data.sourceFields"
        [destinationFields]="data.destinationFields"
        [mappings]="draftMappings"
        [sourceLabel]="data.sourceLabel || 'Source'"
        [destinationLabel]="data.destinationLabel || 'Target'"
        [contextHint]="''"
        (mappingsChange)="draftMappings = $event"
      ></pinquark-visual-field-mapper>
    </mat-dialog-content>

    <mat-dialog-actions align="end" class="vfmd__footer">
      <button mat-button (click)="dialogRef.close()">Cancel</button>
      <button mat-raised-button color="primary" (click)="apply()">Apply</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .vfmd__bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 16px;
      border-bottom: 1px solid #e2e8f0;
      background: #fff;
    }
    .vfmd__bar-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }
    .vfmd__bar-icon {
      width: 20px;
      height: 20px;
      font-size: 20px;
      color: #2563eb;
      flex-shrink: 0;
    }
    .vfmd__bar-title {
      font-size: 15px;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .vfmd__bar-stat {
      padding: 2px 8px;
      border-radius: 999px;
      background: #f1f5f9;
      color: #475569;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .vfmd__body {
      width: min(1280px, 94vw);
      min-width: min(1280px, 94vw);
      max-width: 94vw;
      max-height: 82vh;
      overflow: auto;
      padding: 10px 14px 6px;
      background: #f8fafc;
    }
    .vfmd__footer {
      padding: 8px 16px;
      border-top: 1px solid #e2e8f0;
      background: #fff;
    }
    @media (max-width: 900px) {
      .vfmd__body {
        width: 100vw;
        min-width: 100vw;
        max-width: 100vw;
        padding: 8px;
      }
    }
  `],
})
export class VisualFieldMapperDialogComponent {
  draftMappings: FieldMapping[];

  constructor(
    readonly dialogRef: MatDialogRef<VisualFieldMapperDialogComponent, FieldMapping[]>,
    @Inject(MAT_DIALOG_DATA) readonly data: VisualFieldMapperDialogData,
  ) {
    this.draftMappings = data.mappings.map(mapping => ({ ...mapping }));
  }

  apply(): void {
    this.dialogRef.close(this.draftMappings.map(mapping => ({ ...mapping })));
  }
}
