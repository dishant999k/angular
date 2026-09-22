import { Injectable, signal } from '@angular/core';
import { MultivariateTelemetrySignature } from '../core/models/alert.model';

/**
 * Multivariate Telemetry Service
 *
 * Provides 24-hour time series telemetry for the three verified parameters:
 * - temp: Air Temperature (°C)
 * - rhum: Relative Humidity (%)
 * - pres: Barometric Pressure (hPa)
 *
 * NOTE ON DATA SOURCE:
 * The exact numbers shown in PDF Page 3 (e.g. 39.8°C, +6.4°C, 34% RH, -28% RH, 1012.4 hPa,
 * 0.0 hPa, 14:15 Event) are implemented here as MOCK/DEMO frontend reference data specifically
 * to reproduce the visual layout and fidelity of the PDF. They are clearly segregated here
 * and ready to be replaced by live telemetry API responses when connected to the backend.
 */
@Injectable({
  providedIn: 'root',
})
export class TelemetryService {
  private readonly telemetrySignature = signal<MultivariateTelemetrySignature>({
    stationId: 'AWS_1042',
    currentTemperature: 39.8,
    tempDelta: '+6.4°C / 15m',
    currentHumidity: 34,
    rhDelta: '-28% RH',
    currentPressure: 1012.4,
    baroDelta: '0.0 hPa (Flat)',
    eventTime: '14:15 (Event)',
    thermalDeltaSummary: '+6.4°C',
    rhDeltaSummary: '-28%',
    baroDeltaSummary: '0.0 hPa',
    timeSeries: [
      { timeLabel: '00:00', temperature: 24.2, humidity: 72, pressure: 1012.3 },
      { timeLabel: '02:00', temperature: 23.5, humidity: 76, pressure: 1012.4 },
      { timeLabel: '04:00', temperature: 22.8, humidity: 80, pressure: 1012.5 },
      { timeLabel: '06:00', temperature: 24.0, humidity: 78, pressure: 1012.4 },
      { timeLabel: '08:00', temperature: 27.5, humidity: 68, pressure: 1012.4 },
      { timeLabel: '10:00', temperature: 31.0, humidity: 58, pressure: 1012.3 },
      { timeLabel: '12:00', temperature: 33.4, humidity: 52, pressure: 1012.4 },
      { timeLabel: '13:00', temperature: 33.5, humidity: 51, pressure: 1012.4 },
      { timeLabel: '14:00', temperature: 33.4, humidity: 51, pressure: 1012.4 },
      // Sudden spike & drop event at 14:15
      { timeLabel: '14:15 (Event)', temperature: 39.8, humidity: 34, pressure: 1012.4, isEvent: true },
      { timeLabel: '15:00', temperature: 39.2, humidity: 35, pressure: 1012.4 },
      { timeLabel: '16:00', temperature: 37.5, humidity: 38, pressure: 1012.3 },
      { timeLabel: '18:00', temperature: 33.0, humidity: 48, pressure: 1012.4 },
      { timeLabel: '20:00', temperature: 29.5, humidity: 58, pressure: 1012.5 },
      { timeLabel: '22:00', temperature: 27.0, humidity: 64, pressure: 1012.4 },
      { timeLabel: '24:00', temperature: 25.1, humidity: 70, pressure: 1012.4 },
    ],
  });

  readonly signature = this.telemetrySignature.asReadonly();
}
