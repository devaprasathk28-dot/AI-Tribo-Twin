from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import ALLOWED_ORIGINS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="AI-TriboTwin API",
    description=(
        "Experimental-data intake and planning API. Prediction and optimization "
        "remain gated by scientific readiness evidence."
    ),
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
