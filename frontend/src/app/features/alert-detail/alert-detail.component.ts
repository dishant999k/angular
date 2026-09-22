import { Component } from '@angular/core';
import { ShapDiagnosisComponent } from './shap-diagnosis/shap-diagnosis.component';
import { StationBannerComponent } from './station-banner/station-banner.component';
import { TelemetrySignatureComponent } from './telemetry-signature/telemetry-signature.component';

@Component({
  selector: 'app-alert-detail',
  imports: [
    StationBannerComponent,
    ShapDiagnosisComponent,
    TelemetrySignatureComponent,
  ],
  templateUrl: './alert-detail.component.html',
  styleUrl: './alert-detail.component.scss',
})
export class AlertDetailComponent {}
