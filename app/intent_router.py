import re

BLOCK_CARD_KEYWORDS = [
    "block", "stolen", "lost", "freeze", "cancel card",
    "stop card", "deactivate card", "block card", "block my card",
    "block atm", "lost card", "card stolen", "missing card"
]

# remove generic "account" from account keywords
ACCOUNT_KEYWORDS = [
    "balance", "transaction", "statement",
    "history", "how much", "account info",
    "account details", "last transaction", "recent transaction"
]

PRODUCT_KEYWORDS = [
    "loan", "savings", "investment", "product", "interest rate",
    "mortgage", "treasury", "bonds", "overdraft",
    "kiddies", "domiciliary", "current account", "non resident",
    "fixed deposit", "savings account", "commercial paper",
    "money market", "debit card", "vehicle loan", "business loan",
    "personal loan", "salary advance", "home extension", "working capital",
    "benefit", "features of", "what is a", "tell me about", "available product",
    "available loan", "available saving", "available investment",
]

ACCOUNT_NO_PATTERN = r"\b\d{6,12}\b"

def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(k in msg for k in BLOCK_CARD_KEYWORDS):
        return "block_card"

    has_account_no = re.search(ACCOUNT_NO_PATTERN, msg) is not None
    has_personal = any(p in msg for p in [" my ", " me ", " mine ", " i "])

    # product phrases that contain "account" but are NOT personal account queries
    product_account_phrases = ["savings account", "current account", "domiciliary account", "non resident"]

    if any(p in msg for p in product_account_phrases):
        return "product_query"

    # personal account intent: requires personal cue or explicit account number + account keywords
    if has_account_no or (has_personal and any(k in msg for k in ACCOUNT_KEYWORDS)):
        return "account_query"

    if any(k in msg for k in PRODUCT_KEYWORDS) or "offer" in msg or "options" in msg or "features" in msg:
        return "product_query"

    return "general"