

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a financial transparency auditor for non-profit / NGO
annual and financial reports. You will be given raw text extracted from a PDF.

Analyze it and respond with ONLY a JSON object (no markdown, no prose, no
code fences) in exactly this shape:

{
  "transparency_score": <integer 0-100>,
  "red_flags": [<string>, ...],
  "summary": "<2-3 sentence plain-language summary>"
}

Scoring guidance:
- 90-100: clear breakdown of income/expenses, named auditor, disclosed
  admin/overhead ratio, disclosed major donors/grants, dated and signed.
- 60-89: mostly clear financials but missing one or two disclosures
  (e.g. no named auditor, vague overhead figures).
- 30-59: numbers present but vague, inconsistent, or missing key sections
  (no breakdown of spending categories, no audit mention).
- 0-29: little to no real financial detail, boilerplate text, numbers
  don't add up, or signs of copy-pasted/generic content.

red_flags should be short, concrete phrases, e.g.:
  "No named external auditor"
  "Administrative costs not disclosed"
  "Total income and total expenses do not reconcile"
  "No breakdown of program vs overhead spending"

If the text is empty, unreadable, or clearly not a financial report,
return transparency_score: 0 and a red flag stating that.
"""


def _extract_json(raw_text: str) -> dict:
    """Best-effort extraction of a JSON object from the model's reply."""
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in AI response")

    return json.loads(raw_text[start:end + 1])


def analyze_report_with_ai(extracted_text: str) -> dict:
    
    if not ANTHROPIC_API_KEY:
        return {
            "transparency_score": 0,
            "red_flags": "AI analysis unavailable: missing ANTHROPIC_API_KEY",
            "summary": "Could not run AI analysis because the API key is not configured.",
        }

    if not extracted_text or not extracted_text.strip():
        return {
            "transparency_score": 0,
            "red_flags": "No readable text found in uploaded PDF",
            "summary": "The uploaded file had no extractable text to analyze.",
        }

    # Trim very long reports to keep the request reasonable
    trimmed_text = extracted_text[:15000]

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Here is the extracted report text:\n\n{trimmed_text}",
                    }
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        text_blocks = [
            block["text"]
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        raw_reply = "\n".join(text_blocks)

        parsed = _extract_json(raw_reply)

        score = int(parsed.get("transparency_score", 0))
        score = max(0, min(100, score))

        flags = parsed.get("red_flags", [])
        if isinstance(flags, list):
            flags_str = ", ".join(str(f) for f in flags)
        else:
            flags_str = str(flags)

        summary = str(parsed.get("summary", "")).strip()

        return {
            "transparency_score": score,
            "red_flags": flags_str,
            "summary": summary,
        }

    except requests.exceptions.RequestException as e:
        return {
            "transparency_score": 0,
            "red_flags": f"AI analysis request failed: {e}",
            "summary": "The AI analysis service could not be reached.",
        }
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return {
            "transparency_score": 0,
            "red_flags": f"Could not parse AI response: {e}",
            "summary": "The AI analysis service returned an unexpected response.",
        }