def calculate_severity(text):

    text = text.lower()

    if "missing" in text or "not implemented" in text:
        return "High"

    if "delayed" in text or "partial" in text:
        return "Medium"

    return "Low"


def confidence_score(text):

    score = 50

    if len(text) > 300:
        score += 20

    if "soc2" in text.lower():
        score += 15

    if "evidence" in text.lower():
        score += 10

    return min(score, 95)