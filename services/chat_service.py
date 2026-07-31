import os
import random
from dotenv import load_dotenv
import google.generativeai as genai

from google.generativeai import types


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-3.6-flash"

_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# Basic project info points
PROJECT_INFO = [
    "✔ Track NGO transparency scores",
    "✔ Upload and analyze financial reports",
    "✔ Create and manage fundraising campaigns",
    "✔ Record donations and download certificates",
    "✔ Stay updated with NGO news",
]

FAQS = {
    "donation": "You can donate to any NGO or campaign using the 'Donate' button on the donor dashboard or Campaigns page.",
    "transparency": "Our platform analyzes NGO financial reports with AI to generate transparency scores.",
    "campaign": "Campaigns are created by NGOs and appear on the Campaigns page for donors right away.",
    "report": "NGOs upload PDF financial reports, which are analyzed to detect red flags and calculate transparency scores.",
    "certificate": "After donating, you can download a transparency certificate from your dashboard.",
}

SYSTEM_PROMPT = """You are TransparencyBot, the assistant for a Donation Transparency
Checker platform. You ONLY answer questions about this platform and general
donation/NGO-transparency topics. You must not answer unrelated general-knowledge
questions (coding help, trivia, current events, etc.) — politely redirect instead.

Platform features you can explain:
- Donors can search NGOs and see AI-generated transparency scores (0-100) with
  red flags, based on uploaded financial reports.
- NGOs upload PDF financial reports; AI analyzes them for transparency issues
  (missing audit info, undisclosed admin costs, no beneficiary/impact reporting, etc.)
- NGOs can create fundraising campaigns with a title, description, and goal amount.
  Campaigns appear immediately on the donor-facing Campaigns page — there is no
  separate admin approval step.
- Donors can record a general donation to an NGO, or donate directly to a specific
  campaign, and receive a transaction ID.
- The platform shows an NGO news sidebar for NGO users.

Tone: friendly, concise, plain language. Keep replies SHORT — 1-3 sentences or
a few short bullet points at most, since this runs inside a small chat widget.
If you don't know something specific about this platform's exact behavior, say
so honestly rather than guessing.
"""


def _is_greeting(text: str) -> bool:
    words = text.lower().strip().strip("!.?").split()
    return any(w in ("hi", "hello", "hey", "hola") for w in words)


def _greeting_response() -> str:
    intro = "👋 Hi, I'm TransparencyBot!\n\n"
    points = "\n".join(PROJECT_INFO)
    return f"{intro}Here's what I can help with:\n{points}\n\nWhat would you like to know?"


def _rule_based_response(query: str) -> str:
    """Keyword-matching fallback used when Gemini is unavailable."""
    if _is_greeting(query):
        return _greeting_response()

    query_lower = query.lower()
    for keyword, answer in FAQS.items():
        if keyword in query_lower:
            return answer

    fallback_responses = [
        "I can only answer questions about this donation transparency platform.",
        "Please ask me about donations, campaigns, reports, or transparency scores.",
        "Sorry, I don't have information on that. Try asking about how to donate or how reports work.",
    ]
    return random.choice(fallback_responses)


def get_chatbot_response(query: str, history: list | None = None) -> str:
    """
    Returns a chatbot reply. Uses Gemini if configured; otherwise falls back
    to simple keyword-based FAQ matching so the chat still works with zero setup.

    A plain greeting ("hi"/"hello"/etc) always shows the project-info intro
    directly, whether or not Gemini is configured — no need to burn an API
    call on something this simple.

    history: optional list of {"role": "user"|"model", "text": str} from
    earlier turns in the conversation, oldest first.
    """
    if _is_greeting(query) and not (history and len(history) > 0):
        return _greeting_response()

    if not _client:
        return _rule_based_response(query)

    try:
        contents = []
        for turn in (history or []):
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=turn.get("text", ""))])
            )
        contents.append(types.Content(role="user", parts=[types.Part(text=query)]))

        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=300,
                temperature=0.4,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
        )
        if response.text and response.text.strip():
            return response.text.strip()
        return _rule_based_response(query)

    except Exception:
        # Any API hiccup silently falls back rather than breaking the chat
        return _rule_based_response(query)