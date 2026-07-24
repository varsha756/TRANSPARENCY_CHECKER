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


MONEY_USAGE_SYSTEM_PROMPT = """You are a donor-transparency assistant. You will be given:
1. The financial/annual report text an NGO submitted.
2. The total amount a specific donor has given to this NGO.

Write a short, plain-language explanation (3-5 sentences) of how a donor's
contribution likely supported the NGO's work, based ONLY on what the report
text actually says (program areas, spending categories, overhead ratio, etc).

Rules:
- Do not invent figures that aren't in the report.
- If the report doesn't break down spending clearly, say so honestly and
  give a general sense of the NGO's stated mission/activities instead.
- Do not claim a precise rupee-for-rupee allocation (e.g. don't say
  "your ₹500 bought X notebooks") unless the report itself gives that kind
  of per-unit costing.
- Keep the tone factual and reassuring but not exaggerated.
- Respond with ONLY a JSON object, no markdown, no code fences, in this shape:

{
  "usage_summary": "<3-5 sentence explanation>"
}
"""


def analyze_money_usage(org_name: str, extracted_text: str, donation_amount: float, donation_count: int) -> dict:
    if not ANTHROPIC_API_KEY:
        return {"usage_summary": "AI analysis unavailable: missing ANTHROPIC_API_KEY."}

    if not extracted_text or not extracted_text.strip():
        return {
            "usage_summary": f"{org_name} hasn't uploaded a financial report yet, "
                              f"so we can't generate a usage summary for your donation."
        }

    trimmed_text = extracted_text[:15000]

    user_content = (
        f"NGO name: {org_name}\n"
        f"Donor's total contribution to this NGO: ₹{donation_amount:.2f} across {donation_count} donation(s)\n\n"
        f"Report text:\n\n{trimmed_text}"
    )

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
                "max_tokens": 512,
                "system": MONEY_USAGE_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_content}],
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        raw_reply = "\n".join(text_blocks)
        parsed = _extract_json(raw_reply)
        summary = str(parsed.get("usage_summary", "")).strip()
        return {"usage_summary": summary or "AI could not generate a usage summary from this report."}
    except requests.exceptions.RequestException as e:
        return {"usage_summary": f"Could not reach AI service: {e}"}
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return {"usage_summary": f"Could not parse AI response: {e}"}