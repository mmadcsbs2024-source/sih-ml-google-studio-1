# Environmental Data Sources

## 1. Rainfall

### Selected source
ERA5-Land hourly data

### Provider
Copernicus Climate Change Service / ECMWF

### Official URL
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

### Spatial resolution
Approximately 0.1 degree

### Temporal resolution
Hourly

### Historical coverage
1950-present

### Geographic coverage
Global land

### Why selected
ERA5-Land is the authoritative baseline rainfall source for this project because it provides long historical coverage, hourly temporal resolution, global land coverage, and the precipitation data needed for the required antecedent rainfall windows. This aligns cleanly with the project requirement to calculate rainfall_24h, rainfall_3day, and rainfall_7day from historical observations without fabricating daily totals.

### Rainfall features
- rainfall_24h
- rainfall_3day
- rainfall_7day

### Temporal convention
For each positive sample with a reliable exact event date D:

- rainfall_24h = precipitation accumulated during the 24 hours immediately preceding D
- rainfall_3day = precipitation accumulated during the 72 hours immediately preceding D
- rainfall_7day = precipitation accumulated during the 168 hours immediately preceding D

No rainfall after D may be used. If event time is unavailable, a documented date-level convention will be applied and must not include post-event rainfall.

### Leakage prevention
The project must forbid post-event rainfall, future observations, and fabricated event dates. Only exact event dates are eligible for temporal rainfall extraction. Non-exact dates will remain missing and must be reported as such.

### Alternative source
NASA GPM IMERG is documented as a viable secondary/validation source for future comparison, but it is not the selected baseline source for this project. ERA5-Land remains the primary rainfall source.

## 2. DEM

### Selected source
Copernicus DEM GLO-30

### Provider
Copernicus Data Space Ecosystem

### Official URL
https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM

### Spatial resolution
30 m

### Geographic coverage
Global land

### Format / characteristics
Copernicus DEM GLO-30 is a global DEM suitable for elevation extraction and later slope derivation. The pipeline must use the selected DEM rather than inventing elevation values.

### Access status
The source is validated as the intended DEM source. Whether it is practically downloadable in the current environment depends on Copernicus access/credential requirements. If GLO-30 is not practically accessible, the documented fallback is Copernicus DEM GLO-90.

## 3. Slope

Slope is not a separate source dataset. It is derived from the selected DEM using a terrain-gradient method and reported in degrees.

DEM
→ terrain gradient
→ slope_degrees

## 4. Soil Moisture

Soil moisture is optional and deferred. It must not be fabricated and must not block the baseline pipeline.

Status: OPTIONAL / DEFERRED

## 5. Spatial alignment

Future Module 8 extraction will map latitude/longitude to the selected rainfall grid and DEM using the documented source spatial resolution. The implementation must use one consistent spatial extraction method per source, rather than mixing arbitrary methods silently.

## 6. Temporal alignment

Only samples with a reliable exact_date are rainfall-eligible. Records with month_only, year_only, approximate_date, or multiple_dates are not eligible for temporal rainfall extraction and must remain missing with an explanatory status.

## 7. Leakage risks

The project must explicitly guard against:

- post-event rainfall
- future rainfall observations
- fabricated event dates
- fabricated rainfall, DEM, or slope values

## 8. Access limitations

This document distinguishes between:

- SOURCE VALIDATED: the source is the correct project-authoritative choice
- DATA ACTUALLY DOWNLOADED: only if the current environment successfully accesses and retrieves the data

The documentation is valid even if automated download is not currently possible in this environment. In that case, the access limitation must be clearly reported.

## 9. Data availability matrix

| Feature | Source | Spatial Resolution | Temporal Resolution | Coverage | Status |
| --- | --- | --- | --- | --- | --- |
| rainfall_24h | ERA5-Land | approximately 0.1 degree | hourly | 1950-present | READY |
| rainfall_3day | ERA5-Land | approximately 0.1 degree | hourly | 1950-present | READY |
| rainfall_7day | ERA5-Land | approximately 0.1 degree | hourly | 1950-present | READY |
| elevation | Copernicus DEM GLO-30 | 30 m | static | global | READY |
| slope | DEM-derived | 30 m input | static | global | READY |
| soil_moisture | — | — | — | — | OPTIONAL / DEFERRED |

## 10. Known limitations

- ERA5-Land and the Copernicus DEM are source-level validated choices, but actual retrieval may still require credentials or specific Copernicus access.
- Module 8 must not include rainfall or terrain values that are not verified from the selected sources.
- Background samples do not have validated event dates; rainfall extraction for background samples is therefore deferred until a defensible temporal sampling design is defined.
