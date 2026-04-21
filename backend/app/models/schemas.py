from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SinglePredictionInput(BaseModel):
    Corporation: Optional[str] = None
    Sector: Optional[str] = None
    Ticker: Optional[str] = None
    Current_Ratio: float = Field(..., alias="Current Ratio")
    Long_term_Debt_Capital: Optional[float] = Field(None, alias="Long-term Debt / Capital")
    Debt_Equity_Ratio: float = Field(..., alias="Debt/Equity Ratio")
    Gross_Margin: Optional[float] = Field(None, alias="Gross Margin")
    Operating_Margin: Optional[float] = Field(None, alias="Operating Margin")
    EBIT_Margin: Optional[float] = Field(None, alias="EBIT Margin")
    EBITDA_Margin: float = Field(..., alias="EBITDA Margin")
    Pre_Tax_Profit_Margin: Optional[float] = Field(None, alias="Pre-Tax Profit Margin")
    Net_Profit_Margin: Optional[float] = Field(None, alias="Net Profit Margin")
    Asset_Turnover: Optional[float] = Field(None, alias="Asset Turnover")
    ROE_Return_On_Equity: float = Field(..., alias="ROE - Return On Equity")
    Return_On_Tangible_Equity: Optional[float] = Field(None, alias="Return On Tangible Equity")
    ROA_Return_On_Assets: float = Field(..., alias="ROA - Return On Assets")
    ROI_Return_On_Investment: Optional[float] = Field(None, alias="ROI - Return On Investment")
    Operating_Cash_Flow_Per_Share: Optional[float] = Field(None, alias="Operating Cash Flow Per Share")
    Free_Cash_Flow_Per_Share: Optional[float] = Field(None, alias="Free Cash Flow Per Share")
    Year: int
    Month: int

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "Corporation": "Acme Corp",
                "Sector": "Technology",
                "Ticker": "ACME",
                "Current Ratio": 1.8,
                "Long-term Debt / Capital": 0.22,
                "Debt/Equity Ratio": 0.7,
                "Gross Margin": 0.56,
                "Operating Margin": 0.21,
                "EBIT Margin": 0.19,
                "EBITDA Margin": 0.24,
                "Pre-Tax Profit Margin": 0.16,
                "Net Profit Margin": 0.12,
                "Asset Turnover": 1.1,
                "ROE - Return On Equity": 0.15,
                "Return On Tangible Equity": 0.18,
                "ROA - Return On Assets": 0.08,
                "ROI - Return On Investment": 0.11,
                "Operating Cash Flow Per Share": 2.4,
                "Free Cash Flow Per Share": 1.9,
                "Year": 2025,
                "Month": 4,
            }
        },
    }


class PredictionResponse(BaseModel):
    row: Dict[str, Any]
    added_columns: List[str]
    extra_columns: List[str]


class MetadataResponse(BaseModel):
    required_columns: List[str]
    optional_columns: List[str]
    target_meaning: Dict[str, str]


class BatchPredictionResponse(BaseModel):
    rows: List[Dict[str, Any]]
    added_columns: List[str]
    extra_columns: List[str]
    row_count: int
