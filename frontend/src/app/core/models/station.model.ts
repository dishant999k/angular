import { StationStatusLevel } from './detection.model';

export type ZoneName = 'Zone 1' | 'Zone 2' | 'Zone 3' | 'Zone 4';

export interface StationRecord {
  stationId: string;
  zone: ZoneName;
  status: StationStatusLevel;
  updated: string;
  isPrimary?: boolean;
  sector?: string;
  arrayName?: string;
  mastId?: string;
  lat?: number;
  lon?: number;
}

export interface StationDirectorySummary {
  totalNodesOnline: number;
  normalCount: number;
  watchCount: number;
  alertCount: number;
  criticalCount: number;
}
