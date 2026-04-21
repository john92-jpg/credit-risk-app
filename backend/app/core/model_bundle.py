from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json

import joblib

from app.core.config import ARTIFACTS_DIR


@dataclass
class ModelBundle:
    preprocessor: Any
    baseline_model: Any
    symbolic_tree: Any
    neurosymbolic_model: Any
    metadata: Dict[str, Any]


_bundle: Optional[ModelBundle] = None


PREPROCESSOR_PATH = ARTIFACTS_DIR / "preprocessor.joblib"
BASELINE_MODEL_PATH = ARTIFACTS_DIR / "xgb_baseline.joblib"
SYMBOLIC_TREE_PATH = ARTIFACTS_DIR / "dt_symbolic.joblib"
NEUROSYMBOLIC_MODEL_PATH = ARTIFACTS_DIR / "xgb_neurosymbolic.joblib"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"



def load_metadata() -> Dict[str, Any]:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"metadata.json non trovato in: {METADATA_PATH}")
    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)



def load_bundle() -> ModelBundle:
    required_files = [
        PREPROCESSOR_PATH,
        BASELINE_MODEL_PATH,
        SYMBOLIC_TREE_PATH,
        NEUROSYMBOLIC_MODEL_PATH,
        METADATA_PATH,
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError("Mancano i seguenti artifacts:\n" + "\n".join(missing))

    metadata = load_metadata()
    return ModelBundle(
        preprocessor=joblib.load(PREPROCESSOR_PATH),
        baseline_model=joblib.load(BASELINE_MODEL_PATH),
        symbolic_tree=joblib.load(SYMBOLIC_TREE_PATH),
        neurosymbolic_model=joblib.load(NEUROSYMBOLIC_MODEL_PATH),
        metadata=metadata,
    )



def get_bundle() -> ModelBundle:
    global _bundle
    if _bundle is None:
        _bundle = load_bundle()
    return _bundle
