import re

def calculate_score(text: str) -> dict:
    text_lower = text.lower()
    red_flags = []
    score = 100

    if "audit" not in text_lower:
        red_flags.append("No mention of audited financials")
        score -= 25

    admin_pct = extract_admin_percentage(text_lower)

    if "administrative" not in text_lower and "admin cost" not in text_lower:
        red_flags.append("No breakdown of administrative costs")
        score -= 20
    elif admin_pct is None:
        red_flags.append("Administrative costs mentioned but percentage unclear")
        score -= 10

    if admin_pct and admin_pct > 40:
        red_flags.append(f"High administrative cost: {admin_pct}%")
        score -= 20

    if "beneficiar" not in text_lower:
        red_flags.append("No mention of beneficiaries/impact reporting")
        score -= 15

    return {
        "transparency_score": max(score, 0),
        "red_flags": red_flags,
        "admin_cost_percentage": admin_pct
    }


def extract_admin_percentage(text: str):
    match = re.search(
        r"admin(?:istrative)?\s*(?:cost|expense)?s?\D{0,30}(\d{1,3}(?:\.\d+)?)\s?%",
        text,
        re.DOTALL
    )
    return float(match.group(1)) if match else None