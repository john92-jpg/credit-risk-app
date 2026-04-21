from __future__ import annotations

import io

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.model_bundle import get_bundle
from app.models.schemas import BatchPredictionResponse, MetadataResponse, PredictionResponse, SinglePredictionInput
from app.services.inference_service import (
    dataframe_from_single_payload,
    generate_final_report_pdf,
    run_inference,
    safe_pdf_filename,
)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/metadata", response_model=MetadataResponse)
def metadata_endpoint():
    md = get_bundle().metadata
    return {
        "required_columns": md.get("required_columns", []),
        "optional_columns": md.get("optional_columns", []),
        "target_meaning": md.get("target_meaning", {}),
    }


@router.post("/predict-single", response_model=PredictionResponse)
def predict_single(payload: SinglePredictionInput):
    try:
        bundle = get_bundle()
        df_input = dataframe_from_single_payload(payload.model_dump(by_alias=True))
        result_df, added_columns, extras = run_inference(df_input, bundle)
        row = result_df.replace({np.nan: None}).to_dict(orient="records")[0]
        return {"row": row, "added_columns": added_columns, "extra_columns": extras}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/predict-excel", response_model=BatchPredictionResponse)
async def predict_excel(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_input = pd.read_excel(io.BytesIO(content))
        bundle = get_bundle()
        result_df, added_columns, extras = run_inference(df_input, bundle)
        return {
            "rows": result_df.replace({np.nan: None}).to_dict(orient="records"),
            "added_columns": added_columns,
            "extra_columns": extras,
            "row_count": len(result_df),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate-report-single")
def generate_report_single(payload: SinglePredictionInput):
    try:
        bundle = get_bundle()
        df_input = dataframe_from_single_payload(payload.model_dump(by_alias=True))
        result_df, _, _ = run_inference(df_input, bundle)
        selected = result_df.loc[0]
        pdf_bytes = generate_final_report_pdf(selected, bundle.metadata)
        filename = safe_pdf_filename(selected.get("Corporation", None), "report_finale_single.pdf")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate-report/{row_index}")
async def generate_report_from_excel(row_index: int, file: UploadFile = File(...)):
    try:
        content = await file.read()
        df_input = pd.read_excel(io.BytesIO(content))
        bundle = get_bundle()
        result_df, _, _ = run_inference(df_input, bundle)
        if row_index < 0 or row_index >= len(result_df):
            raise HTTPException(status_code=404, detail="Indice riga non valido")
        selected = result_df.loc[row_index]
        pdf_bytes = generate_final_report_pdf(selected, bundle.metadata)
        filename = safe_pdf_filename(selected.get("Corporation", None), f"report_finale_riga_{row_index}.pdf")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
