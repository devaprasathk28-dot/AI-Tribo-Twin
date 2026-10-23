# AI-TriboTwin

> **Digital Twin Platform & Scientific Machine Learning Workspace for Tribological Systems**  
> *Empirical experiment lifecycle management, transparent machine-learning inference, rigorous scientific gating, and publication-grade engineering reporting.*

<p align="center">
  <a href="#-backend-tests"><img src="https://img.shields.io/badge/backend%20tests-132%20passed-00C853?style=flat-square&logo=pytest&logoColor=white" alt="Backend Tests"></a>
  <a href="#-frontend-tests"><img src="https://img.shields.io/badge/frontend%20tests-52%20passed-00C853?style=flat-square&logo=vitest&logoColor=white" alt="Frontend Tests"></a>
  <a href="#-typecheck--lint"><img src="https://img.shields.io/badge/typescript-strict%20clean-blue?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript Strict"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/next.js-15.5.9-black?style=flat-square&logo=next.js&logoColor=white" alt="Next.js"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/fastapi-0.143.0-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/postgresql-16%2B-336791?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <a href="#-scientific-integrity-framework"><img src="https://img.shields.io/badge/composite%20targets-BLOCKED%20%2F%20NO__GO-d32f2f?style=flat-square" alt="Target Readiness Gate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License: MIT"></a>
</p>

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. The Triboinformatics Challenge](#2-the-triboinformatics-challenge)
- [3. System Architecture](#3-system-architecture)
- [4. Core Platform Modules](#4-core-platform-modules)
  - [4.1 Research Workspace & Telemetry (`/`)](#41-research-workspace--telemetry-)
  - [4.2 Model Experience & Prediction Transparency (`/models`)](#42-model-experience--prediction-transparency-models)
  - [4.3 Experiment Planning & In Silico Screening (`/planning`)](#43-experiment-planning--in-silico-screening-planning)
  - [4.4 Empirical Experiment Registry (`/experiments`)](#44-empirical-experiment-registry-experiments)
  - [4.5 Tribological Analytics & Statistical Distributions (`/analytics`)](#45-tribological-analytics--statistical-distributions-analytics)
  - [4.6 Data Ingestion & Provenance Auditing (`/imports`)](#46-data-ingestion--provenance-auditing-imports)
  - [4.7 Engineering Reports & Export Hub (`/reports`)](#47-engineering-reports--export-hub-reports)
- [5. Scientific Integrity & Gating Framework](#5-scientific-integrity--gating-framework)
  - [5.1 The 3-Tier Model Hierarchy](#51-the-3-tier-model-hierarchy)
  - [5.2 Rationale for Blocking Composite Targets](#52-rationale-for-blocking-composite-targets)
  - [5.3 Strict Anti-Hallucination & Zero-Imputation Policy](#53-strict-anti-hallucination--zero-imputation-policy)
- [6. Technology Stack](#6-technology-stack)
- [7. Local Development & Quickstart](#7-local-development--quickstart)
  - [7.1 Prerequisites](#71-prerequisites)
  - [7.2 Repository Setup](#72-repository-setup)
  - [7.3 Backend Execution (FastAPI)](#73-backend-execution-fastapi)
  - [7.4 Frontend Execution (Next.js)](#74-frontend-execution-nextjs)
- [8. Automated Verification & Quality Assurance](#8-automated-verification--quality-assurance)
  - [8.1 Backend Pytest Suite (132 tests)](#81-backend-pytest-suite-132-tests)
  - [8.2 Frontend Vitest & Verification (52 tests)](#82-frontend-vitest--verification-52-tests)
  - [8.3 Cryptographic Scientific Data Hash](#83-cryptographic-scientific-data-hash)
- [9. REST API Specification](#9-rest-api-specification)
- [10. Data Architecture & Database Schema](#10-data-architecture--database-schema)
- [11. Repository Layout](#11-repository-layout)
- [12. Citations & Attribution](#12-citations--attribution)
- [13. License & Maintenance](#13-license--maintenance)

---

## 1. Executive Summary

**AI-TriboTwin** is an open-source, production-ready engineering workspace and digital twin platform specifically engineered for experimental tribology, surface engineering, and composite materials design. It bridges the gap between laboratory tribometer characterization (pin-on-disc, block-on-ring, tow-on-tool) and computational surrogate modeling.

Unlike generic machine-learning wrappers that hallucinate predictions across uncalibrated regimes, AI-TriboTwin enforces **scientific integrity as executable code**:
* **Physical Domain Confinement**: Models reject or flag unphysical operating conditions (e.g., negative contact areas, out-of-boundary normal loads, uncalibrated velocity regimes).
* **Strict Separation of Planned vs. Measured Data**: In silico screening candidates and prospective parameter sweeps are physically separated from verified empirical laboratory observations in databases, statistical distributions, and reporting documents.
* **Rigorous Target Gating**: Predictive inference on complex composite formulations is hard-blocked until underlying experimental ambiguities (specimen run mappings and wear metric unit harmonization) are definitively resolved by original investigators.
* **Deterministic Provenance Chains**: Every record, import batch, model artifact, and generated PDF report is tied to cryptographic SHA-256 fingerprints, preserving a complete audit trail from physical test bench to final report.

---

## 2. The Triboinformatics Challenge

Tribological systems—governed by friction, lubrication, and multi-scale wear mechanisms—present notorious failure modes for conventional machine learning:

1. **Severe Sensitivity to Contact Geometry & Normal Load**: Non-linear transitions in real contact area, asperities deforming under Hertzian vs. plastic regimes, and sliding speeds induce thermal transitions that invalidate unconstrained model extrapolations.
2. **Heterogeneous & Incompatible Wear Metrics**: Wear is reported variously as volumetric wear loss ($\text{mm}^3$), linear wear depth ($\mu\text{m}$), or specific wear rate ($\text{mm}^3/\text{N}\cdot\text{m}$). Silently pooling or converting these metrics without counterface topography and test duration introduces catastrophic physical errors.
3. **Pervasive Data Leakage**: Slicing time-series or multi-step load ramps from the same physical coupon into both training and validation splits yields artificially high validation scores ($R^2 > 0.98$) that fail completely on unseen material batches.
4. **Data Scarcity & High Experimental Cost**: High-temperature and vacuum tribometry runs are expensive and time-intensive, resulting in sparse experimental datasets where standard mean/median imputation corrupts correlation structures.

**AI-TriboTwin solves these problems** by embedding tribological boundary checking, group-based cross-validation splitting, unit-segregated analytics, and scientific gatekeeping directly into the software architecture.

---

## 3. System Architecture

AI-TriboTwin is engineered with a modular, decoupling-first architecture consisting of a Next.js 15 presentation layer, an asynchronous FastAPI service layer, a relational storage engine, and a verified ML artifact registry:

```
+----------------------------------------------------------------------------------------------------+
|                                    AI-TriboTwin Web Application                                    |
|                      Next.js 15 (App Router) · React 19 · TypeScript (Strict)                      |
|                  Responsive Shell Layout · Tailwind CSS · Semantic Token Palette                   |
+----------------------------------------------------------------------------------------------------+
       |                     |                      |                     |                   |
       v                     v                      v                     v                   v
 [/] Overview         [/models] Models      [/experiments]       [/analytics]        [/reports]
 Dashboard & Status   Transparency Hub      Registry & History   Visualizations      Compliance Hub
       |                     |                      |                     |                   |
+----------------------------------------------------------------------------------------------------+
|                                     FastAPI REST Service (v1)                                      |
|                 Asynchronous Routing · Pydantic v2 Validation · ReportLab 5.1 Engine               |
+----------------------------------------------------------------------------------------------------+
       |                     |                      |                                 |
       v                     v                      v                                 v
+--------------+     +---------------+     +--------------------+           +--------------------+
| Model Engine |     | Scientific    |     | Relational Storage |           | Engineering        |
| & Estimators |     | Gatekeeper    |     | PostgreSQL/SQLite  |           | Reporting Engine   |
| • Cambridge  |     | • Composite   |     | • experiments      |           | • ReportLab Canvas |
|   Tow Model  |     |   COF: BLOCKED|     | • file_imports     |           | • Running Headers  |
| • Synthetic  |     | • Wear:BLOCKED|     | • check constraints|           | • Page X of Y      |
|   Fixture    |     | • SWR: BLOCKED|     | • immutable blobs  |           | • RFC 4180 CSVs    |
+--------------+     +---------------+     +--------------------+           +--------------------+
       |                     |                      |                                 |
       +---------------------+----------------------+---------------------------------+
                                            |
                                            v
                         +--------------------------------------+
                         | Scientific Data & Artifact Store     |
                         | • Read-only CSV (SHA-256 Verified)   |
                         | • Cambridge Tow Workbook (.xlsx)     |
                         | • Serialized Joblib & Manifests      |
                         +--------------------------------------+
```

---

## 4. Core Platform Modules

### 4.1 Research Workspace & Telemetry (`/`)
* **Operational Telemetry**: Real-time status cards detailing backend service health, database connection status, active ORM schema version, and migration state.
* **Target Readiness Register**: Live dashboard displaying which predictive targets are approved for operational use versus those actively blocked under scientific gating.
* **Recent Experimental Feed**: Chronological activity feed highlighting newly recorded empirical runs and pending prospective test matrices.
* **Quick Navigation Hub**: One-click contextual transitions directly into test planning, dataset importation, statistical analytics, or formal reporting.

### 4.2 Model Experience & Prediction Transparency (`/models`)
* **3-Tier Model Visual Hierarchy**:
  * **Tier 1 — External Real-Data Benchmark**: Carbon-fibre tow-on-tool friction estimator trained on the University of Cambridge Apollo dataset.
  * **Tier 2 — Synthetic Demonstration Fixture**: Deterministic software testbed (`SYNTHETIC-DEMO`) validating pipeline execution without asserting physical reality.
  * **Tier 3 — Experimental Composite Targets (`CURRENTLY BLOCKED`)**: Hard-gated glass-fibre/epoxy composite friction and wear targets locked against prediction and uncalibrated optimization.
* **Transparent Prediction Interface**:
  * Inputs display explicit scientific units (`N`, `MPa`, `mm`, `mm²`, `%`) alongside empirical boundary ranges.
  * Dynamic out-of-domain banners warn operators when requested parameters exceed experimental bounds.
  * Point predictions are explicitly watermarked: **`Model estimate — Not a measured result`**.
  * Input validation rejects negative values, division-by-zero geometries, and non-finite numbers.
* **Verified Evidence Panel**:
  * Sourced directly from cryptographically verified model artifact reports (`report.json` validated against SHA-256 manifest).
  * Held-out Group-Shuffle evaluation metrics: **$\text{MAE} = 0.1340$**, **$\text{RMSE} = 0.2263$**, **$R^2 = 0.7826$** across 42 held-out observations ($7$ train / $3$ holdout sweeps).
  * Stratified tow sizing disclosures: T700-12k-60E ($R^2 = 0.8716$) versus T700-12k-50C ($R^2 = -0.7446$).
  * Full scientific disclosure of specimen-independence limitations (absence of spool serial numbers, uncalibrated prediction intervals).
* **Transparent Candidate Condition Screening**:
  * Generates physical candidate conditions based on contact geometry and normal load relationships.
  * Ranks candidates by selected optimization criterion (`lowest_predicted_cof`, `highest_predicted_cof`, `load_sweep_grid`).
  * Direct **"Plan test"** workflow pre-populates the planning module with candidate conditions without claiming global optimality.

### 4.3 Experiment Planning & In Silico Screening (`/planning`)
* **Prospective Test Specification**: Formulate parameter sweeps (normal load, velocity, test duration, temperature, contact geometry) prior to physical machine allocation.
* **Seamless Model Handoff**: Parameter combinations recommended by `/models` are automatically pre-populated into the test planning form with source metadata intact.
* **Data Integrity Enforcement**: Prevents operators from entering measured responses (friction, wear depth, mass loss) into planned records.

### 4.4 Empirical Experiment Registry (`/experiments`)
* **Complete Record Lifecycle**: Create, view, edit, search, filter, and delete experimental records.
* **Strict Status Segregation**: Visual and database-level distinction between `MEASURED` observations and `PLANNED` prospective screening conditions.
* **Multi-Parameter Search & Sorting**: Real-time filtering by material system, record status, operator, and keyword query; pagination controls with configurable page sizes ($10, 25, 50, 100$).
* **Detailed Record Modal**: Displays specimen composition, counterface material, operating conditions, measured responses with exact source units, and SHA-256 provenance chain.
* **Direct Export Action**: One-click download of individual experiment engineering reports (PDF) directly from the inspection modal.

### 4.5 Tribological Analytics & Statistical Distributions (`/analytics`)
* **Registry KPI Metrics**: Total records, physically measured runs, prospective plans, distinct material systems, and populated response counts.
* **Empirical Friction (COF) Distribution**: Dynamic calculation of minimum, maximum, mean, and median with custom histogram binning computed directly from active database records.
* **Unit-Segregated Wear Analysis**: Segregates wear depth ($\mu\text{m}$) and specific wear rate ($\text{mm}^3/\text{N}\cdot\text{m}$) into separate distribution tables to prevent unphysical pooling.
* **Descriptive Condition Relationships**: Interactive scatter visualization plotting friction against normal load, sliding speed, or cumulative distance. Includes mandatory scientific disclaimers on correlation versus causation.

### 4.6 Data Ingestion & Provenance Auditing (`/imports`)
* **CSV Schema Pre-Validation**: Parses and inspects uploaded experimental CSV files against the strict laboratory template schema.
* **Cryptographic Byte Preservation**: Original file bytes are archived in PostgreSQL alongside a cryptographic SHA-256 fingerprint.
* **Duplicate Detection**: Identifies exact file duplicates and existing experiment IDs before commit.
* **Historical Intake Audit**: Full audit trail of past file imports, timestamps, and row validation outcomes.

### 4.7 Engineering Reports & Export Hub (`/reports`)
* **Server-Side PDF Engine**: Built using ReportLab 5.1 with a custom two-pass `NumberedCanvas` that generates running headers, persistent document IDs (`REP-*`), UTC timestamps, and `"Page X of Y"` footers.
* **Four Standardized Report Types**:
  1. *Individual Experiment Report (PDF)*: Single-run engineering specification with condition audit and response metrics.
  2. *Filtered Experiment Registry Summary (PDF & CSV)*: Summary of active records with applied filter parameters.
  3. *Engineering Analytics Summary (PDF & CSV)*: Synthesis of registry distributions, friction statistics, and wear distributions.
  4. *Model Evaluation & Provenance Audit (PDF)*: Scientific audit detailing verified benchmark performance, 50C deficit disclosures, and gating statuses.
* **RFC 4180 CSV Exports**: Clean tabular datasets with explicit units in column headers (`normal_load_n`, `sliding_velocity_mps`, etc.).

---

## 5. Scientific Integrity & Gating Framework

```
               +--------------------------------------------------------+
               |               SCIENTIFIC INTEGRITY GATES               |
               +--------------------------------------------------------+
                                            |
       +--------------------+---------------+--------------------+
       |                    |                                    |
       v                    v                                    v
[Gate 1: Zero Data]   [Gate 2: Target ML Hard Gate]   [Gate 3: Status & Unit Isolation]
• Missing data is     • Glass-fibre/epoxy composite   • Planned tests != measured runs.
  marked Unavailable.   targets: BLOCKED / NO_GO.     • Wear depth (microns) and
• No silent median    • External carbon-fibre model     specific wear rate (mm³/N·m)
  or mean imputation.   never satisfies composite ML.   are never pooled together.
```

### 5.1 The 3-Tier Model Hierarchy

| Tier | Identification | Scope & Substrate | Validation Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Cambridge COF Estimator | Carbon-fibre tow on glass tool ($0.078\text{ N} - 48.36\text{ N}$) | Group-Shuffle Cross-Validation ($R^2 = 0.7826$) | **ACTIVE (External Benchmark)** |
| **Tier 2** | `SYNTHETIC-DEMO` | Algorithmic fixture for software pipelines | Deterministic synthetic regression tests | **ACTIVE (Software Pipeline Only)** |
| **Tier 3** | Composite COF & Wear | Glass-fibre/epoxy composites with ceramic fillers | Unresolved DOCX-to-paper run mappings | **CURRENTLY BLOCKED / NO_GO** |

### 5.2 Rationale for Blocking Composite Targets

The platform implements a hard gate (`BLOCKED / NO_GO`) on composite prediction targets:
1. **Run Identification Ambiguity**: The experimental source dataset contains discrepancies between laboratory manuscript tables and raw extraction run indices. Mapping these without author clarification risks training models on mismatched operating conditions.
2. **Wear Metric Incompatibility**: Wear data was recorded using heterogeneous units (linear penetration vs volumetric specific wear rate) across different trials without standardized profilometry calibration curves.
3. **Prevention of Hallucinated Science**: Rather than deploying a flawed model that produces visually convincing but physically incorrect predictions, AI-TriboTwin locks inference until validated experimental updates are committed.

### 5.3 Strict Anti-Hallucination & Zero-Imputation Policy
* **No Median/Mean Imputation**: If an experimental record lacks a specific response measurement, it is stored as `null` and displayed as `"Unavailable"`. It is never silently imputed with statistical aggregates.
* **No Fabricated Confidence Intervals**: Conformal prediction intervals are withheld for the Cambridge model because the underlying dataset comprises only 10 distinct sweeps without verified spool serial numbers. The system refuses to present uncalibrated mathematical bands as physical uncertainty.

---

## 6. Technology Stack

| Layer | Component | Specification | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Next.js | 15.5.9 (App Router) | Server/Client rendering, responsive UI shell, strict routing |
| **Frontend Language** | TypeScript | 5.x (Strict Mode) | Full type safety across components, props, and API interfaces |
| **Styling & Design** | Tailwind CSS | 3.4+ & Lucide Icons | Accessible, high-contrast engineering design system |
| **Frontend Testing** | Vitest & RTL | 3.x / Testing Library | 52 unit and integration tests across 10 page/component suites |
| **Backend Framework** | FastAPI | 0.143.0 | High-performance asynchronous REST API with Pydantic v2 schemas |
| **Backend Language** | Python | 3.11 – 3.14 | Modern typing, dataclasses, and scientific libraries |
| **Database & ORM** | PostgreSQL / SQLite | SQLAlchemy 2.1 + Alembic | Declarative schema, migration tracking, check constraints, ACID |
| **Machine Learning** | Scikit-Learn | 1.9+ & Joblib | Ridge regression, GroupShuffleSplit, cross-validation metrics |
| **PDF Reporting** | ReportLab | 5.1 | Server-side vector PDF generation with custom two-pass canvas |
| **Testing (Backend)** | Pytest | 8.x + HTTPX TestClient | 132 automated tests covering routes, models, and reports |

---

## 7. Local Development & Quickstart

### 7.1 Prerequisites
* **Python**: 3.11, 3.12, 3.13, or 3.14 installed on your system path.
* **Node.js**: 20.x LTS or newer (with `npm` 10+).
* **Git**: Modern Git client.
* **Database**: SQLite (default local fallback, zero setup required) or PostgreSQL 16+.

### 7.2 Repository Setup
```bash
git clone https://github.com/devaprasathk28-dot/AI-Tribo-Twin.git
cd AI-Tribo-Twin
```

### 7.3 Backend Execution (FastAPI)
```powershell
# 1. Create and activate a Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install production and development dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Apply database schema migrations (defaults to SQLite dev database if DATABASE_URL is unset)
alembic -c backend\alembic.ini upgrade head

# 4. Launch FastAPI server on port 8001
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```
* The backend API will be available at: **`http://localhost:8001`**
* Interactive OpenAPI / Swagger documentation: **`http://localhost:8001/docs`**
* Health check endpoint: **`http://localhost:8001/api/v1/health`**

### 7.4 Frontend Execution (Next.js)
Open a new terminal window:
```powershell
cd frontend

# 1. Install Node dependencies
npm ci

# 2. Configure API host environment variable (PowerShell)
$env:NEXT_PUBLIC_API_URL = "http://localhost:8001"

# For bash/zsh on Linux/macOS:
# export NEXT_PUBLIC_API_URL="http://localhost:8001"

# 3. Launch the Next.js development server on port 3000
npm run dev -- --port 3000
```
* Open your browser and navigate to: **`http://localhost:3000`**

---

## 8. Automated Verification & Quality Assurance

The platform includes comprehensive test suites across both backend and frontend layers:

### 8.1 Backend Pytest Suite (132 tests)
Run the complete backend test suite:
```powershell
.\.venv\Scripts\pytest -v
```
**Test Coverage Breakdown**:
* `backend/tests/test_predictions.py`: Validates input range boundaries, out-of-domain tagging, candidate ranking, and error recovery.
* `backend/tests/test_reports.py`: Validates PDF generation, magic byte verification (`%PDF-`), running headers, custom Platypus flowables, and RFC 4180 CSV exports.
* `backend/tests/test_api.py`: Validates experiment CRUD, status filtering, pagination, and error handlers.
* `backend/tests/test_persistence.py`: Validates database models, check constraints, and unique index behavior.
* `backend/tests/test_cambridge_dataset.py`: Validates dataset parser, raw data ingestion, and feature transformations.
* `backend/tests/test_external_cof_model.py`: Validates model training, GroupShuffleSplit leakage prevention, and manifest hashing.

### 8.2 Frontend Vitest & Verification (52 tests)
```powershell
cd frontend

# Run all 52 Vitest component and integration tests
npm test

# Run strict TypeScript compilation check (0 errors required)
npm run typecheck

# Run ESLint check (0 errors, 0 warnings required)
npm run lint

# Run Next.js production build verification (10/10 routes prerendered)
npm run build
```

### 8.3 Cryptographic Scientific Data Hash
Verify that the primary scientific reference dataset has not been modified or corrupted:
```powershell
(Get-FileHash data\raw\tribological_experiments_raw.csv -Algorithm SHA256).Hash
# Expected: BC4B438BFCB472BDB92D653953B23ACD3FF20DBAF3E0220704AA0A16BDDEDD1D
```

---

## 9. REST API Specification

All API endpoints are versioned under `/api/v1` and return typed JSON or binary stream responses:

| Method | Endpoint | Description | Request / Query Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health telemetry and database check | None |
| `GET` | `/api/v1/models/status` | Model readiness gates, benchmark metrics & audit | None |
| `POST` | `/api/v1/models/external/predict` | Predict friction for single tow-on-tool condition | JSON: `ExternalCofPredictionRequest` |
| `POST` | `/api/v1/models/external/candidates/validate` | Pre-submission validation for candidate conditions | JSON: `CandidateValidationRequest` |
| `POST` | `/api/v1/models/external/recommendations` | Generate ranked physical test candidates | JSON: `RecommendationRequest` |
| `GET` | `/api/v1/experiments` | List, search, filter, and paginate experiments | `material_system`, `status`, `page`, `page_size`, `q` |
| `POST` | `/api/v1/experiments` | Record a new physically measured observation | JSON: `ExperimentCreateRequest` |
| `POST` | `/api/v1/plans` | Create a prospective screening test condition | JSON: `PlanCreateRequest` |
| `GET` | `/api/v1/experiments/{id}` | Retrieve single experiment by ID | Path: `id` (e.g., `EXP-001`) |
| `PUT` | `/api/v1/experiments/{id}` | Update conditions or measured responses | Path: `id`, JSON: `ExperimentUpdateRequest` |
| `DELETE` | `/api/v1/experiments/{id}` | Delete an experimental record | Path: `id` |
| `GET` | `/api/v1/analytics` | Compute registry KPIs, COF distributions & wear breakdowns | `material_system`, `record_status`, `date_from`, `date_to` |
| `GET` | `/api/v1/reports/experiment/{id}/pdf` | Download single-run engineering PDF report | Path: `id` |
| `GET` | `/api/v1/reports/experiments/pdf` | Download filtered experiment registry summary PDF | `material_system`, `status`, `operator` |
| `GET` | `/api/v1/reports/experiments/csv` | Export structured experiment registry CSV with explicit units | `material_system`, `status`, `operator` |
| `GET` | `/api/v1/reports/analytics/pdf` | Download analytics summary PDF report | `material_system`, `record_status`, `date_from`, `date_to` |
| `GET` | `/api/v1/reports/analytics/csv` | Export analytics KPIs and distributions CSV | `material_system`, `record_status`, `date_from`, `date_to` |
| `GET` | `/api/v1/reports/models/pdf` | Download formal model evaluation and provenance audit PDF | None |

---

## 10. Data Architecture & Database Schema

The database model is managed via SQLAlchemy and version-controlled using Alembic migrations:

```
+----------------------------------------------------------------------------------------------------+
|                                    TABLE: experiments                                              |
+------------------------------------+-----------------------------+---------------------------------+
| Column Name                        | SQL Type                    | Description & Constraints       |
+------------------------------------+-----------------------------+---------------------------------+
| id                                 | INTEGER                     | Primary Key (Autoincrement)     |
| experiment_id                      | VARCHAR(64)                 | Unique Identifier (EXP-*, PLN-*)|
| run_order                          | INTEGER                     | Laboratory sequence index       |
| status                             | VARCHAR(16)                 | 'MEASURED' or 'PLANNED'         |
| material_system                    | VARCHAR(128)                | Substrate formulation           |
| filler_type                        | VARCHAR(64)                 | Secondary phase / reinforcement |
| filler_content_wt_percent          | NUMERIC(6,3)                | Weight fraction (0 - 100%)      |
| counterface_material               | VARCHAR(64)                 | Pin/tool counterface spec       |
| normal_load_n                      | NUMERIC(8,3)                | Applied normal force (N)        |
| sliding_velocity_mps               | NUMERIC(8,3)                | Relative linear velocity (m/s)  |
| sliding_distance_m                 | NUMERIC(10,3)               | Total test travel distance (m)  |
| test_temperature_c                 | NUMERIC(6,2)                | Ambient chamber temp (°C)       |
| coefficient_of_friction            | NUMERIC(6,4)                | Measured mean friction coeff.   |
| wear_depth_um                      | NUMERIC(8,3)                | Linear penetration depth (µm)   |
| specific_wear_rate_mm3_per_nm      | NUMERIC(12,8)               | Volumetric wear rate            |
| wear_volume_loss_mm3               | NUMERIC(10,4)               | Total volumetric material loss  |
| operator                           | VARCHAR(64)                 | Technician / Principal Inv.     |
| notes                              | TEXT                        | Observations / equipment flags  |
| created_at                         | TIMESTAMP WITH TIME ZONE    | UTC record creation time        |
| updated_at                         | TIMESTAMP WITH TIME ZONE    | UTC last modification time      |
+------------------------------------+-----------------------------+---------------------------------+

+----------------------------------------------------------------------------------------------------+
|                                    TABLE: file_imports                                             |
+------------------------------------+-----------------------------+---------------------------------+
| id                                 | INTEGER                     | Primary Key (Autoincrement)     |
| filename                           | VARCHAR(255)                | Original uploaded file name     |
| sha256_hash                        | VARCHAR(64)                 | Cryptographic SHA-256 digest    |
| row_count                          | INTEGER                     | Extracted record count          |
| status                             | VARCHAR(32)                 | 'SUCCESS', 'PARTIAL', 'FAILED'  |
| file_bytes                         | LARGEBINARY / BYTEA         | Raw immutable source bytes      |
| created_at                         | TIMESTAMP WITH TIME ZONE    | UTC intake timestamp            |
+------------------------------------+-----------------------------+---------------------------------+
```

---

## 11. Repository Layout

```
AI-TriboTwin/
├── artifacts/
│   └── ml/
│       ├── external-cof-cambridge/        # Verified Cambridge model artifacts & report.json
│       └── synthetic-demo/                # Verified synthetic demonstration artifacts
├── backend/
│   ├── alembic/                           # Database schema migrations & version scripts
│   ├── app/
│   │   ├── api/                           # REST route controllers & dependency injections
│   │   ├── db/                            # SQLAlchemy models, session factory & base class
│   │   ├── domain/                        # Target readiness register logic & invariants
│   │   ├── schemas/                       # Pydantic v2 request/response validation models
│   │   └── services/                      # Analytics, prediction, reports & import services
│   └── tests/                             # Pytest automated test suites (132 tests)
├── data/
│   ├── external/                          # Cambridge tow-on-tool source workbook (.xlsx)
│   ├── raw/                               # Read-only experimental extraction CSV (SHA-256 secured)
│   ├── templates/                         # Standardized experiment intake template (.csv)
│   └── validation/                        # Target readiness register & evidence trackers
├── docs/                                  # Architectural decisions, sprint audits & source reviews
├── frontend/
│   ├── src/
│   │   ├── app/                           # Next.js App Router pages (/, /models, /reports, etc.)
│   │   ├── components/                    # Reusable UI components (Notice, Shell, Modal, Forms)
│   │   └── lib/                           # Typed API client & domain interfaces
│   └── tests/                             # Vitest integration suites (52 tests) & Playwright specs
├── scripts/                               # Database backup, restore & dataset build scripts
├── src/                                   # Standalone dataset parsers & ML training modules
├── compose.yaml                           # Multi-container Docker Compose configuration
├── requirements.txt                       # Backend Python dependencies
├── requirements-dev.txt                   # Development & testing Python dependencies
└── README.md                              # Complete platform documentation
```

---

## 12. Citations & Attribution

If you utilize AI-TriboTwin in scientific research or industrial tribology studies, please cite the corresponding data sources and foundations:

1. **Carbon-Fibre Tow Sliding Friction Benchmark**:  
   University of Cambridge Apollo Research Repository: *"Friction of carbon fibre tows"*  
   DOI: [`10.17863/CAM.1671`](https://doi.org/10.17863/CAM.1671)  
   *Referenced as an external benchmark dataset for continuous sliding friction under normal load ramps.*

2. **Composite Experimental Research Foundation**:  
   Experimental baseline extraction based on: *"AI-Enabled Prediction and Experimental Characterization of Tribological Behaviour and Wear Morphology in Ceramic-Filler included Glass Fiber Reinforced Epoxy Composites"*.  
   *Note: Composite prediction targets currently remain gated pending author run-mapping and wear metric resolution.*

---

## 13. License & Maintenance

This project is open-source software licensed under the **[MIT License](LICENSE)**.

* **Lead Maintainer**: [Devaprasath K.](https://github.com/devaprasathk28-dot)
* **Project Repository**: [https://github.com/devaprasathk28-dot/AI-Tribo-Twin.git](https://github.com/devaprasathk28-dot/AI-Tribo-Twin.git)
* **Bug Reports & Issues**: Please submit issues via GitHub Issues with reproducible logs and input data.
