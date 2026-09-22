import { Injectable, computed, signal } from '@angular/core';
import {
  OperatingModeConfig,
  OperatingModeName,
  VERIFIED_OPERATING_MODES,
} from '../core/models/detection.model';

/**
 * Detection & Operating Mode Service
 *
 * Backed strictly by dishant999k/angular: skyguard/config.py
 * Config.OPERATING_MODES:
 * - Maintenance: threshold 2.5, min_votes 3
 * - Balanced: threshold 2.0, min_votes 2 (DEFAULT)
 * - Extreme Weather: threshold 1.6, min_votes 2
 * - Forensic: threshold 1.2, min_votes 1
 */
@Injectable({
  providedIn: 'root',
})
export class DetectionService {
  readonly modes: OperatingModeName[] = [
    'Maintenance',
    'Balanced',
    'Extreme Weather',
    'Forensic',
  ];

  private readonly selectedMode = signal<OperatingModeName>('Balanced');

  readonly currentMode = computed<OperatingModeName>(() => this.selectedMode());

  readonly currentModeConfig = computed<OperatingModeConfig>(
    () => VERIFIED_OPERATING_MODES[this.selectedMode()]
  );

  setMode(mode: OperatingModeName): void {
    if (VERIFIED_OPERATING_MODES[mode]) {
      this.selectedMode.set(mode);
    }
  }
}
