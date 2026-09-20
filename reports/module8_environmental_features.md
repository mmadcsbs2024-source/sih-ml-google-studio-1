# Module 8 — Environmental Feature Extraction

## Status

BLOCKED

## Why this is blocked

Module 7 configuration in [src/utils/environment_config.py](../src/utils/environment_config.py) shows all environmental sources disabled:

- rainfall: enabled = False
- elevation: enabled = False
- slope: enabled = False
- soil_moisture: enabled = False

The expected Module 7 documentation file `reports/environmental_data_sources.md` is not present in the workspace, so there is no verified rainfall/DEM source to extract from.

Per the instructions, Module 8 must not fabricate rainfall, elevation, slope, or soil-moisture values. Because no validated environmental source is configured, the only safe Module 8 outcome is to preserve all environmental features as missing and report the blocker.

## Verified input counts from the existing processed datasets

- Positive records: 13,674
- Background records: 8,364
- Valid positive coordinates: 13,674
- Exact-date positive records: 4,611
- Month-only positive records: 883
- Year-only positive records: 7,516
- Approximate-date positive records: 175
- Multiple-date positive records: 319
- Unusable positive records: 167

## Current evidence

### Module 7 configuration

See [src/utils/environment_config.py](../src/utils/environment_config.py).

### Existing outputs used as inputs

- [data/processed/positive_landslide_events.csv](../data/processed/positive_landslide_events.csv)
- [data/processed/background_samples.csv](../data/processed/background_samples.csv)
- [data/external/boundary/ner_boundary.geojson](../data/external/boundary/ner_boundary.geojson)

## Module 8 output policy in this workspace

Because the configured source list is disabled, the correct Module 8 behavior is:

- build the unified sample table from the verified positive and background inputs
- keep all environmental features missing
- record the reason in the report
- avoid any synthetic or estimated values
- report the source/configuration blocker explicitly

## Leakage verification

- Post-event rainfall included: 0
- Future rainfall observations used: 0
- Fabricated event dates: 0

## Feature availability statistics

- rainfall_24h: unavailable (source disabled)
- rainfall_3day: unavailable (source disabled)
- rainfall_7day: unavailable (source disabled)
- elevation: unavailable (source disabled)
- slope_degrees: unavailable (source disabled)
- soil_moisture: unavailable (source disabled)

## Recommended next step

To continue with full Module 8 extraction, the workspace must contain a valid Module 7 source configuration and a verified environmental dataset source. Once that is present, the module can be completed without fabricating data.
