/**
 * Detection & Operating Mode models verified strictly from dishant999k/angular:
 * skyguard/config.py: Config.OPERATING_MODES
 * skyguard/detection_layers/
 */

export type OperatingModeName = 'Maintenance' | 'Balanced' | 'Extreme Weather' | 'Forensic';

export interface OperatingModeConfig {
  name: OperatingModeName;
  threshold: number;
  minVotes: number;
  description: string;
}

export const VERIFIED_OPERATING_MODES: Record<OperatingModeName, OperatingModeConfig> = {
  Maintenance: {
    name: 'Maintenance',
    threshold: 2.5,
    minVotes: 3,
    description: 'Routine audits — very strict',
  },
  Balanced: {
    name: 'Balanced',
    threshold: 2.0,
    minVotes: 2,
    description: 'Standard operations',
  },
  'Extreme Weather': {
    name: 'Extreme Weather',
    threshold: 1.6,
    minVotes: 2,
    description: 'Cyclone / heavy rain',
  },
  Forensic: {
    name: 'Forensic',
    threshold: 1.2,
    minVotes: 1,
    description: 'Post-event — catch everything',
  },
};

export type StationStatusLevel = 'Normal' | 'Watch' | 'Alert' | 'Critical';

export interface DetectionLayerEvidence {
  layerASpike: boolean;       // Layer A: Statistical temperature spike
  layerAFlatline: boolean;    // Layer A: Sensor flatline
  layerB: boolean;            // Layer B: Mahalanobis Distance
  layerC: boolean;            // Layer C: Isolation Forest
  layerD: boolean;            // Layer D: Spatial Consistency
  flatlineOverride: boolean;  // Override rule: persistent frozen sensor
  votes: number;              // Total distinct layer votes (0-4)
  weightedScore: number;      // Weighted score from combination logic
}
