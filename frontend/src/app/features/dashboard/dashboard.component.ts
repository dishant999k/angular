import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { StationService } from '../../services/station.service';
import { HeaderComponent } from '../../shared/header/header.component';
import { AnomalyMapComponent } from './anomaly-map/anomaly-map.component';
import { StationDirectoryComponent } from './station-directory/station-directory.component';

@Component({
  selector: 'app-dashboard',
  imports: [
    FormsModule,
    HeaderComponent,
    AnomalyMapComponent,
    StationDirectoryComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  protected readonly stationService = inject(StationService);

  searchQuery = '';

  onSearchChange(value: string): void {
    this.stationService.setSearchQuery(value);
  }
}
