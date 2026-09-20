import { ModuleAuditInfo } from '../types';

export const MODULES_AUDIT_DATA: ModuleAuditInfo[] = [
  {
    moduleNumber: 1,
    name: 'Data Audit',
    status: 'PASS',
    implementationFile: 'src/data/audit.py',
    primaryOutputs: ['reports/module1_audit_report.txt'],
    findings: {
      'Raw Records': 36071,
      'Total States': 27,
      'Total Districts': 283,
      'Latitude Range': '-17.29° to 34.76°',
      'Longitude Range': '72.81° to 96.62°',
      'Exact Duplicate Rows': 0,
      'Duplicate Sl.No.': 0,
      'Duplicate Slide No': 559
    },
    scientificPrinciples: [
      'Slide No is not assumed to be a unique physical event identifier.',
      'Raw GSI source dataset preserved immutably with original 11 columns.',
      'Complete cataloging of spatial bounding envelope across all Indian territories.'
    ],
    notes: 'The audit confirmed 36,071 original entries across India with a concentrated mountain corridor in the North Eastern Region.'
  },
  {
    moduleNumber: 2,
    name: 'Cleaning & Coordinate Validation',
    status: 'PASS',
    implementationFile: 'src/data/cleaning.py',
    primaryOutputs: ['data/processed/gsi_clean.csv'],
    findings: {
      'Input Records': 36071,
      'Output Records': 36071,
      'Valid Coordinates': 36070,
      'Missing Longitude': 1,
      'Missing History Text': 22397,
      'Missing Material': 150,
      'Missing Movement Type': 117
    },
    scientificPrinciples: [
      'Zero rows deleted: all rows preserved with explicit validity flags.',
      'Sl.No. 410 flagged (Assam, West Karbi Anglong: lat 25.98736, lon missing).',
      'Raw data directory (data/raw/) remains write-protected.'
    ],
    notes: 'Added quality flags (latitude_valid, longitude_valid, coordinate_status) without destroying original schema.'
  },
  {
    moduleNumber: 3,
    name: 'Conservative Date Processing',
    status: 'PASS',
    implementationFile: 'src/data/date_processing.py',
    primaryOutputs: ['data/processed/gsi_with_dates.csv'],
    findings: {
      'Exact Event Dates': 4611,
      'Year Only (e.g. 2019)': 7516,
      'Month Only (e.g. May 2023)': 883,
      'Multiple Dates': 319,
      'Approximate Dates': 175,
      'Unusable Text': 167
    },
    scientificPrinciples: [
      'STRICT: Never convert year-only (e.g. "2019") into "2019-01-01".',
      'STRICT: Never convert month-only (e.g. "May 2023") into "2023-05-01".',
      'Preserve multi-date event sequences separately without arbitrary collapsing.'
    ],
    notes: 'Conservative parsing ensures only scientifically verified timestamps are paired with high-resolution hourly rainfall reanalyses.'
  },
  {
    moduleNumber: 4,
    name: 'Duplicate & Reactivation Analysis',
    status: 'PASS',
    implementationFile: 'src/data/duplicate_analysis.py',
    primaryOutputs: ['reports/module4_duplicate_analysis.txt'],
    findings: {
      'Unique Sl.No.': 36071,
      'Unique Slide No': 35716,
      'Duplicate Slide No Groups': 205,
      'Groups Across States': 87,
      'Different Coordinates': 179,
      'Reactivation Mentions': 270,
      'Explicit Reactivations': 22
    },
    scientificPrinciples: [
      'Distinguish repeated records from physical landslide reactivations.',
      'Spatial buffering differentiates re-mobilized scars from administrative entry collisions.',
      'No premature event clustering applied before feature extraction.'
    ],
    notes: 'Identified chronic recurrence hotspots along National and State Highways in Assam, Meghalaya, and Sikkim.'
  },
  {
    moduleNumber: 5,
    name: 'Positive Landslide Samples',
    status: 'PASS',
    implementationFile: 'src/data/positive_samples.py',
    primaryOutputs: ['data/processed/positive_landslide_events.csv'],
    findings: {
      'Total Positive Events (y=1)': 36071,
      'Valid Coordinates': 36070,
      'Usable Date Info': 13504,
      'Exact Date Eligible': 4611,
      'NER Positive Events': 3057
    },
    scientificPrinciples: [
      'Target label landslide = 1 strictly verified.',
      'Only exact_date records are eligible for hourly event-relative rainfall windows.',
      'All positive events retain full provenance tracking to raw GSI catalog.'
    ],
    notes: 'Provides the high-confidence positive ground truth necessary for supervised Machine Learning classification.'
  },
  {
    moduleNumber: 6,
    name: 'Authoritative Boundary & Background Sampling',
    status: 'PASS',
    implementationFile: 'src/data/background_sampling.py',
    primaryOutputs: ['data/processed/background_samples.csv'],
    findings: {
      'Positive Samples (y=1)': 4182,
      'Negative Samples (y=0)': 4182,
      'NER States Covered': '8 of 8 States',
      'Boundary Source': 'Authoritative GeoJSON (NER Boundary)',
      'Exclusion Buffer': 'Applied around positive scars'
    },
    scientificPrinciples: [
      'CRITICAL: Rectangular bounding box rejected — negatives must be inside true NER boundary.',
      'STRICT: Background points must never have fabricated event dates assigned.',
      'Exclusion buffer prevents negative points from falling on active landslide scarps.'
    ],
    notes: 'Balanced 1:1 ratio within the complex terrain of Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura.'
  },
  {
    moduleNumber: 7,
    name: 'Environmental Data Sources Configuration',
    status: 'PASS',
    implementationFile: 'src/utils/environment_config.py',
    primaryOutputs: ['reports/environmental_data_sources.md'],
    findings: {
      'Rainfall Source': 'Copernicus ERA5-Land hourly (0.1° / ~10km)',
      'Elevation Source': 'Copernicus DEM GLO-30 (30m resolution)',
      'Slope Source': 'Derived gradient from DEM',
      'Alternative Rainfall': 'NASA GPM IMERG (0.1° / 30-min)',
      'Soil Moisture': 'Optional / Deferred (Not fabricated)'
    },
    scientificPrinciples: [
      'Copernicus Climate Data Store (CDS API) selected for 1950-present hourly reanalysis.',
      'Elevation and Slope derived cohesively from identical digital elevation models.',
      'STRICT: Missing data is represented as NaN, NEVER imputed as 0 mm.'
    ],
    notes: 'Module 7 fully validated and locked. Provides the authoritative data access contracts for downstream modeling.'
  },
  {
    moduleNumber: 8,
    name: 'Environmental Feature Extraction Pipeline',
    status: 'PASS',
    implementationFile: 'src/data/environmental_features.py',
    primaryOutputs: [
      'data/processed/positive_environmental_features.csv',
      'data/processed/background_environmental_features.csv',
      'reports/module8_environmental_features.md'
    ],
    findings: {
      'Temporal Windows': '24h, 72h (3-day), 168h (7-day)',
      'Leakage Guard': 'Strictly before or at event timestamp T',
      'Terrain Features': 'Elevation (m), Slope angle (°), Aspect',
      'ML Target Baseline': 'RandomForestClassifier (SIH26001 baseline)'
    },
    scientificPrinciples: [
      'ZERO TEMPORAL LEAKAGE: strictly previous 24h, 72h, and 168h precipitation.',
      'Post-event rainfall strictly excluded from model feature vector.',
      'Exact temporal matching ensures robust generalized inference.'
    ],
    notes: 'Migrated and fully operational in Node.js runtime with built-in real-time geotechnical RF probability engine.'
  }
];

export const NER_STATES_INFO = [
  { name: 'Assam', capital: 'Dispur', landslides: 238, keyDistricts: ['Hailakandi', 'Dima Hasao', 'Karbi Anglong', 'Kamrup', 'Cachar'] },
  { name: 'Arunachal Pradesh', capital: 'Itanagar', landslides: 144, keyDistricts: ['Papum Pare', 'West Kameng', 'Lower Subansiri', 'Tawang'] },
  { name: 'Meghalaya', capital: 'Shillong', landslides: 366, keyDistricts: ['East Khasi Hills', 'West Khasi Hills', 'Ri-Bhoi', 'Jaintia Hills'] },
  { name: 'Manipur', capital: 'Imphal', landslides: 272, keyDistricts: ['Tamenglong', 'Churachandpur', 'Senapati', 'Ukhrul'] },
  { name: 'Mizoram', capital: 'Aizawl', landslides: 1374, keyDistricts: ['Aizawl', 'Lunglei', 'Champhai', 'Kolasib', 'Serchhip'] },
  { name: 'Nagaland', capital: 'Kohima', landslides: 553, keyDistricts: ['Kohima', 'Mokokchung', 'Wokha', 'Phek', 'Dimapur'] },
  { name: 'Sikkim', capital: 'Gangtok', landslides: 62, keyDistricts: ['East Sikkim', 'North Sikkim', 'South Sikkim', 'West Sikkim'] },
  { name: 'Tripura', capital: 'Agartala', landslides: 48, keyDistricts: ['Dhalai', 'North Tripura', 'South Tripura', 'West Tripura'] }
];
