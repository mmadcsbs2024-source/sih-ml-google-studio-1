# SIH26001 --- AI-Based Early Warning and Landslide Risk Monitoring System

## Project Progress, Verified Decisions, Current State & Next-Step Prompts

> **Current project state:** Modules 1--7 are verified complete.\
> **Current active module:** Module 8 --- Environmental Feature
> Extraction.\
> **Module 8 is currently blocked by the local Python/filesystem
> environment and has NOT been legitimately completed.**\
> **Module 9 must NOT be started until Module 8 is verified.**

------------------------------------------------------------------------

# 1. Project Overview

This project is the ML/AI component for:

**"AI-Based Early Warning and Landslide Risk Monitoring System in North
Eastern Region of India"**

SIH Problem ID:

**SIH26001**

The goal is to build a scientifically defensible landslide-risk
prediction pipeline using historical landslide observations and
environmental variables.

The intended ML baseline is:

**RandomForestClassifier**

The system should eventually estimate landslide probability and convert
it into a risk score suitable for backend/GIS integration.

------------------------------------------------------------------------

# 2. Core ML Idea

The final prediction problem is:

> Given environmental conditions at a location and prediction time,
> estimate the probability that a landslide is likely to occur.

Initial environmental predictors:

-   `rainfall_24h`
-   `rainfall_3day`
-   `rainfall_7day`
-   `elevation`
-   `slope`
-   optional `soil_moisture`

Target:

``` text
landslide = 1 → observed landslide
landslide = 0 → carefully constructed background/non-event
```

Latitude and longitude are primarily used for spatial environmental-data
extraction and are NOT automatically included as ML predictors.

------------------------------------------------------------------------

# 3. Critical Scientific Rules

These rules must remain valid throughout the project.

## 3.1 No temporal leakage

Environmental features must only use information available before or at
prediction time.

For an event at time `T`:

``` text
rainfall_24h  = previous 24 hours
rainfall_3day = previous 72 hours
rainfall_7day = previous 168 hours
```

Rainfall occurring after the event must never be included.

Never use future rainfall.

------------------------------------------------------------------------

## 3.2 No fabricated dates

Do not convert uncertain historical dates into fake exact dates.

Examples:

``` text
2019      → DO NOT convert to 2019-01-01

May 2023  → DO NOT convert to 2023-05-01
```

Date categories are preserved:

-   exact date
-   month only
-   year only
-   approximate
-   multiple dates
-   unusable

------------------------------------------------------------------------

## 3.3 Missing is not zero

If rainfall/environmental data is unavailable:

``` text
missing ≠ 0
```

Do not replace missing rainfall with zero.

------------------------------------------------------------------------

## 3.4 Background dates must not be fabricated

Background samples do not have observed landslide event dates.

Do not assign:

-   today's date
-   a random date
-   a positive event's date
-   an arbitrary historical date

A defensible temporal sampling strategy must be established before
background rainfall is generated.

------------------------------------------------------------------------

## 3.5 Raw data must remain untouched

The raw GSI dataset must never be overwritten or modified.

All processing must create separate files under:

``` text
data/processed/
```

------------------------------------------------------------------------

# 4. Raw GSI Dataset

Raw source:

``` text
data/raw/landslide_data.csv
```

Original dataset:

-   approximately 36,071 records
-   11 original columns

Original columns:

``` text
Sl.No.
Slide No
State
District
Slide Name
NH SH Location
Latitude
Longitude
Material Involved
Movement Type
History
```

The raw source has been preserved.

------------------------------------------------------------------------

# 5. Module 1 --- Data Audit

## Status

**PASS**

## Implementation

``` text
src/data/audit.py
```

## Verified findings

-   Raw dataset: 36,071 rows
-   27 states
-   283 districts
-   Latitude range approximately:
    -   minimum: -17.29222222
    -   maximum: 34.758333
-   Longitude range approximately:
    -   minimum: 72.8095
    -   maximum: 96.61719
-   Exact duplicate rows: 0
-   Duplicate `Sl.No.`: 0
-   Duplicate `Slide No`: 559

## Important decision

`Slide No` is not assumed to be a unique physical event identifier.

------------------------------------------------------------------------

# 6. Module 2 --- Cleaning & Validation

## Status

**PASS**

## Implementation

``` text
src/data/cleaning.py
```

## Output

``` text
data/processed/gsi_clean.csv
```

## Verified findings

-   Input rows: 36,071
-   Output rows: 36,071
-   Missing latitude: 0
-   Missing longitude: 1
-   Invalid latitude/longitude: 0
-   Valid coordinate rows: 36,070
-   Missing `History`: 22,397 in the original cleaning diagnostics
-   Missing `Material`: 150
-   Missing `Movement Type`: 117

One suspicious coordinate record was identified:

``` text
Sl.No. = 410
Slide No = ASM/WKA/83C09/2016/34
State = Assam
District = West Karbi Anglong
Latitude = 25.98736
Longitude = missing
```

The cleaned file contains additional quality/status fields while
preserving the original 11 source columns.

The raw dataset remains untouched.

------------------------------------------------------------------------

# 7. Module 3 --- Date Processing

## Status

**PASS**

## Implementation

``` text
src/data/date_processing.py
```

## Output

``` text
data/processed/gsi_with_dates.csv
```

## Verified date categories

From the validated Module 3 run:

``` text
Exact dates:       4611
Multiple dates:     319
Month only:         883
Year only:         7516
Approximate:        175
Unusable:           167
```

The parser is conservative.

Examples:

``` text
17 May 2016
→ exact event date

May 2023
→ month-only range

2019
→ year-only

2nd week of May 2016
→ approximate range
```

Multiple-date records are not arbitrarily reduced to one exact event
date.

Time is separately preserved when explicitly available.

## Verification

``` text
No fabricated dates: PASS
No rows deleted: PASS
History preserved: PASS
MODULE 3 STATUS: PASS
```

------------------------------------------------------------------------

# 8. Module 4 --- Duplicate & Reactivation Analysis

## Status

**PASS**

## Implementation

``` text
src/data/duplicate_analysis.py
```

## Report

``` text
reports/module4_duplicate_analysis.txt
```

## Findings

-   Unique `Sl.No.`: 36,071
-   Duplicate `Sl.No.` rows: 0
-   Unique `Slide No`: 35,716
-   Duplicate `Slide No` groups: 205
-   Maximum records for one `Slide No`: 18
-   Duplicate Slide No groups spanning multiple states: 87
-   Spanning multiple districts: 97
-   Materially different coordinates: 179
-   Different slide names: 120
-   Exact duplicate rows: 0

## Reactivation/recurrence findings

Raw text analysis identified:

``` text
Reactivation examples: 270
Explicit reactivation: 22
Initiation + reactivation: 5
Recurrence: 2
Ambiguous reactivation: 241
```

The analysis distinguishes:

-   repeated records
-   same physical location
-   historical reactivation/recurrence

No final event IDs were incorrectly finalized in this module.

No sampling was performed here.

------------------------------------------------------------------------

# 9. Module 5 --- Positive Landslide Samples

## Status

**PASS**

## Implementation

``` text
src/data/positive_samples.py
```

## Output

``` text
data/processed/positive_landslide_events.csv
```

Positive target:

``` text
landslide = 1
```

## Verified counts

``` text
Total raw records:       36,071
Valid coordinates:       36,070
Usable event-date info:  13,504
Reliable candidates:      4,930
Limited-date candidates:  8,574
Unusable candidates:        170
```

Important distinction:

`13,504` represents records with usable date information broadly.

For event-relative rainfall extraction, the stricter eligible category
is:

``` text
date_status == exact_date
```

which currently contains:

``` text
4,611 records
```

No environmental values were generated in Module 5.

------------------------------------------------------------------------

# 10. Module 6 --- Background Sampling

## Status

**PASS**

## Implementation

``` text
src/data/background_sampling.py
```

## Boundary

An authoritative NER state boundary was obtained and used rather than
relying on a rectangular bounding box.

Boundary files include:

``` text
data/external/boundary/state_NWIC.GeoJSON
data/external/ner_boundary.geojson
```

## Verified principles

-   8/8 NER states represented
-   Background points are inside the NER boundary
-   Positive-coordinate overlap checked
-   Exclusion buffer checked
-   Invalid outside-NER background points rejected

An earlier rectangular bounding-box approach was rejected because it
could generate negatives outside the actual study region.

The final background-sampling method uses the NER boundary.

------------------------------------------------------------------------

# 11. Module 7 --- Environmental Data Sources

## Status

**PASS**

## Configuration

``` text
src/utils/environment_config.py
```

## Documentation

``` text
reports/environmental_data_sources.md
```

## Rainfall source

Primary rainfall source:

**ERA5-Land hourly**

Provider:

**Copernicus Climate Change Service / ECMWF**

Validated properties:

-   hourly temporal resolution
-   approximately 0.1° spatial resolution
-   historical coverage from 1950 to present
-   NER coverage
-   supports 24h aggregation
-   supports 72h aggregation
-   supports 168h aggregation

Official source:

``` text
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
```

## DEM source

Primary terrain source:

**Copernicus DEM**

The DEM provides elevation.

Slope will be derived from the DEM rather than obtained from an
unrelated slope dataset.

## Soil moisture

Soil moisture is optional/deferred.

It must never be fabricated merely to complete the feature list.

## Verification

Module 7 was explicitly verified as:

``` text
MODULE 7 STATUS: PASS
```

The earlier line:

``` text
Required for Module 7: FAIL
```

was confirmed to be a formatting artifact related to optional soil
moisture and is NOT considered a Module 7 failure.

------------------------------------------------------------------------

# 12. Current Module 8 --- Environmental Feature Extraction

## Status

**BLOCKED**

Module 8 implementation exists:

``` text
src/data/environmental_features.py
```

However, Module 8 has NOT been successfully executed and verified.

Expected outputs:

``` text
data/processed/positive_environmental_features.csv
data/processed/background_environmental_features.csv
reports/module8_environmental_features.md
```

These outputs were not legitimately generated during the failed run.

------------------------------------------------------------------------

# 13. Module 8 Blocking Problem

The blocker is currently the local execution environment, not the
intended Module 8 logic.

The Code Agent tested Python writes to:

``` text
E:\sih_ml_model\data\processed\
```

and encountered:

``` text
FileNotFoundError: [Errno 2] No such file or directory
OSError: [Errno 9] Bad file descriptor
```

The workspace directory exists and can be read.

The Windows machine also showed:

``` text
Unauthorized changes blocked
Controlled folder access blocked python.exe
```

This is consistent with Windows Defender Controlled Folder Access
preventing Python from modifying protected folders.

------------------------------------------------------------------------

# 14. Second Module 8 Problem --- Python Environment

The project virtual environment:

``` text
.venv\Scripts\python.exe
```

was found, but the agent reported:

``` text
ModuleNotFoundError: No module named 'pandas'
```

Therefore two prerequisites must be satisfied before Module 8 can be
legitimately rerun:

1.  Python must be allowed to write to the project directory.
2.  The project's Python environment must contain the required
    dependencies.

------------------------------------------------------------------------

# 15. Important Invalid Artifact Warning

During the failed recovery attempt, the agent executed:

``` powershell
Copy-Item 'data\processed\positive_landslide_events.csv' `
          'data\processed\positive_environmental_features.csv'
```

This is NOT a valid environmental-feature output.

The copied file must NOT be treated as Module 8 success.

Before rerunning Module 8, remove that incorrectly copied file if it
still exists.

Also remove only temporary diagnostic files created during the failed
tests.

Do not delete legitimate project datasets.

------------------------------------------------------------------------

# 16. Module 8 Scientific Requirements

Once the environment is fixed, Module 8 must:

## Positive samples

Use exact event dates only for event-relative rainfall.

Required rainfall:

``` text
rainfall_24h
rainfall_3day
rainfall_7day
```

No post-event rainfall.

No future rainfall.

No fabricated dates.

## Terrain

Extract:

``` text
elevation
slope
```

Slope must be derived from DEM and expressed in degrees.

Calculation should account for geographic coordinates appropriately
rather than treating latitude/longitude degrees as ordinary metric
distances.

## Background

Do not fabricate background dates.

Static terrain may be extracted.

Background rainfall should remain deferred unless a scientifically
defensible temporal sampling strategy has been established.

------------------------------------------------------------------------

# 17. Critical Future-Date Issue

A previous verification reported:

``` text
Maximum exact event date: 2028-08-16
```

Current project date at the time of verification:

``` text
2026-09-11
```

Therefore any exact event date after the current date must be
investigated.

Possible explanations:

-   genuine source-data issue
-   parsing issue
-   malformed `History`
-   another data problem

Module 8 must NOT silently change or delete such records.

Future-dated records should receive an explicit status such as:

``` text
future_event_date
```

and must not receive temporal rainfall extraction.

------------------------------------------------------------------------

# 18. Module 9 --- Final ML Dataset

## Status

**NOT STARTED**

Module 9 must wait until Module 8 is legitimately verified.

Expected final ML features:

``` text
rainfall_24h
rainfall_3day
rainfall_7day
elevation
slope
```

Optional:

``` text
soil_moisture
```

Target:

``` text
landslide
```

Do not automatically include:

``` text
latitude
longitude
Sl.No.
Slide No
State
District
Slide Name
NH SH Location
History
event_date
```

Metadata/identifiers should remain available for traceability but should
not automatically become predictors.

------------------------------------------------------------------------

# 19. Modules Not Yet Started

## Module 10 --- Train/Validation/Test Split

Not started.

Will be responsible for creating leakage-safe training/validation/test
data.

## Module 11 --- Random Forest

Not started.

Baseline model:

``` text
RandomForestClassifier
```

No blind:

-   SMOTE
-   PCA
-   scaling
-   GridSearchCV

unless later justified by actual validation evidence.

## Module 12 --- Evaluation & Risk Score

Not started.

Required evaluation:

-   confusion matrix
-   precision
-   recall
-   F1
-   ROC-AUC

Recall is particularly important for an early-warning system.

Later risk score:

``` text
risk_score = probability * 100
```

Risk thresholds will follow the project's defined risk-category
specification.

------------------------------------------------------------------------

# 20. Complete Pipeline

``` text
GSI Raw Inventory
       ↓
Module 1 — Audit                         ✅
       ↓
Module 2 — Cleaning & Validation         ✅
       ↓
Module 3 — Date Processing               ✅
       ↓
Module 4 — Duplicate Analysis            ✅
       ↓
Module 5 — Positive Samples              ✅
       ↓
Module 6 — Background Samples            ✅
       ↓
Module 7 — Environmental Sources         ✅
       ↓
Module 8 — Environmental Extraction      🔴 CURRENT / BLOCKED
       ↓
Module 9 — Final ML Dataset              ⏳
       ↓
Module 10 — Train/Validation/Test        ⏳
       ↓
Module 11 — Random Forest                ⏳
       ↓
Module 12 — Evaluation + Risk Score      ⏳
       ↓
Backend / GIS / Early Warning Integration
```

------------------------------------------------------------------------

# 21. CURRENT ACTION PLAN

Do NOT start Module 9.

First repair the local environment.

## Step A --- Windows Controlled Folder Access

In Windows:

``` text
Windows Security
→ Virus & threat protection
→ Ransomware protection
→ Manage ransomware protection
→ Allow an app through Controlled folder access
→ Add an allowed app
→ Browse
```

Add the exact Python executable used by the project:

``` text
E:\sih_ml_model\.venv\Scripts\python.exe
```

If necessary, verify with:

``` powershell
where python
```

or:

``` powershell
Get-Command python
```

Prefer allowing the project's `.venv` Python rather than disabling all
ransomware protection.

------------------------------------------------------------------------

# 22. Step B --- Restart VS Code

After changing Controlled Folder Access permissions:

1.  Close VS Code.
2.  Reopen VS Code.
3.  Reopen the project:

``` text
E:\sih_ml_model
```

4.  Open a fresh terminal.

------------------------------------------------------------------------

# 23. Step C --- Verify Python Environment

Run:

``` powershell
.\.venv\Scripts\python.exe --version
```

Then:

``` powershell
.\.venv\Scripts\python.exe -c "import pandas; print('pandas PASS')"
```

Also:

``` powershell
.\.venv\Scripts\python.exe -c "import numpy; print('numpy PASS')"
```

and:

``` powershell
.\.venv\Scripts\python.exe -c "import sklearn; print('sklearn PASS')"
```

If dependencies are missing, inspect:

``` text
requirements.txt
```

and install the project's declared dependencies.

Do not randomly install unrelated packages.

------------------------------------------------------------------------

# 24. Step D --- Verify Python Write Access

From:

``` text
E:\sih_ml_model
```

run:

``` powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; p=Path('data/processed/module8_write_test.tmp'); p.write_text('ok', encoding='utf-8'); print('WRITE PASS', p.exists()); p.unlink()"
```

Expected:

``` text
WRITE PASS True
```

If this fails:

**STOP.**

Do not generate fake Module 8 outputs.

------------------------------------------------------------------------

# 25. Step E --- Rerun Module 8

Only after Python dependencies and write access pass:

``` powershell
.\.venv\Scripts\python.exe src\data\environmental_features.py
```

Then verify the actual outputs.

------------------------------------------------------------------------

# 26. MODULE 8 RERUN PROMPT

Copy this into the Code Agent after the environment is fixed:

``` text
MODULE 8 — FINAL RERUN AFTER ENVIRONMENT FIX

Module 8 implementation already exists.

First verify:

1. .venv Python works
2. pandas is available
3. numpy is available
4. sklearn is available if required
5. Python can write to data/processed

Do not proceed if any prerequisite fails.

IMPORTANT:
A previous attempt incorrectly copied positive_landslide_events.csv
to positive_environmental_features.csv.

That copied file is NOT a valid Module 8 result.

Remove only that invalid copied artifact if it still exists.

Do not delete legitimate project datasets.

==================================================
RUN
==================================================

Run:

.venv\Scripts\python.exe src\data\environmental_features.py

Do not fabricate environmental values.

Do not fabricate dates.

Do not fabricate background dates.

==================================================
VERIFY
==================================================

Verify these are genuinely generated by environmental_features.py:

data/processed/positive_environmental_features.csv

data/processed/background_environmental_features.csv

reports/module8_environmental_features.md

Check their actual contents.

Required environmental columns:

rainfall_24h
rainfall_3day
rainfall_7day
elevation
slope

==================================================
FUTURE DATE
==================================================

Investigate the previously detected:

2028-08-16

Do not silently change it.

Future-dated records must not receive rainfall.

==================================================
LEAKAGE
==================================================

Verify:

Post-event rainfall = 0
Future rainfall = 0
Fabricated dates = 0
Fabricated background dates = 0

==================================================
ROW INTEGRITY
==================================================

Report:

Positive input rows:
Positive output rows:

Background input rows:
Background output rows:

Unexpected row loss:

==================================================
FINAL
==================================================

Print:

========================================
MODULE 8 FINAL VERIFICATION
========================================

Python environment: PASS/FAIL
Python write access: PASS/FAIL

Positive environmental output: PASS/FAIL
Background environmental output: PASS/FAIL
Module 8 report: PASS/FAIL

Positive rows: ...
Background rows: ...

Rainfall 24h available: ...
Rainfall 3day available: ...
Rainfall 7day available: ...

Elevation available: ...
Slope available: ...

Future-dated records: ...
Future records receiving rainfall: ...

Post-event rainfall: ...
Future rainfall: ...
Fabricated dates: ...
Fabricated background dates: ...

========================================
MODULE 8 STATUS
========================================

PASS / PARTIAL / BLOCKED

STOP.

DO NOT START MODULE 9.
```

------------------------------------------------------------------------

# 27. Module 9 Prompt --- Use Only After Module 8 PASS

``` text
MODULE 9 — FINAL ML DATASET CONSTRUCTION

Module 8 has been verified successfully.

Create ONLY the final ML-ready dataset.

DO NOT:
- train a model
- split the data
- tune Random Forest
- use SMOTE
- use PCA
- scale features unnecessarily
- evaluate the model

==================================================
INPUTS
==================================================

Use:

data/processed/positive_environmental_features.csv
data/processed/background_environmental_features.csv

Inspect the actual schemas first.

==================================================
TARGET
==================================================

Create/verify:

landslide

1 = observed landslide
0 = background/non-event

Verify both classes exist.

==================================================
FEATURES
==================================================

Primary features:

rainfall_24h
rainfall_3day
rainfall_7day
elevation
slope

Optional:

soil_moisture

Do NOT automatically use latitude/longitude or identifiers as ML
predictors.

==================================================
MISSING VALUES
==================================================

Report missing values feature-by-feature.

Never convert missing rainfall to zero.

Do not blindly impute.

==================================================
INTEGRITY
==================================================

Verify:

- positive/negative labels
- row preservation
- duplicate records
- numeric datatypes
- finite values
- rainfall >= 0
- slope 0–90 degrees
- elevation plausibility

==================================================
LEAKAGE
==================================================

Verify:

- no post-event rainfall
- no future rainfall
- no fabricated dates
- no fabricated background dates

If unresolved leakage exists:

BLOCK Module 9.

==================================================
OUTPUT
==================================================

Create:

data/processed/final_ml_dataset.csv

Create:

reports/module9_ml_dataset.md

Do not create train/validation/test files.

==================================================
TERMINAL
==================================================

Print complete verification.

End with:

MODULE 9 STATUS: PASS / PARTIAL / BLOCKED

STOP.
```

------------------------------------------------------------------------

# 28. Module-by-Module Completion Rule

A module is considered complete only when:

``` text
Implementation exists
        AND
Expected output exists
        AND
Verification passes
        AND
No known blocker remains
```

Do not mark a module PASS merely because its script exists.

Do not use filenames alone as evidence.

------------------------------------------------------------------------

# 29. Current Checkpoint

As of the latest verified workspace investigation:

``` text
Completed:
7 / 12 modules

Current:
Module 8

Module 8:
Implementation exists
Execution blocked
Outputs not legitimately generated

Next immediate action:
Fix Windows/Python write environment

After that:
Rerun and verify Module 8

Only then:
Start Module 9
```

------------------------------------------------------------------------

# 30. Final Principle

The project should prioritize **scientific validity over completing
files quickly**.

It is better to report:

``` text
PARTIAL
```

or:

``` text
BLOCKED
```

than to generate:

-   fabricated rainfall
-   fabricated dates
-   fake background dates
-   post-event features
-   copied CSVs pretending to be environmental features
-   invalid negative samples

The final ML model is only as trustworthy as the data-generation
pipeline before it.

------------------------------------------------------------------------

## END OF PROJECT STATUS DOCUMENT
