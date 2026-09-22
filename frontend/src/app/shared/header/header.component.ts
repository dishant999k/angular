import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { OperatingModeName } from '../../core/models/detection.model';
import { DetectionService } from '../../services/detection.service';
import { StationService } from '../../services/station.service';

@Component({
  selector: 'app-header',
  imports: [],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
})
export class HeaderComponent implements OnInit, OnDestroy {
  protected readonly detectionService = inject(DetectionService);
  protected readonly stationService = inject(StationService);

  utcTimeString = '00:00:00 UTC';
  private timerInterval: any;

  ngOnInit(): void {
    this.updateUtcTime();
    this.timerInterval = setInterval(() => {
      this.updateUtcTime();
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }

  updateUtcTime(): void {
    const now = new Date();
    const hours = String(now.getUTCHours()).padStart(2, '0');
    const minutes = String(now.getUTCMinutes()).padStart(2, '0');
    const seconds = String(now.getUTCSeconds()).padStart(2, '0');
    this.utcTimeString = `${hours}:${minutes}:${seconds} UTC`;
  }

  onModeSelect(mode: OperatingModeName): void {
    this.detectionService.setMode(mode);
  }
}
