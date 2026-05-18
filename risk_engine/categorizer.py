from risk_engine.risk_categories import infer_category_from_text, normalize_risk_item


def categorize_risk(text: str) -> str:
    return infer_category_from_text(text)


def categorize_risk_record(risk_record: dict) -> dict:
    return normalize_risk_item(risk_record)
