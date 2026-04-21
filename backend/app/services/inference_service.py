from __future__ import annotations

import io
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.model_bundle import ModelBundle

SHORT_FEATURE_LABELS = {
    "Asset Turnover": "Asset Turnover",
    "Current Ratio": "Current Ratio",
    "Debt/Equity Ratio": "Debt/Equity Ratio",
    "EBIT Margin": "EBIT Margin",
    "EBITDA Margin": "EBITDA Margin",
    "Free Cash Flow Per Share": "Free Cash Flow Per Share",
    "Gross Margin": "Gross Margin",
    "Long-term Debt / Capital": "Long-term Debt / Capital",
    "Net Profit Margin": "Net Profit Margin",
    "Operating Cash Flow Per Share": "Operating Cash Flow Per Share",
    "Operating Margin": "Operating Margin",
    "Pre-Tax Profit Margin": "Pre-Tax Profit Margin",
    "ROA - Return On Assets": "ROA",
    "ROE - Return On Equity": "ROE",
    "ROI - Return On Investment": "ROI",
    "Return On Tangible Equity": "Return On Tangible Equity",
    "Sector": "Sector",
    "Ticker": "Ticker",
    "Corporation": "Corporation",
    "Year": "Year",
    "Month": "Month",
}


def clean_input_dataframe(df: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
    df = df.copy()
    for col in metadata.get("drop_columns", []):
        if col in df.columns:
            df = df.drop(columns=[col])

    if "Rating Date" in df.columns:
        rating_date = pd.to_datetime(df["Rating Date"], errors="coerce")
        if "Year" not in df.columns:
            df["Year"] = rating_date.dt.year
        if "Month" not in df.columns:
            df["Month"] = rating_date.dt.month
        df = df.drop(columns=["Rating Date"])

    return df



def validate_columns(df: pd.DataFrame, metadata: Dict) -> Tuple[bool, List[str], List[str]]:
    required_columns = metadata.get("required_columns", [])
    optional_columns = metadata.get("optional_columns", [])
    current = set(df.columns)
    required = set(required_columns)
    allowed = set(required_columns + optional_columns)

    missing_required = sorted(list(required - current))
    extras = sorted(list(current - allowed))
    return len(missing_required) == 0, missing_required, extras



def fill_missing_optional_columns(df: pd.DataFrame, metadata: Dict) -> Tuple[pd.DataFrame, List[str]]:
    df = df.copy()
    optional_columns = metadata.get("optional_columns", [])
    added_columns: List[str] = []

    for col in optional_columns:
        if col not in df.columns:
            df[col] = np.nan
            added_columns.append(col)

    return df, added_columns



def align_to_training_columns(df: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
    df = df.copy()
    ordered_columns = metadata.get("training_columns", [])
    if not ordered_columns:
        raise ValueError("metadata.json non contiene 'training_columns'")

    for col in ordered_columns:
        if col not in df.columns:
            df[col] = np.nan

    return df[ordered_columns]



def clean_feature_name(feature: str):
    if not isinstance(feature, str):
        return feature
    feature = feature.strip()
    if feature.startswith("num__"):
        feature = feature.replace("num__", "", 1)
    if feature.startswith("cat__"):
        feature = feature.replace("cat__", "", 1)
    return feature



def shorten_feature_label(feature: str) -> str:
    feature = clean_feature_name(feature)
    return SHORT_FEATURE_LABELS.get(feature, feature)



def parse_rule_conditions(rule_text: str) -> List[Dict]:
    if not isinstance(rule_text, str) or not rule_text.strip():
        return []

    pattern = r"\((.*?)\s*(<=|>=|<|>)\s*([\-]?\d+(?:\.\d+)?)\)"
    matches = re.findall(pattern, rule_text)
    parsed = []

    for feature, operator, threshold in matches:
        parsed.append(
            {
                "feature": clean_feature_name(feature.strip()),
                "operator": operator.strip(),
                "threshold": float(threshold),
            }
        )
    return parsed



def split_onehot_categorical_feature(feature: str) -> Tuple[str, Optional[str]]:
    known_prefixes = ["Corporation_", "Sector_", "Ticker_"]
    for prefix in known_prefixes:
        if feature.startswith(prefix):
            base = prefix[:-1]
            value = feature[len(prefix):]
            return base, value
    return feature, None



def format_condition_explicit(feature: str, operator: str, threshold: float) -> str:
    feature = clean_feature_name(feature)
    short_label = shorten_feature_label(feature)
    threshold_fmt = f"{threshold:.2f}"

    base_feature, category_value = split_onehot_categorical_feature(feature)
    if category_value is not None:
        short_base = shorten_feature_label(base_feature)
        return f"{short_base} = {category_value}" if operator in [">", ">="] else f"{short_base} ≠ {category_value}"

    return f"{short_label} {operator} {threshold_fmt}"



def format_rule_explicit(rule_text: str) -> str:
    conditions = parse_rule_conditions(rule_text)
    if not conditions:
        return rule_text
    return " AND ".join(format_condition_explicit(c["feature"], c["operator"], c["threshold"]) for c in conditions)



def interpret_numeric_condition(feature: str, operator: str, threshold: float) -> str:
    feature = clean_feature_name(feature)
    short_label = shorten_feature_label(feature)
    threshold_fmt = f"{threshold:.2f}"

    positive_features = {
        "Current Ratio", "EBIT Margin", "EBITDA Margin", "Gross Margin", "Net Profit Margin",
        "Operating Margin", "Pre-Tax Profit Margin", "ROA - Return On Assets",
        "ROE - Return On Equity", "ROI - Return On Investment", "Return On Tangible Equity",
        "Free Cash Flow Per Share", "Operating Cash Flow Per Share", "Asset Turnover"
    }
    negative_features = {"Debt/Equity Ratio", "Long-term Debt / Capital"}

    base_feature, category_value = split_onehot_categorical_feature(feature)
    if category_value is not None:
        short_base = shorten_feature_label(base_feature)
        return f"{short_base} = {category_value}" if operator in [">", ">="] else f"{short_base} ≠ {category_value}"

    if feature in positive_features or feature in negative_features:
        return f"{short_label} contenuto (soglia ≤ {threshold_fmt})" if operator in ["<=", "<"] else f"{short_label} elevato (soglia > {threshold_fmt})"

    return f"{short_label} con condizione {operator} {threshold_fmt}"



def translate_rule_to_financial_language(rule_text: str) -> str:
    conditions = parse_rule_conditions(rule_text)
    if not conditions:
        return rule_text

    translated_conditions = [interpret_numeric_condition(c["feature"], c["operator"], c["threshold"]) for c in conditions]
    translated_conditions = list(dict.fromkeys(translated_conditions))

    if len(translated_conditions) == 1:
        return f"La valutazione è influenzata principalmente da {translated_conditions[0].lower()}."
    if len(translated_conditions) == 2:
        return f"La valutazione è influenzata principalmente da {translated_conditions[0].lower()} e {translated_conditions[1].lower()}."
    return f"La valutazione è influenzata principalmente da {', '.join(x.lower() for x in translated_conditions[:-1])}, e {translated_conditions[-1].lower()}."



def explain_risk_implication(prediction: int, rule_text: str) -> str:
    translated = translate_rule_to_financial_language(rule_text)
    if prediction == 1:
        return (
            f"{translated} Nel complesso, questa configurazione è coerente con una struttura economico-finanziaria "
            "più equilibrata, con maggiore capacità di sostenere il debito e assorbire tensioni operative. "
            "Per questo il caso risulta associato a un profilo di rischio contenuto."
        )
    return (
        f"{translated} Nel complesso, questa configurazione segnala criticità nella tenuta economico-finanziaria, "
        "in termini di sostenibilità del debito, redditività o capacità di generare cassa. "
        "Per questo il caso risulta associato a un profilo di rischio elevato."
    )



def risk_label(pred_class: int, metadata: Dict) -> str:
    return metadata.get("target_meaning", {}).get(str(pred_class), str(pred_class))



def risk_level(prob: float) -> str:
    if prob >= 0.75:
        return "Basso"
    if prob >= 0.55:
        return "Medio-Basso"
    if prob >= 0.40:
        return "Medio"
    return "Alto"



def executive_explanation(prediction: int, probability: float, rule_text: str) -> str:
    level = risk_level(probability)
    rule_business_text = explain_risk_implication(prediction, rule_text)
    if prediction == 1:
        outcome_text = "L'azienda è stata classificata come Investment Grade, quindi associata a un profilo di rischio contenuto."
    else:
        outcome_text = "L'azienda è stata classificata come High Risk / Non-Investment Grade, quindi associata a un profilo di rischio più elevato."
    return (
        f"{outcome_text} La probabilità stimata di appartenenza alla classe 1 è pari al {probability * 100:.1f}%, "
        f"corrispondente a un livello di rischio {level.lower()}. {rule_business_text}"
    )



def get_rule_details_from_active_column(rule_column_name: str, metadata: Dict) -> Dict:
    leaf_to_rule_map = metadata.get("leaf_to_rule_map", {})
    if not rule_column_name or rule_column_name == "Nessuna regola attiva":
        return {"leaf_id": None, "rule_text": "Nessuna regola attiva", "pred_class": None, "samples": None, "confidence": None}
    if not rule_column_name.startswith("rule_"):
        return {"leaf_id": None, "rule_text": rule_column_name, "pred_class": None, "samples": None, "confidence": None}

    leaf_id = rule_column_name.replace("rule_", "")
    detail = leaf_to_rule_map.get(str(leaf_id)) or leaf_to_rule_map.get(int(leaf_id)) if str(leaf_id).isdigit() else None
    if detail is None:
        return {"leaf_id": leaf_id, "rule_text": rule_column_name, "pred_class": None, "samples": None, "confidence": None}

    return {
        "leaf_id": leaf_id,
        "rule_text": detail.get("rule_text", rule_column_name),
        "pred_class": detail.get("pred_class"),
        "samples": detail.get("samples"),
        "confidence": detail.get("confidence"),
    }



def build_rule_features(X_proc: np.ndarray, symbolic_tree) -> pd.DataFrame:
    leaves = symbolic_tree.apply(X_proc)
    return pd.get_dummies(leaves, prefix="rule")



def align_rule_features(train_rule_columns: List[str], rules_df: pd.DataFrame) -> pd.DataFrame:
    out = rules_df.copy()
    for column in train_rule_columns:
        if column not in out.columns:
            out[column] = 0
    return out[train_rule_columns]



def classify_probability(probability: float, threshold: float) -> int:
    return int(probability >= threshold)



def run_inference(df_input: pd.DataFrame, bundle: ModelBundle):
    metadata = bundle.metadata
    threshold = float(metadata.get("probability_threshold", 0.50))

    df_clean = clean_input_dataframe(df_input, metadata)
    ok, missing_required, extras = validate_columns(df_clean, metadata)
    if not ok:
        raise ValueError("Colonne obbligatorie mancanti: " + ", ".join(missing_required))

    df_clean, added_columns = fill_missing_optional_columns(df_clean, metadata)
    df_clean = align_to_training_columns(df_clean, metadata)

    X_proc = bundle.preprocessor.transform(df_clean)
    rules_df = build_rule_features(X_proc, bundle.symbolic_tree)
    train_rule_columns = metadata.get("rule_feature_columns", [])
    if not train_rule_columns:
        raise ValueError("metadata.json non contiene 'rule_feature_columns'")

    rules_df = align_rule_features(train_rule_columns, rules_df)
    X_ns = np.hstack([X_proc, rules_df.values])

    ns_proba = bundle.neurosymbolic_model.predict_proba(X_ns)[:, 1]
    ns_pred = np.array([classify_probability(p, threshold) for p in ns_proba])

    result = df_input.copy()
    result["ns_prob_classe_1"] = np.round(ns_proba, 4)
    result["ns_predizione"] = ns_pred
    result["ns_esito"] = [risk_label(v, metadata) for v in ns_pred]

    explicit_rules = []
    financial_translations = []
    risk_interpretations = []
    confidences = []

    for i in range(rules_df.shape[0]):
        row_rules = rules_df.iloc[i]
        active_cols = [c for c, v in row_rules.items() if v == 1]
        active_col = active_cols[0] if active_cols else "Nessuna regola attiva"

        details = get_rule_details_from_active_column(active_col, metadata)
        raw_rule_text = details["rule_text"]
        explicit_rule = format_rule_explicit(raw_rule_text)
        translation = translate_rule_to_financial_language(raw_rule_text)
        implication = explain_risk_implication(int(ns_pred[i]), raw_rule_text)

        explicit_rules.append(explicit_rule)
        financial_translations.append(translation)
        risk_interpretations.append(implication)
        confidences.append(details["confidence"])

    result["driver_principali"] = explicit_rules
    result["regola_tecnica_attiva"] = explicit_rules
    result["traduzione_regola"] = financial_translations
    result["interpretazione_rischio_regola"] = risk_interpretations
    result["confidenza_regola"] = confidences

    return result, added_columns, extras



def build_appendix_rules_table(metadata: Dict) -> List[Dict]:
    leaf_to_rule_map = metadata.get("leaf_to_rule_map", {})
    items = []
    for key, value in leaf_to_rule_map.items():
        try:
            leaf_id = int(key)
        except Exception:
            leaf_id = key
        items.append({
            "leaf_id": leaf_id,
            "pred_class": value.get("pred_class"),
            "samples": value.get("samples"),
            "confidence": value.get("confidence"),
            "rule_text": format_rule_explicit(value.get("rule_text", "")),
        })
    return sorted(items, key=lambda x: x["leaf_id"])



def generate_final_report_pdf(selected_row: pd.Series, metadata: Dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, leading=11)
    small_bold = ParagraphStyle("small_bold", parent=styles["Normal"], fontSize=9, leading=11, spaceAfter=4)

    prob = float(selected_row["ns_prob_classe_1"])
    pred = int(selected_row["ns_predizione"])
    level = risk_level(prob)
    explanation_text = executive_explanation(pred, prob, str(selected_row["regola_tecnica_attiva"]))

    company = selected_row.get("Corporation", "N/D") if pd.notna(selected_row.get("Corporation", None)) else "N/D"
    ticker = selected_row.get("Ticker", "N/D") if pd.notna(selected_row.get("Ticker", None)) else "N/D"
    sector = selected_row.get("Sector", "N/D") if pd.notna(selected_row.get("Sector", None)) else "N/D"
    year = selected_row.get("Year", "N/D")
    month = selected_row.get("Month", "N/D")

    elements = [
        Paragraph("Report Finale di Valutazione del Rischio di Credito", styles["Title"]),
        Spacer(1, 16),
        Paragraph("1. Profilo aziendale", styles["Heading2"]),
        Paragraph(f"<b>Corporation:</b> {company}", small),
        Paragraph(f"<b>Ticker:</b> {ticker}", small),
        Paragraph(f"<b>Sector:</b> {sector}", small),
        Paragraph(f"<b>Periodo:</b> {month}/{year}", small),
        Spacer(1, 12),
        Paragraph("2. Esito della valutazione", styles["Heading2"]),
        Paragraph(f"<b>Classe prevista:</b> {selected_row['ns_esito']}", small),
        Paragraph(f"<b>Probabilità classe 1:</b> {prob * 100:.2f}%", small),
        Paragraph(f"<b>Livello di rischio:</b> {level}", small),
        Spacer(1, 12),
        Paragraph("3. Driver principali", styles["Heading2"]),
        Paragraph(str(selected_row["driver_principali"]), small),
        Spacer(1, 10),
        Paragraph("4. Spiegazione business", styles["Heading2"]),
        Paragraph(explanation_text, small),
        Spacer(1, 10),
        Paragraph("5. Traduzione della regola", styles["Heading2"]),
        Paragraph(str(selected_row["traduzione_regola"]), small),
        Spacer(1, 10),
        Paragraph("6. Interpretazione del rischio", styles["Heading2"]),
        Paragraph(str(selected_row["interpretazione_rischio_regola"]), small),
        Spacer(1, 10),
        Paragraph("7. Confidenza della regola", styles["Heading2"]),
        Paragraph(str(selected_row.get("confidenza_regola", "N/D")), small),
        PageBreak(),
        Paragraph("Appendice - Regole simboliche", styles["Heading2"]),
        Spacer(1, 8),
    ]

    appendix_data = [[
        Paragraph("Leaf", small_bold),
        Paragraph("Classe", small_bold),
        Paragraph("Campioni", small_bold),
        Paragraph("Confidenza", small_bold),
        Paragraph("Regola", small_bold),
    ]]

    for row in build_appendix_rules_table(metadata):
        conf_text = f"{float(row['confidence']) * 100:.1f}%" if row["confidence"] is not None else "N/D"
        appendix_data.append([
            Paragraph(str(row["leaf_id"]), small),
            Paragraph(str(row["pred_class"]), small),
            Paragraph(str(row["samples"]), small),
            Paragraph(conf_text, small),
            Paragraph(str(row["rule_text"]), small),
        ])

    appendix_table = Table(appendix_data, colWidths=[45, 45, 55, 60, 315], repeatRows=1)
    appendix_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(appendix_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()



def dataframe_from_single_payload(payload: Dict) -> pd.DataFrame:
    return pd.DataFrame([payload])



def safe_pdf_filename(company: Optional[str], fallback: str) -> str:
    if company and str(company).strip():
        safe = str(company).replace(" ", "_").replace("/", "_")
        return f"report_finale_{safe}.pdf"
    return fallback



def generate_pdf_from_dataframe_row(row_index: int, df_input: pd.DataFrame, bundle: ModelBundle) -> bytes:
    result_df, _, _ = run_inference(df_input, bundle)
    if row_index < 0 or row_index >= len(result_df):
        raise HTTPException(status_code=404, detail="Indice riga non valido")
    selected = result_df.loc[row_index]
    return generate_final_report_pdf(selected, bundle.metadata)
