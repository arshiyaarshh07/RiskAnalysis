"""
TPRM evidence-review prompts with framework-specific alignment (SOC 2, ISO 27001, general TPRM).
"""

import json
from pathlib import Path

from risk_engine.risk_categories import TPRM_RISK_CATEGORIES

FRAMEWORKS_PATH = Path(__file__).resolve().parent.parent / "data" / "frameworks.json"

TPRM_CATEGORIES_BLOCK = "\n".join(f"- {c}" for c in TPRM_RISK_CATEGORIES)

VALID_FRAMEWORKS = frozenset({"soc2", "iso27001", "tprm"})

DEFAULT_FRAMEWORK = "soc2"

FRAMEWORK_ALIASES = {
    "soc2": "soc2",
    "soc_2": "soc2",
    "soc 2": "soc2",
    "soc-2": "soc2",
    "iso27001": "iso27001",
    "iso_27001": "iso27001",
    "iso 27001": "iso27001",
    "iso-27001": "iso27001",
    "iso": "iso27001",
    "tprm": "tprm",
    "general": "tprm",
    "general_tprm": "tprm",
}


def normalize_framework(framework: str | None) -> str:
    if not framework:
        return DEFAULT_FRAMEWORK
    key = framework.strip().lower().replace(" ", "_")
    return FRAMEWORK_ALIASES.get(key, DEFAULT_FRAMEWORK)


def load_frameworks_config() -> dict:
    with open(FRAMEWORKS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_framework_label(framework: str | None) -> str:
    fid = normalize_framework(framework)
    cfg = load_frameworks_config()
    return cfg["frameworks"][fid]["label"]


FRAMEWORK_REVIEW_CONTEXT = {
    "soc2": """
REVIEW FRAMEWORK: SOC 2 Type II (Trust Services Criteria)

Align findings to applicable Trust Services Categories, especially:
- CC (Common Criteria) — logical access, change management, risk mitigation
- Security — access controls, monitoring, incident handling
- Availability — resilience, recovery, capacity (when evidenced)
- Confidentiality — data handling and protection (when evidenced)
- Processing Integrity — processing accuracy and completeness (when evidenced)
- Privacy — notice, choice, retention (only when privacy evidence is present)

Map observations to SOC 2–style control themes (e.g., access provisioning, logging,
change management, vendor management) without claiming certification or audit opinion.
""",
    "iso27001": """
REVIEW FRAMEWORK: ISO/IEC 27001 (ISMS & Annex A)

Align findings to ISO 27001 control themes, including where evidenced:
- Organizational controls (policies, roles, supplier relationships)
- People controls (screening, awareness, terms of employment)
- Physical controls (perimeters, secure areas, equipment)
- Technological controls (access, cryptography, operations security, communications,
  system acquisition/development, incident management, continuity, compliance)

Reference Annex A–style domains only when supported by supplied evidence.
Do not assert ISO certification, Statement of Applicability approval, or audit pass/fail.
""",
    "tprm": """
REVIEW FRAMEWORK: General Third-Party Risk Management (TPRM)

Apply a blended lens using SOC 2 principles and ISO 27001 control themes where relevant.
Prioritize vendor risk signals: access governance, data protection, monitoring, incident
readiness, continuity, subprocessors, and compliance evidence gaps suitable for onboarding
or reassessment workflows.
""",
}

SYSTEM_PROMPT = """
You are a Senior Cybersecurity Risk Analyst specializing in SOC 2 Type II assessments,
ISO 27001 security reviews, Third-Party Risk Management (TPRM), and vendor security
evidence analysis.

STRICT RULES:
1. ONLY analyze provided evidence — never hallucinate.
2. NEVER assume controls exist if evidence is missing.
3. NEVER state: "Vendor is insecure", "Confirmed breach", or "Control failure confirmed".
4. ALWAYS use audit-safe language IN THE "risk" FIELD ONLY (never as category):
   "Evidence could not verify", "Missing evidence observed", "Insufficient evidence provided".
5. NEVER use "Potential Risk" or "Missing Evidence" as a category value.
6. If evidence is unavailable, incomplete, or unclear, state that in the "risk" field.
7. Return STRICT JSON ONLY — no markdown fences or commentary outside JSON.
8. This is AI-assisted preliminary evidence review only — no legal conclusions,
   compliance certification claims, or final audit statements.
"""

TPRM_ANALYSIS_PROMPT = """
You are a Senior Cybersecurity Risk Analyst specializing in:

- SOC 2 Type II assessments
- ISO 27001 security reviews
- Third-Party Risk Management (TPRM)
- Vendor security evidence analysis

Your task is to review ONLY the provided evidence and identify risks, control gaps,
missing evidence, and governance concerns using standard TPRM risk categories.

IMPORTANT RULES:

1. NEVER hallucinate.
2. NEVER assume controls exist if evidence is missing.
3. NEVER state:
   - "Vendor is insecure"
   - "Confirmed breach"
   - "Control failure confirmed"

4. In the "risk" field, use professional audit-safe wording such as:
   - "Evidence could not verify..."
   - "Missing evidence observed for..."
   - "Insufficient evidence provided regarding..."
   Do NOT label the category as "Potential Risk" or "Missing Evidence".

5. If evidence is unavailable, incomplete, or unclear, describe that in the "risk" field.

6. Review should be aligned with the ACTIVE REVIEW FRAMEWORK specified below
   (SOC 2, ISO 27001, or general TPRM as applicable).

--------------------------------------------------

{framework_context}

--------------------------------------------------

RISK CATEGORY RULES (MANDATORY)

The "category" field MUST be exactly ONE of these TPRM major risk categories:

{tprm_categories}

NEVER use as category:
- Potential Risk
- Missing Evidence
- Access Control
- Identity and Access Management
- Or any control theme / audit phrase

Map each finding to the single best-fit major category above (e.g., missing MFA → Cybersecurity Risk;
no DRP → Business Continuity Risk; GDPR gap → Compliance Risk).

Evaluate risk as: Likelihood × Impact (document implicitly via severity).

Distinguish:
- Inherent risk: risk before controls (when evidence shows gap)
- Residual risk: risk after controls (when evidence shows partial mitigation)

--------------------------------------------------

SEVERITY CLASSIFICATION RULES

Assign severity as:

- Critical
- High
- Medium
- Low

Severity should depend on:

- Evidence quality
- Potential business impact
- Missing critical controls
- Operational exposure

--------------------------------------------------

CONFIDENCE SCORE

Generate a confidence score (0-100) based on:

- Evidence clarity
- Evidence completeness
- AI certainty
- Control verification strength

--------------------------------------------------

OUTPUT FORMAT

Return ONLY valid JSON.

{{
  "summary": "Executive summary of overall security posture and evidence quality.",

  "risks": [
    {{
      "category": "Cybersecurity Risk",
      "risk": "Evidence could not verify quarterly privileged access review for critical systems.",
      "severity": "Medium",
      "recommendation": "Implement automated quarterly privileged access review workflows and maintain audit evidence.",
      "confidence": 88
    }}
  ]
}}

--------------------------------------------------

IMPORTANT FINAL INSTRUCTION

This is an AI-assisted preliminary evidence review only.

Do NOT produce:
- legal conclusions
- compliance certification claims
- final audit statements

Only identify:
- risks aligned to major TPRM categories
- missing evidence (described in the risk field)
- operational and security concerns

--------------------------------------------------

EVIDENCE TO REVIEW:

{evidence_text}
"""


def build_analysis_prompt(evidence_text: str, framework: str | None = None) -> str:
    fid = normalize_framework(framework)
    framework_context = FRAMEWORK_REVIEW_CONTEXT[fid]
    label = get_framework_label(fid)
    header = f"ACTIVE REVIEW FRAMEWORK: {label}\n"
    return header + TPRM_ANALYSIS_PROMPT.format(
        framework_context=framework_context.strip(),
        tprm_categories=TPRM_CATEGORIES_BLOCK,
        evidence_text=evidence_text,
    )
