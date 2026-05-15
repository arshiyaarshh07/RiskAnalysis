def categorize_risk(text):

    mapping = {
        "mfa": "Access Control",
        "access review": "Access Control",
        "encryption": "Data Protection",
        "incident": "Incident Response",
        "backup": "Business Continuity",
        "logging": "Logging & Monitoring",
        "vendor": "Third-Party Risk",
        "compliance": "Compliance",
        "vulnerability": "Vulnerability Management"
    }

    text_lower = text.lower()

    for keyword, category in mapping.items():
        if keyword in text_lower:
            return category

    return "Governance"