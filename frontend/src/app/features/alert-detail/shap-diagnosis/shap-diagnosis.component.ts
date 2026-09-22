import { Component, inject } from '@angular/core';
import { AlertService } from '../../../services/alert.service';

@Component({
  selector: 'app-shap-diagnosis',
  imports: [],
  templateUrl: './shap-diagnosis.component.html',
  styleUrl: './shap-diagnosis.component.scss',
})
export class ShapDiagnosisComponent {
  protected readonly alertService = inject(AlertService);
}
