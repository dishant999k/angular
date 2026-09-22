import { Injectable, signal } from '@angular/core';
import { AlertIntelligenceReport, ShapDiagnosisPoint } from '../core/models/alert.model';

/**
 * Alert Intelligence Service
 *
 * Data models aligned with dishant999k/angular:
 * skyguard/reporting/alert_intelligence.py
 *
 * NOTE ON VALUES & ACKNOWLEDGE ACTION:
 * The exact numbers (98.4% confidence, +6.4°C, -28% RH, etc.) are reference DEMO data
 * matching the visual layout of PDF Page 3.
 * The acknowledgment state is strictly local UI state for button interaction feedback,
 * as the repository does not define a backend acknowledgment endpoint or schema.
 */
@Injectable({
  providedIn: 'root',
})
export class AlertService {
  private readonly alertReport = signal<AlertIntelligenceReport>({
    alertId: 'ALERT-AWS_1042-2026-09-20T14:15:00',
    stationId: 'AWS_1042',
    timestamp: '2026-09-20T14:15:00',
    parameter: 'Temperature',
    anomalyType: 'Multi-Condition Sensor Fault',
    rootCause: 'Sudden Temperature spike inconsistent with hourly norm',
    confidence: 98.4,
    severity: 'CRITICAL',
    votes: 3,
    weightedScore: 3.0,
    layerASpike: true,
    layerAFlatline: false,
    layerB: true,
    layerC: true,
    layerD: false,
    override: false,
    tempDev: 6.4,
    presDev: 0.0,
    rhumDev: 28.0,
    temperature: 39.8,
    pressure: 1012.4,
    humidity: 34.0,
  });

  private readonly shapPoints = signal<ShapDiagnosisPoint[]>([
    {
      id: 'heat-spike',
      title: 'Sudden Heat Spike',
      description: 'Temperature jumped rapidly by +6.4°C in under 15 minutes, which triggered the primary warning.',
      category: 'temperature',
    },
    {
      id: 'humidity-drop',
      title: 'Sharp Humidity Drop',
      description: 'Humidity plummeted by 28% at the exact same moment the heat spike occurred.',
      category: 'humidity',
    },
    {
      id: 'flat-pressure',
      title: 'Flat Air Pressure',
      description: 'Barometric pressure remained completely unchanged, ruling out an actual passing storm or weather front.',
      category: 'pressure',
    },
    {
      id: 'model-conclusion',
      title: 'Model Conclusion',
      description: 'Isolated sensor failure or hardware glitch on Probe AWS_1042 rather than an environmental weather threat.',
      category: 'conclusion',
    },
  ]);

  /**
   * Local UI-only state for Acknowledge button visual feedback.
   */
  readonly isAcknowledgedLocally = signal<boolean>(false);

  readonly currentAlert = this.alertReport.asReadonly();
  readonly diagnosisPoints = this.shapPoints.asReadonly();

  /**
   * Local UI action handler for the Acknowledge button.
   * Ready for future backend API integration.
   */
  acknowledgeAlertLocally(): void {
    this.isAcknowledgedLocally.set(!this.isAcknowledgedLocally());
  }
}
