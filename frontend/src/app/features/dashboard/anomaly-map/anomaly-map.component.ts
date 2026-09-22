import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { StationService } from '../../../services/station.service';

interface MapStationNode {
  id: string;
  label: string;
  x: number;
  y: number;
  status: 'Normal' | 'Watch' | 'Alert' | 'Critical';
  zone: string;
  isCrit?: boolean;
}

@Component({
  selector: 'app-anomaly-map',
  imports: [],
  templateUrl: './anomaly-map.component.html',
  styleUrl: './anomaly-map.component.scss',
})
export class AnomalyMapComponent {
  private readonly router = inject(Router);
  protected readonly stationService = inject(StationService);

  /**
   * Station coordinates on the synoptic mesh map matching PDF Page 1
   */
  readonly mapStations: MapStationNode[] = [
    { id: 'AWS_1001', label: 'AWS_1001', x: 80, y: 310, status: 'Normal', zone: 'Zone 1' },
    { id: 'AWS_1004', label: 'AWS_1004', x: 120, y: 300, status: 'Normal', zone: 'Zone 1' },
    { id: 'AWS_1003', label: 'AWS_1003', x: 165, y: 290, status: 'Normal', zone: 'Zone 1' },
    { id: 'AWS_1011', label: 'AWS_1011', x: 200, y: 280, status: 'Normal', zone: 'Zone 1' },
    { id: 'AWS_1015', label: 'AWS_1015', x: 235, y: 250, status: 'Alert', zone: 'Zone 1' },
    { id: 'AWS_1018', label: 'AWS_1018', x: 260, y: 220, status: 'Normal', zone: 'Zone 3' },
    { id: 'AWS_1020', label: 'AWS_1020', x: 300, y: 200, status: 'Normal', zone: 'Zone 2' },
    { id: 'AWS_1027', label: 'AWS_1027', x: 340, y: 195, status: 'Normal', zone: 'Zone 2' },
    { id: 'AWS_1030', label: 'AWS_1030', x: 320, y: 270, status: 'Normal', zone: 'Zone 3' },
    { id: 'AWS_1032', label: 'AWS_1032', x: 375, y: 285, status: 'Normal', zone: 'Zone 3' },
    { id: 'AWS_1035', label: 'AWS_1035', x: 420, y: 300, status: 'Normal', zone: 'Zone 3' },
    { id: 'AWS_1008', label: 'AWS_1008', x: 220, y: 330, status: 'Watch', zone: 'Zone 3' },
    { id: 'AWS_1042', label: 'AWS_1042 [CRIT]', x: 280, y: 350, status: 'Critical', zone: 'Zone 4', isCrit: true },
    { id: 'AWS_1045', label: 'AWS_1045', x: 310, y: 380, status: 'Normal', zone: 'Zone 4' },
    { id: 'AWS_1048', label: 'AWS_1048', x: 335, y: 410, status: 'Normal', zone: 'Zone 4' },
  ];

  onStationClick(station: MapStationNode): void {
    if (station.id === 'AWS_1042') {
      this.router.navigate(['/alert-detail']);
    }
  }
}
