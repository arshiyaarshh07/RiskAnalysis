from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

SYSTEM_PROMPT = """
You are a cybersecurity TPRM evidence review assistant.

STRICT RULES:
- Only analyze provided evidence
- Never hallucinate
- Never say confirmed breach
- Use:
  - Potential Risk
  - Missing Evidence
- Return STRICT JSON ONLY
"""

MODEL_NAME = "llama-3.1-8b-instant"

CHUNK_SIZE = 2500



def split_text(text, chunk_size=CHUNK_SIZE):

    chunks = []

    for i in range(0, len(text), chunk_size):

        chunks.append(
            text[i:i + chunk_size]
        )

    return chunks


def analyze_chunk(chunk):

    prompt = f"""
{SYSTEM_PROMPT}

Analyze this cybersecurity evidence.

Evidence:
{chunk}

Return ONLY valid JSON.

Format:

{{
  "summary": "...",
  "risks": [
    {{
      "category": "...",
      "risk": "...",
      "severity": "...",
      "recommendation": "...",
      "confidence": 85
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    if result.startswith("```json"):
        result = result.replace("```json", "")
        result = result.replace("```", "")

    result = result.strip()

    return json.loads(result)


def analyze_text(text):

    chunks = split_text(text)

    all_risks = []

    summaries = []

    for chunk in chunks:

        try:

            result = analyze_chunk(chunk)

            summaries.append(
                result.get("summary", "")
            )

            all_risks.extend(
                result.get("risks", [])
            )

        except Exception as e:

            print("\nCHUNK ERROR:\n")
            print(str(e))

    if not all_risks:

        return {
            "summary": "AI analysis could not identify major risks.",
            "risks": []
        }

    return {
        "summary": " ".join(summaries[:2]),
        "risks": all_risks
    }