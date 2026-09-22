import { Injectable, computed, signal } from '@angular/core';
import { StationDirectorySummary, StationRecord } from '../core/models/station.model';

/**
 * Station Data Service
 *
 * Provides station records and directory statistics for the SkyGuard AI dashboard.
 *
 * NOTE ON DATA SOURCE:
 * The primary station 'AWS_1042' is verified from the repository (Config.STATION_ID = "AWS_1042").
 * Additional station records below are reference demo records structured to match the visual
 * layout of PDF Page 1 ("24 Nodes Online"). They are explicitly segregated here as mock UI data
 * and are ready to be connected to a live backend REST endpoint when available.
 */
@Injectable({
  providedIn: 'root',
})
export class StationService {
  /**
   * Reference mock station records reproducing PDF Page 1 directory layout.
   */
  private readonly stations = signal<StationRecord[]>([
    {
      stationId: 'AWS_1042',
      zone: 'Zone 4',
      status: 'Critical',
      updated: '14:23:01 UTC',
      isPrimary: true,
      sector: 'Zone 2 — North Sector',
      arrayName: 'Primary Meteorological Array',
      mastId: 'MAST-04 ARRAY',
      lat: 26.9124,
      lon: 75.7873,
    },
    { stationId: 'AWS_1015', zone: 'Zone 1', status: 'Alert', updated: '14:22:54 UTC', lat: 26.85, lon: 75.70 },
    { stationId: 'AWS_1061', zone: 'Zone 2', status: 'Alert', updated: '14:22:38 UTC', lat: 27.05, lon: 75.85 },
    { stationId: 'AWS_1008', zone: 'Zone 3', status: 'Watch', updated: '14:22:15 UTC', lat: 26.95, lon: 75.65 },
    { stationId: 'AWS_1033', zone: 'Zone 4', status: 'Watch', updated: '14:21:55 UTC', lat: 26.78, lon: 75.92 },
    { stationId: 'AWS_1001', zone: 'Zone 1', status: 'Normal', updated: '14:22:15 UTC', lat: 26.70, lon: 75.60 },
    { stationId: 'AWS_1004', zone: 'Zone 1', status: 'Normal', updated: '14:21:10 UTC', lat: 26.75, lon: 75.62 },
    { stationId: 'AWS_1012', zone: 'Zone 2', status: 'Normal', updated: '14:22:04 UTC', lat: 27.02, lon: 75.80 },
    { stationId: 'AWS_1018', zone: 'Zone 3', status: 'Normal', updated: '14:20:49 UTC', lat: 26.92, lon: 75.72 },
    { stationId: 'AWS_1022', zone: 'Zone 1', status: 'Normal', updated: '14:21:48 UTC', lat: 26.80, lon: 75.68 },
    { stationId: 'AWS_1027', zone: 'Zone 2', status: 'Normal', updated: '14:19:30 UTC', lat: 27.08, lon: 75.88 },
    { stationId: 'AWS_1030', zone: 'Zone 3', status: 'Normal', updated: '14:21:12 UTC', lat: 26.98, lon: 75.75 },
    { stationId: 'AWS_1003', zone: 'Zone 1', status: 'Normal', updated: '14:21:05 UTC', lat: 26.73, lon: 75.65 },
    { stationId: 'AWS_1011', zone: 'Zone 1', status: 'Normal', updated: '14:20:55 UTC', lat: 26.82, lon: 75.64 },
    { stationId: 'AWS_1020', zone: 'Zone 2', status: 'Normal', updated: '14:20:10 UTC', lat: 27.04, lon: 75.82 },
    { stationId: 'AWS_1032', zone: 'Zone 3', status: 'Normal', updated: '14:20:40 UTC', lat: 26.96, lon: 75.78 },
    { stationId: 'AWS_1035', zone: 'Zone 3', status: 'Normal', updated: '14:19:55 UTC', lat: 26.94, lon: 75.82 },
    { stationId: 'AWS_1045', zone: 'Zone 4', status: 'Normal', updated: '14:21:30 UTC', lat: 26.76, lon: 75.95 },
    { stationId: 'AWS_1048', zone: 'Zone 4', status: 'Normal', updated: '14:21:18 UTC', lat: 26.74, lon: 75.98 },
    { stationId: 'AWS_1050', zone: 'Zone 2', status: 'Normal', updated: '14:19:15 UTC', lat: 27.10, lon: 75.90 },
    { stationId: 'AWS_1052', zone: 'Zone 2', status: 'Normal', updated: '14:18:50 UTC', lat: 27.06, lon: 75.92 },
    { stationId: 'AWS_1055', zone: 'Zone 3', status: 'Normal', updated: '14:18:22 UTC', lat: 26.90, lon: 75.79 },
    { stationId: 'AWS_1058', zone: 'Zone 4', status: 'Normal', updated: '14:18:05 UTC', lat: 26.72, lon: 75.90 },
    { stationId: 'AWS_1060', zone: 'Zone 4', status: 'Normal', updated: '14:17:40 UTC', lat: 26.70, lon: 75.93 },
  ]);

  /**
   * Filter query from search field: "Search stations by ID, zone, or status..."
   */
  readonly searchQuery = signal<string>('');

  /**
   * Filtered station records without altering server or default order (no sorting).
   */
  readonly filteredStations = computed(() => {
    const query = this.searchQuery().trim().toLowerCase();
    const all = this.stations();
    if (!query) {
      return all;
    }
    return all.filter(
      (s) =>
        s.stationId.toLowerCase().includes(query) ||
        s.zone.toLowerCase().includes(query) ||
        s.status.toLowerCase().includes(query)
    );
  });

  /**
   * Directory summary matching PDF: "24 Nodes Online | 19 Normal 2 Watch 2 Alert 1 Critical"
   */
  readonly summary = computed<StationDirectorySummary>(() => {
    const list = this.stations();
    return {
      totalNodesOnline: list.length,
      normalCount: list.filter((s) => s.status === 'Normal').length,
      watchCount: list.filter((s) => s.status === 'Watch').length,
      alertCount: list.filter((s) => s.status === 'Alert').length,
      criticalCount: list.filter((s) => s.status === 'Critical').length,
    };
  });

  getStationById(id: string): StationRecord | undefined {
    return this.stations().find((s) => s.stationId.toUpperCase() === id.toUpperCase());
  }

  setSearchQuery(query: string): void {
    this.searchQuery.set(query);
  }
}
