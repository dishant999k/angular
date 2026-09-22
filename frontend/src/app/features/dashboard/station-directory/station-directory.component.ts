import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { StationRecord } from '../../../core/models/station.model';
import { StationService } from '../../../services/station.service';

@Component({
  selector: 'app-station-directory',
  imports: [],
  templateUrl: './station-directory.component.html',
  styleUrl: './station-directory.component.scss',
})
export class StationDirectoryComponent {
  private readonly router = inject(Router);
  protected readonly stationService = inject(StationService);

  onRowClick(station: StationRecord): void {
    if (station.stationId === 'AWS_1042') {
      this.router.navigate(['/alert-detail']);
    }
  }
}
