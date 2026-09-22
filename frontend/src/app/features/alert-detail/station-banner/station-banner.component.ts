import { Component, inject } from '@angular/core';
import { AlertService } from '../../../services/alert.service';

@Component({
  selector: 'app-station-banner',
  imports: [],
  templateUrl: './station-banner.component.html',
  styleUrl: './station-banner.component.scss',
})
export class StationBannerComponent {
  protected readonly alertService = inject(AlertService);

  onAcknowledgeClick(): void {
    // Local UI action only, ready for future backend integration
    this.alertService.acknowledgeAlertLocally();
  }
}
