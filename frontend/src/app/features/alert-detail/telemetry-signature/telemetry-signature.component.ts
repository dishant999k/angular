import { Component, inject } from '@angular/core';
import { TelemetryService } from '../../../services/telemetry.service';

@Component({
  selector: 'app-telemetry-signature',
  imports: [],
  templateUrl: './telemetry-signature.component.html',
  styleUrl: './telemetry-signature.component.scss',
})
export class TelemetrySignatureComponent {
  protected readonly telemetryService = inject(TelemetryService);
}
