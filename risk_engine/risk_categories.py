"""
TPRM major risk categories and normalization for AI findings.
"""

TPRM_RISK_CATEGORIES = [
    "Strategic Risk",
    "Operational Risk",
    "Cybersecurity Risk",
    "Compliance Risk",
    "Financial Risk",
    "Reputational Risk",
    "Legal Risk",
    "Privacy Risk",
    "Third-Party Risk",
    "Technology Risk",
    "Business Continuity Risk",
    "Physical Security Risk",
    "Data Risk",
    "Human Resource Risk",
    "Environmental & Social Risk",
]

# Values that must NOT appear in the category field (audit phrasing / legacy control themes)
INVALID_CATEGORY_VALUES = {
    "potential risk",
    "missing evidence",
    "no evidence provided",
    "insufficient evidence provided",
    "evidence could not verify",
    "other",
    "governance",
    "access control",
    "identity & mfa",
    "identity and access management",
    "data protection",
    "encryption",
    "logging & monitoring",
    "logging and monitoring",
    "incident response",
    "vulnerability management",
    "compliance controls",
    "third-party risk management",
}

_CATEGORY_ALIASES = {
    "strategic": "Strategic Risk",
    "strategic risk": "Strategic Risk",
    "operational": "Operational Risk",
    "operational risk": "Operational Risk",
    "cybersecurity": "Cybersecurity Risk",
    "cybersecurity risk": "Cybersecurity Risk",
    "information security": "Cybersecurity Risk",
    "information security risk": "Cybersecurity Risk",
    "security risk": "Cybersecurity Risk",
    "compliance": "Compliance Risk",
    "compliance risk": "Compliance Risk",
    "financial": "Financial Risk",
    "financial risk": "Financial Risk",
    "reputational": "Reputational Risk",
    "reputational risk": "Reputational Risk",
    "reputation": "Reputational Risk",
    "legal": "Legal Risk",
    "legal risk": "Legal Risk",
    "privacy": "Privacy Risk",
    "privacy risk": "Privacy Risk",
    "third-party": "Third-Party Risk",
    "third party": "Third-Party Risk",
    "third-party risk": "Third-Party Risk",
    "third party risk": "Third-Party Risk",
    "vendor risk": "Third-Party Risk",
    "technology": "Technology Risk",
    "technology risk": "Technology Risk",
    "business continuity": "Business Continuity Risk",
    "business continuity risk": "Business Continuity Risk",
    "physical security": "Physical Security Risk",
    "physical security risk": "Physical Security Risk",
    "data": "Data Risk",
    "data risk": "Data Risk",
    "human resource": "Human Resource Risk",
    "human resources": "Human Resource Risk",
    "personnel": "Human Resource Risk",
    "human resource risk": "Human Resource Risk",
    "environmental": "Environmental & Social Risk",
    "environmental & social": "Environmental & Social Risk",
    "environmental and social": "Environmental & Social Risk",
    "esg": "Environmental & Social Risk",
}

_KEYWORD_TO_CATEGORY = [
    ("merger", "Strategic Risk"),
    ("acquisition", "Strategic Risk"),
    ("competitive", "Strategic Risk"),
    ("market strategy", "Strategic Risk"),
    ("outage", "Operational Risk"),
    ("downtime", "Operational Risk"),
    ("process failure", "Operational Risk"),
    ("service delivery", "Operational Risk"),
    ("mfa", "Cybersecurity Risk"),
    ("multi-factor", "Cybersecurity Risk"),
    ("phishing", "Cybersecurity Risk"),
    ("ransomware", "Cybersecurity Risk"),
    ("malware", "Cybersecurity Risk"),
    ("access control", "Cybersecurity Risk"),
    ("access review", "Cybersecurity Risk"),
    ("privileged", "Cybersecurity Risk"),
    ("vulnerability", "Cybersecurity Risk"),
    ("penetration", "Cybersecurity Risk"),
    ("logging", "Cybersecurity Risk"),
    ("monitoring", "Cybersecurity Risk"),
    ("incident response", "Cybersecurity Risk"),
    ("gdpr", "Compliance Risk"),
    ("pci", "Compliance Risk"),
    ("hipaa", "Compliance Risk"),
    ("soc 2", "Compliance Risk"),
    ("soc2", "Compliance Risk"),
    ("iso 27001", "Compliance Risk"),
    ("regulatory", "Compliance Risk"),
    ("audit", "Compliance Risk"),
    ("bankrupt", "Financial Risk"),
    ("financial", "Financial Risk"),
    ("fraud", "Financial Risk"),
    ("revenue", "Financial Risk"),
    ("reputation", "Reputational Risk"),
    ("media", "Reputational Risk"),
    ("brand", "Reputational Risk"),
    ("contract", "Legal Risk"),
    ("liability", "Legal Risk"),
    ("indemnif", "Legal Risk"),
    ("litigation", "Legal Risk"),
    ("intellectual property", "Legal Risk"),
    ("privacy", "Privacy Risk"),
    ("pii", "Privacy Risk"),
    ("personal data", "Privacy Risk"),
    ("data subject", "Privacy Risk"),
    ("fourth-party", "Third-Party Risk"),
    ("subprocessor", "Third-Party Risk"),
    ("vendor", "Third-Party Risk"),
    ("supplier", "Third-Party Risk"),
    ("legacy system", "Technology Risk"),
    ("unsupported", "Technology Risk"),
    ("cloud misconfig", "Technology Risk"),
    ("integration", "Technology Risk"),
    ("infrastructure", "Technology Risk"),
    ("disaster recovery", "Business Continuity Risk"),
    ("business continuity", "Business Continuity Risk"),
    ("backup", "Business Continuity Risk"),
    ("drp", "Business Continuity Risk"),
    ("biometric", "Physical Security Risk"),
    ("data center", "Physical Security Risk"),
    ("facility", "Physical Security Risk"),
    ("cctv", "Physical Security Risk"),
    ("data retention", "Data Risk"),
    ("data loss", "Data Risk"),
    ("data corruption", "Data Risk"),
    ("encryption", "Data Risk"),
    ("employee", "Human Resource Risk"),
    ("background check", "Human Resource Risk"),
    ("insider", "Human Resource Risk"),
    ("training", "Human Resource Risk"),
    ("esg", "Environmental & Social Risk"),
    ("sustainability", "Environmental & Social Risk"),
    ("environmental", "Environmental & Social Risk"),
]


def _canonical_category(name: str) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    for cat in TPRM_RISK_CATEGORIES:
        if key == cat.lower():
            return cat
    return None


def infer_category_from_text(*texts: str) -> str:
    combined = " ".join(t for t in texts if t).lower()
    for keyword, category in _KEYWORD_TO_CATEGORY:
        if keyword in combined:
            return category
    return "Operational Risk"


def is_invalid_category(category: str) -> bool:
    if not category:
        return True
    key = category.strip().lower()
    if key in INVALID_CATEGORY_VALUES:
        return True
    return _canonical_category(category) is None


def normalize_risk_description(risk: str, former_category: str = "") -> str:
    text = (risk or "").strip()
    former = (former_category or "").strip().lower()

    if former == "missing evidence" and text and not text.lower().startswith(
        ("missing evidence", "evidence could not", "insufficient evidence", "no evidence")
    ):
        text = f"Missing evidence observed: {text}"
    elif former == "potential risk" and text.lower().startswith("potential risk"):
        text = text[len("potential risk"):].lstrip(" :-")

    if text and not text[0].isupper():
        text = text[0].upper() + text[1:]

    return text or "Risk identified from supplied evidence requires analyst validation."


def normalize_risk_item(item: dict) -> dict:
    category = str(item.get("category", "")).strip()
    risk = str(item.get("risk", "")).strip()
    recommendation = str(item.get("recommendation", "")).strip()
    severity = str(item.get("severity", "Medium")).strip().title()
    if severity not in ("Critical", "High", "Medium", "Low"):
        severity = "Medium"

    canonical = _canonical_category(category)
    former_category = category

    if canonical and not is_invalid_category(category):
        category = canonical
    else:
        category = infer_category_from_text(category, risk, recommendation)

    item["category"] = category
    item["risk"] = normalize_risk_description(risk, former_category)
    item["severity"] = severity
    if "confidence" in item:
        try:
            item["confidence"] = int(item["confidence"])
        except (TypeError, ValueError):
            item["confidence"] = 75
    return item


def normalize_risks(risks: list) -> list:
    return [normalize_risk_item(dict(r)) for r in risks]


def risks_to_report_rows(risks: list) -> list:
    normalized = normalize_risks(risks)
    rows = []
    for idx, r in enumerate(normalized, start=1):
        rows.append(
            {
                "S.No": idx,
                "Category": r.get("category", ""),
                "Risk": r.get("risk", ""),
                "Severity": r.get("severity", ""),
                "Recommendation": r.get("recommendation", ""),
                "Confidence": r.get("confidence", ""),
            }
        )
    return rows
