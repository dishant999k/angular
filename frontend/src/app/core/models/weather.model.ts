/**
 * Weather parameter models verified strictly from dishant999k/angular:
 * skyguard/config.py: Config.PARAMETERS = ["temp", "pres", "rhum"]
 */

export type WeatherParameter = 'temp' | 'pres' | 'rhum';

export interface ParameterMetadata {
  key: WeatherParameter;
  label: string;
  unit: string;
  description: string;
}

export const VERIFIED_PARAMETERS: Record<WeatherParameter, ParameterMetadata> = {
  temp: {
    key: 'temp',
    label: 'Air Temperature',
    unit: '°C',
    description: 'Ambient air temperature at 2m',
  },
  pres: {
    key: 'pres',
    label: 'Barometric Pressure',
    unit: 'hPa',
    description: 'Surface atmospheric pressure',
  },
  rhum: {
    key: 'rhum',
    label: 'Relative Humidity',
    unit: '%',
    description: 'Relative humidity percentage',
  },
};
