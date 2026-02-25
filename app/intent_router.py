BLOCK_CARD_KEYWORDS = [
    "block", "stolen", "lost", "freeze", "cancel card",
    "stop card", "deactivate card", "block card", "block my card",
    "block atm", "lost card", "card stolen", "missing card"
]

ACCOUNT_KEYWORDS = [
    "balance", "account", "transaction", "statement",
    "history", "how much", "my account", "account info",
    "account details", "last transaction", "recent transaction"
]

PRODUCT_KEYWORDS = [
    "loan", "savings", "investment", "product", "interest rate",
    "mortgage", "debit card", "treasury", "bonds", "overdraft",
    "kiddies", "domiciliary", "current account", "non resident"
]


def detect_intent(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in BLOCK_CARD_KEYWORDS):
        return "block_card"
    if any(k in msg for k in ACCOUNT_KEYWORDS):
        return "account_query"
    if any(k in msg for k in PRODUCT_KEYWORDS):
        return "product_query"
    return "general"