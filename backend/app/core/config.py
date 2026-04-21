from pathlib import Path
from typing import List
import os


BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = BASE_DIR / "artifacts"

APP_NAME = os.getenv("APP_NAME", "Credit Risk Backend")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Se esiste variabile su Render → usa quella
# altrimenti usa default (Vercel + localhost per debug)

CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://credit-risk-xai.vercel.app,https://credit-risk-app-psi.vercel.app,http://localhost:5173"
    ).split(",")
    if origin.strip()
]