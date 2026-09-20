export interface LandslideRecord {
  id: string;
  slideNo: string;
  state: string;
  district: string;
  name: string;
  location: string;
  lat: number;
  lon: number;
  material: string;
  movement: string;
  history: string;
  date: string;
  dateStatus: 'exact_date' | 'month_only' | 'year_only' | 'approximate' | 'multiple_dates' | 'unusable';
  quality: 'reliable' | 'limited_date' | 'unusable';
  isLandslide: 1;
}

export interface BackgroundRecord {
  lat: number;
  lon: number;
  isLandslide: 0;
}

export interface RiskAssessmentInput {
  state: string;
  district: string;
  lat: number;
  lon: number;
  elevation: number; // in meters (Copernicus DEM)
  slope: number; // in degrees (Derived from DEM)
  rainfall24h: number; // in mm (Copernicus ERA5-Land)
  rainfall3day: number; // in mm (Copernicus ERA5-Land previous 72h)
  rainfall7day: number; // in mm (Copernicus ERA5-Land previous 168h)
  material: string; // Debris, Rock, Earth, Mixed
  movementType: string; // Slide, Fall, Flow, Topple
  soilMoisture?: number; // volumetric m3/m3 (Optional/Deferred)
  predictionDate: string;
  isExactDate: boolean;
}

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';

export interface FeatureContribution {
  feature: string;
  value: number | string;
  weight: number; // relative contribution percentage
  impact: 'positive' | 'negative' | 'neutral';
  explanation: string;
}

export interface RiskAssessmentResult {
  probability: number; // 0.0 to 1.0
  riskScore: number; // 0 to 100
  riskLevel: RiskLevel;
  alertStatus: string;
  scientificViolations: string[];
  contributions: FeatureContribution[];
  recommendation: string;
}

export interface ModuleAuditInfo {
  moduleNumber: number;
  name: string;
  status: 'PASS' | 'BLOCKED' | 'PENDING';
  implementationFile: string;
  primaryOutputs: string[];
  findings: { [key: string]: string | number };
  scientificPrinciples: string[];
  notes: string;
}
