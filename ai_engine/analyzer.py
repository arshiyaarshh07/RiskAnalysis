from groq import Groq
from dotenv import load_dotenv
import os
import json

from ai_engine.prompt_templates import (
    SYSTEM_PROMPT,
    build_analysis_prompt,
    normalize_framework,
    get_framework_label,
)

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL_NAME = "llama-3.1-8b-instant"

CHUNK_SIZE = 2500


def split_text(text, chunk_size=CHUNK_SIZE):

    chunks = []

    for i in range(0, len(text), chunk_size):

        chunks.append(
            text[i:i + chunk_size]
        )

    return chunks


def _parse_json_response(raw: str) -> dict:
    result = raw.strip()

    if result.startswith("```json"):
        result = result.replace("```json", "")
        result = result.replace("```", "")

    return json.loads(result.strip())


def analyze_chunk(chunk: str, framework: str | None = None):

    fid = normalize_framework(framework)
    user_prompt = build_analysis_prompt(chunk, framework=fid)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0,
    )

    result = response.choices[0].message.content.strip()
    return _parse_json_response(result)


def analyze_text(text: str, framework: str | None = None):

    fid = normalize_framework(framework)
    chunks = split_text(text)

    all_risks = []
    summaries = []

    for chunk in chunks:

        try:

            result = analyze_chunk(chunk, framework=fid)

            summaries.append(
                result.get("summary", "")
            )

            all_risks.extend(
                result.get("risks", [])
            )

        except Exception as e:

            print("\nCHUNK ERROR:\n")
            print(str(e))

    framework_label = get_framework_label(fid)

    if not all_risks:

        return {
            "summary": (
                f"[{framework_label}] AI analysis could not identify major risks "
                "from the provided evidence."
            ),
            "risks": [],
            "framework": fid,
            "framework_label": framework_label,
        }

    return {
        "summary": " ".join(summaries[:2]),
        "risks": all_risks,
        "framework": fid,
        "framework_label": framework_label,
    }
