# AI-TriboTwin

AI-driven digital twin for tribological prediction, virtual experimentation,
and multi-objective optimization of ceramic-filler reinforced GFRP composites.

## Application

AI-TriboTwin is being developed as a Next.js frontend, FastAPI API, and
PostgreSQL-backed experimental-record system. It is an evidence-intake and
planning foundation, not a validated digital twin.

Current safeguards:

- The source-extraction dataset remains read-only. Imports require the
  dedicated experiment-record template and explicit confirmation of the
  previewed SHA-256.
- Planned test conditions are stored separately from measured conditions and
  responses. Provenance fields are retained with each record.
- CSV uploads are validated before database persistence, and the original
  uploaded bytes are preserved in PostgreSQL with a SHA-256 fingerprint.
- Prediction and optimization endpoints fail closed while target evidence,
  validated models, evaluation, and constraints are unavailable.

### Run locally

Requirements: Python 3.11 or newer, Node.js 20+, and PostgreSQL 16+ (or Docker
with Compose).

#### Docker Compose

Copy `.env.example` to `.env` and replace `POSTGRES_PASSWORD` with a long,
random, URL-safe password. Compose requires both this password and
`NEXT_PUBLIC_API_URL`; it has no built-in database password. PostgreSQL and
API host ports default to 5433 and 8001 to avoid common local-service port
conflicts. All published service ports are bound to loopback only.

```powershell
Copy-Item .env.example .env
# Edit .env and replace the placeholder password before starting services.
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8001/api/v1/health
```

The API container applies Alembic migrations before starting. Verify that
`/api/v1/health` reports both service and database as `ok`. Database records
persist in the named `postgres_data` volume across container restarts. Do not
use `docker compose down -v` if that volume contains data you want to keep.
The API container installs its runtime and synthetic-model demonstration
dependencies from [`backend/requirements.txt`](backend/requirements.txt). The
root requirements file also includes additional research and development tools.

#### PostgreSQL backup and restore

Create a custom-format backup in the ignored `backups/` folder:

```powershell
.\scripts\backup-postgres.ps1
```

Restore only into a new, unused database whose name starts with
`tribotwin_restore_`; the restore script refuses an existing database and never
targets the application database:

```powershell
.\scripts\restore-postgres-new-database.ps1 `
  -BackupPath .\backups\tribotwin-<timestamp>.dump `
  -TargetDatabase tribotwin_restore_verification
```

The restored database is deliberately separate from the application database.
Inspect it before any separately planned cutover. Keep backups protected because
they may contain experimental records; the repository ignores `backups/`.

#### Run API and frontend separately

Set `DATABASE_URL` to a local PostgreSQL URL before migrating and starting the
API. For local development only, the API and Alembic default to an ignored
SQLite file when `DATABASE_URL` is unset.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://tribotwin:<password>@localhost:5433/tribotwin"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

In another PowerShell terminal, point the frontend to the API explicitly:

```powershell
cd frontend
$env:NEXT_PUBLIC_API_URL = "http://localhost:8001"
npm ci
npm run dev
```

Open `http://localhost:3000`; the API listens at `http://localhost:8001`. The frontend does not embed a default API host;
set `NEXT_PUBLIC_API_URL` in the environment used to build/run it.

The initial Alembic migration is additive. Its downgrade drops application
tables and their data; do not downgrade a database containing records unless
you have a verified backup and intend to discard that data.

### Tests and checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm test
npm run test:e2e
npm run typecheck
npm run lint
npm run build
```

The backend integration test suite uses an isolated, temporary SQLite database
with the real Alembic migration and verifies data persistence across API
client restarts. It does not substitute for a PostgreSQL/Docker integration
run. Frontend Playwright tests mock the API and remain a separate test layer.

The raw measurements have not passed the scientific readiness gate. No model
has been trained on composite experimental records, and no validated
experimental prediction or optimization is available.

### Synthetic ML pipeline demonstration

Run the deterministic fixture pipeline from the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.models.training
```

It compares a mean baseline and Ridge regression using group cross-validation,
selects by training-fold MAE, then reports a separate group-held-out evaluation.
The model, provenance manifest, metrics, held-out predictions, and plot are
written under `artifacts/ml/synthetic-demo/` and shown on the application's
**ML status** page. This synthetic exercise validates the software pipeline
only; it is not trained on the experimental CSV and its metrics are not
composite-material evidence. The pipeline rejects experimental training while
the target-readiness register marks a target `BLOCKED`.

### External real-data model (Cambridge carbon-fibre tow)

A separate model is trained on real measurements from the University of
Cambridge "Friction of carbon fibre tows" dataset (carbon-fibre tow on a glass
tool). It is an external material system: its metrics are not AI-TriboTwin
composite results and it cannot satisfy the blocked composite targets.

```powershell
.\.venv\Scripts\python.exe -m src.data.cambridge          # optional: build processed dataset
.\.venv\Scripts\python.exe -m src.models.external_cof     # train, evaluate, write artifacts
```

The parser reads `data/external/cambridge-cam-1671/raw/TowTool_ContactLengthAndFrictionForce.xlsx`,
writes a tidy processed dataset with a provenance sidecar under
`data/external/cambridge-cam-1671/processed/`, and stores the model bundle
under `artifacts/ml/external-cof-cambridge/`. The API exposes the verified
report at `/api/v1/models/status` (key `external_model`) and the plot at
`/api/v1/models/external/predictions.png`, both surfaced on the **ML status**
page. See [`docs/SPRINT5_REAL_DATA_MODEL.md`](docs/SPRINT5_REAL_DATA_MODEL.md)
for the dataset, validation design, metrics, and open items.

### External tow-on-tool prediction workflow

The verified external bundle is served as a typed prediction endpoint:

```powershell
curl -s -X POST http://localhost:8001/api/v1/models/external/predict `
  -H "Content-Type: application/json" -d "@request.json"
```

`POST /api/v1/models/external/predict` accepts a single tow-on-tool
observation (normal load, nominal pressure, contact geometry, and the T700 tow
sizing), derives `log10(normal_load_n)` server-side, and returns the predicted
coefficient of friction with the model identifier, training ranges, held-out
metrics, the external-domain limitation, and a domain status. Missing,
malformed, non-finite, non-positive, or unsupported-categorical inputs are
rejected with a 4xx response; inputs outside the recorded training ranges are
scored but flagged as `OUT_OF_DOMAIN`; and the endpoint fails safe with a 503
if the manifest or any artifact fails provenance verification. Requests are
strict (`extra="forbid"`, no numeric-string coercion). The **ML status** page
renders a matching prediction form with unit-labelled inputs, the recorded
training range for each feature, and the resulting prediction, provenance,
metrics, and domain warnings. This endpoint produces a point estimate for the
external carbon-fibre-tow system only; it never reports a composite target as
trained. See
[`docs/SPRINT6_PREDICTION_WORKFLOW.md`](docs/SPRINT6_PREDICTION_WORKFLOW.md).

A build helper for the processed dataset is
[`scripts/build_cambridge_dataset.py`](scripts/build_cambridge_dataset.py).

The experiment-record template is
[`data/templates/experiment_record_template.csv`](data/templates/experiment_record_template.csv).

## Long-term research stages

1. Project setup
2. Experimental data extraction
3. Data audit and normalization
4. Exploratory data analysis
5. Feature engineering
6. ML benchmarking
7. Virtual experiment engine
8. Multi-objective optimization
9. Explainable and uncertainty-aware AI
10. Next-best-experiment recommendation
11. Dashboard extensions
12. Physical validation
13. Closed-loop model update

## Source foundation

Initial experimental data will be extracted from the supplied paper:
"AI-Enabled Prediction and Experimental Characterization of Tribological Behaviour
and Wear Morphology in Ceramic-Filler included Glass Fiber Reinforced Epoxy Composites".

Important: experimental observations, AI predictions, and AI recommendations must
remain clearly separated throughout the project.
#
