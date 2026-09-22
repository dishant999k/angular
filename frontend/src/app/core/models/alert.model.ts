/**
 * Alert Intelligence models verified from dishant999k/angular:
 * skyguard/reporting/alert_intelligence.py
 * skyguard/config.py
 */

export type AnomalySeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface AlertIntelligenceReport {
  alertId: string;
  stationId: string;
  timestamp: string;
  parameter: string;
  anomalyType: string;
  rootCause: string;
  confidence: number;
  severity: AnomalySeverity;
  votes: number;
  weightedScore: number;
  layerASpike: boolean;
  layerAFlatline: boolean;
  layerB: boolean;
  layerC: boolean;
  layerD: boolean;
  override: boolean;
  tempDev: number;
  presDev: number;
  rhumDev: number;
  temperature: number;
  pressure: number;
  humidity: number;
}

export interface ShapDiagnosisPoint {
  id: string;
  title: string;
  description: string;
  category: 'temperature' | 'humidity' | 'pressure' | 'conclusion';
}

export interface TelemetryReadingPoint {
  timeLabel: string;
  temperature: number;
  humidity: number;
  pressure: number;
  isEvent?: boolean;
}

export interface MultivariateTelemetrySignature {
  stationId: string;
  currentTemperature: number;
  tempDelta: string;
  currentHumidity: number;
  rhDelta: string;
  currentPressure: number;
  baroDelta: string;
  eventTime: string;
  thermalDeltaSummary: string;
  rhDeltaSummary: string;
  baroDeltaSummary: string;
  timeSeries: TelemetryReadingPoint[];
}
