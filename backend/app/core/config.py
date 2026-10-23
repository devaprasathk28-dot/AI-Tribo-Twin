from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_VALIDATION = Path(os.getenv("DATA_VALIDATION_DIR", PROJECT_ROOT / "data" / "validation"))
IMPORTS_DIR = Path(os.getenv("IMPORTS_DIR", PROJECT_ROOT / "data" / "working" / "imports"))
MODEL_DEMO_DIR = PROJECT_ROOT / "artifacts" / "ml" / "synthetic-demo"
EXTERNAL_MODEL_DIR = Path(
    os.getenv("EXTERNAL_MODEL_DIR", PROJECT_ROOT / "artifacts" / "ml" / "external-cof-cambridge")
)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./tribotwin.sqlite3",
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
