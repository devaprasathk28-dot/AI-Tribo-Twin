from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_VALIDATION = PROJECT_ROOT / "data" / "validation"

MODELS = PROJECT_ROOT / "models"
NOTEBOOKS = PROJECT_ROOT / "notebooks"
DASHBOARD = PROJECT_ROOT / "dashboard"
DOCS = PROJECT_ROOT / "docs"
