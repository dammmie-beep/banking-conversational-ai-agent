import sys
import json
import re
from typing import Any, Dict, Optional

from app.llm import llm_wrapper
from app.tools import execute_tool
from app.embeddings import VectorStore, chunk_text
from app.data_loader import data_loader
from app.memory import get_session

# -----------------------------
# Build product vector store
# -----------------------------
_product_chunks = chunk_text(data_loader.product_text)
product_store = VectorStore(_product_chunks)


# -----------------------------
# Logging
# -----------------------------
def log(msg: str):
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except OSError:
        with open("agent.log", "a") as f:
            f.write(msg + "\n")


# -----------------------------
# Regex helpers
# -----------------------------
ACCOUNT_PATTERN = r"\b\d{6,12}\b"


def extract_account_no(message, history):
    match = re.search(ACCOUNT_PATTERN, message or "")
    if match:
        return match.group()
    for msg in reversed(history[-10:]):
        m = re.search(ACCOUNT_PATTERN, msg.get("content", "") or "")
        if m:
            return m.group()
    return None


def is_confirmation(message):
    confirm_words = ["yes", "confirm", "proceed", "go ahead", "correct", "sure", "ok", "okay"]
    msg = (message or "").lower()
    return any(w in msg for w in confirm_words)


def _extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return None


def _looks_like_refusal(text: str) -> bool:
    t = (text or "").lower()
    refusal_markers = [
        "unable", "can't", "cannot", "not able", "i'm sorry",
        "personal banking", "i can only provide", "cannot assist",
        "i don't have access", "i do not have access",
    ]
    return any(m in t for m in refusal_markers)


# -----------------------------
# System prompts
# -----------------------------
BASE_SYSTEM = """You are a professional banking assistant for Globus Bank.
Respond conversationally in 2–3 sentences.
Do not invent procedures.
Use only the information provided."""

PRODUCT_SYSTEM = """You are a banking assistant for Globus Bank.
Answer using ONLY the provided product information.
If the user asks about one specific product, answer only about that product.
Do NOT list multiple products unless the user asks for options or a comparison.
If the product information does not contain the answer, say:
"I don't have that information in the provided product details."
Do NOT guess or invent."""

ACCOUNT_SYSTEM = """You are a professional banking assistant for Globus Bank.
Answer using ONLY the provided account facts.
Do not refuse or mention policy limitations.
If details are missing, say what is missing and ask a short follow-up.
Keep your answer to 2–4 sentences."""


# -----------------------------
# Routing
# -----------------------------
# LLM router prompt — only called for genuinely ambiguous messages
ROUTER_SYSTEM = """You are the ROUTER for an offline banking assistant.

Choose the next action for the user message.

Actions:
- "account_query": balance, transactions, statement, account info.
- "block_card": lost/stolen/missing card, freeze/block/cancel/deactivate.
- "product_query": questions about bank products, account types, loans, interest rates, features.
- "general": ONLY greetings or chit-chat with no information request.

RULES:
- Return ONLY valid JSON. No extra text.
- Do NOT answer the user.
- For any question asking for information, choose product_query unless clearly account_query.
- If message contains an account number, include "account_no".

Return JSON:
{"action":"account_query|block_card|product_query|general","account_no":"optional"}
"""


def route_with_llm(user_message: str, memory) -> Dict[str, Any]:
    """
    All routing goes through the LLM. Qwen2.5-3B reliably returns valid JSON
    so keyword heuristics are no longer needed.
    """
    history = memory.get_history()
    detected_account_no = (
        memory.get_state("account_no")
        or extract_account_no(user_message, history)
    )

    current_flow = memory.get_state("current_flow")
    prompt = f"""State: {{"current_flow": {json.dumps(current_flow)}}}
User message: {user_message}"""

    raw = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=ROUTER_SYSTEM,
        max_tokens=64,
    )

    log(f"[Router] LLM raw={raw[:80]}")
    parsed = _extract_first_json_object(raw)

    if parsed and parsed.get("action") in {"account_query", "block_card", "product_query", "general"}:
        action = parsed["action"]
        account_no = parsed.get("account_no") or detected_account_no
        out: Dict[str, Any] = {"action": action}
        if account_no:
            out["account_no"] = account_no
        log(f"[Router] action={action}")
        return out

    # Last-resort fallback if LLM output is unparseable
    log("[Router] LLM parse failed, falling back")
    if detected_account_no:
        return {"action": "account_query", "account_no": detected_account_no}
    return {"action": "general"}


# -----------------------------
# Block Card Flow
# -----------------------------
def handle_block_card(user_message, memory):
    history = memory.get_history()

    # Prefer account_no persisted in state (set when flow first started)
    account_no = (
        memory.get_state("block_card_account_no")
        or memory.get_state("account_no")
        or extract_account_no(user_message, history)
    )

    if not account_no:
        response = "Please provide your account number so I can locate your cards."
        memory.add_assistant(response)
        return response

    # Persist for subsequent turns in this flow
    memory.set_state("block_card_account_no", account_no)

    selected_card = memory.get_state("selected_card")

    # Fast path: user is confirming a previously selected card
    if selected_card and is_confirmation(user_message):
        issuer = selected_card["Card_Issuer"]
        session_blocked = memory.get_state("session_blocked_cards") or set()
        result = data_loader.block_card(issuer, account_no, session_blocked)

        memory.set_state("selected_card", None)
        memory.set_state("current_flow", None)
        memory.set_state("block_card_account_no", None)

        if result.get("success"):
            # Track the blocked card in session state only — resets on new session
            session_blocked.add(issuer)
            memory.set_state("session_blocked_cards", session_blocked)
            response = f"Your {issuer} card has been successfully blocked."
        else:
            response = result.get("message", "I couldn't block the card right now. Please contact support.")

        memory.add_assistant(response)
        return response

    # Fetch cards
    cards_result = execute_tool("get_linked_cards", {"account_no": account_no})
    try:
        cards = json.loads(cards_result)
    except Exception:
        response = "I couldn't retrieve your linked cards right now. Please try again."
        memory.add_assistant(response)
        return response

    if isinstance(cards, dict) and cards.get("error"):
        response = cards["error"]
        memory.add_assistant(response)
        return response

    # Filter: exclude DB-blocked cards AND session-blocked cards
    session_blocked = memory.get_state("session_blocked_cards") or set()
    active_cards = [
        c for c in cards
        if str(c.get("Status", "")).lower() == "active"
        and c.get("Card_Issuer") not in session_blocked
    ]

    if not active_cards:
        response = "There are no active cards linked to this account."
        memory.add_assistant(response)
        return response

    # Single active card
    if len(active_cards) == 1:
        card = active_cards[0]
        memory.set_state("selected_card", card)
        response = f"You have one active card: {card['Card_Issuer']} ({card['Card_Type']}). Should I block it?"
        memory.add_assistant(response)
        return response

    # Multiple cards — check if user named an issuer in their message
    for card in active_cards:
        issuer = card.get("Card_Issuer", "")
        if issuer and issuer.lower() in (user_message or "").lower():
            memory.set_state("selected_card", card)
            response = f"You want to block your {issuer} card. Please confirm with 'yes' to proceed."
            memory.add_assistant(response)
            return response

    card_list = "\n".join([f"- {c['Card_Issuer']} ({c['Card_Type']})" for c in active_cards])
    response = f"You have multiple active cards. Which one would you like to block?\n{card_list}"
    memory.add_assistant(response)
    return response


# -----------------------------
# Account queries
# -----------------------------
def handle_account_query(user_message, memory):
    history = memory.get_history()
    account_no = (
        memory.get_state("account_no")
        or extract_account_no(user_message, history)
    )

    if not account_no:
        response = "Please provide your account number so I can check your account."
        memory.add_assistant(response)
        return response

    # Persist for follow-up questions in same session
    memory.set_state("account_no", account_no)

    result = execute_tool("get_account_summary", {"account_no": account_no})
    try:
        data = json.loads(result)
    except Exception:
        response = "I couldn't retrieve your account details right now. Please confirm the account number and try again."
        memory.add_assistant(response)
        return response

    if isinstance(data, dict) and data.get("error"):
        response = data["error"]
        memory.add_assistant(response)
        return response

    name = data.get("customer_name") or "Customer"
    balance = data.get("account_balance", "N/A")
    txs = data.get("recent_transactions") or []

    tx_lines = [
        f"- {t.get('date','')}: {t.get('type','')} {t.get('amount','')} ({t.get('description','')})"
        for t in txs[:5]
    ]
    tx_block = "\n".join(tx_lines) if tx_lines else "No recent transactions found."

    prompt = f"""Customer question:
{user_message}

Account facts (authoritative):
Name: {name}
Account Number: {account_no}
Balance: {balance}
Recent Transactions:
{tx_block}

Answer the customer in 2–4 sentences using ONLY the facts above."""

    llm_response = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=ACCOUNT_SYSTEM,
    )

    if _looks_like_refusal(llm_response):
        if tx_lines:
            response = f"{name}, your current balance is {balance}. Your recent transactions:\n{tx_block}"
        else:
            response = f"{name}, your current balance is {balance}. No recent transactions found on this account."
        memory.add_assistant(response)
        return response

    memory.add_assistant(llm_response)
    return llm_response


# -----------------------------
# Product queries (RAG)
# -----------------------------
def handle_product_query(user_message: str, memory) -> str:
    docs = product_store.search(user_message, top_k=3, min_score=0.0)
    log(f"[ProductQuery] retrieved {len(docs)} chunks: {[d[:60] for d in docs]}")

    if not docs:
        response = "I don't have that information in the provided product details."
        memory.add_assistant(response)
        return response

    context = "\n\n".join(docs)

    prompt = f"""Customer asked:
{user_message}

Use ONLY the product information below to answer.

Product information:
{context}

Give a helpful, concise answer in 3–5 sentences."""

    response = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=PRODUCT_SYSTEM,
    )
    memory.add_assistant(response)
    return response


# -----------------------------
# General / conversational
# -----------------------------
def handle_general(memory):
    history = memory.get_history()
    response = llm_wrapper.chat(history, system_prompt=BASE_SYSTEM)
    memory.add_assistant(response)
    return response


# -----------------------------
# Main Agent
# -----------------------------
def run_agent(session_id: str, user_message: str) -> str:
    memory = get_session(session_id)
    memory.add_user(user_message)

    current_flow = memory.get_state("current_flow")

    # Continue an in-progress multi-turn flow (card blocking)
    if current_flow == "block_card":
        log("[Agent] continuing flow=block_card")
        return handle_block_card(user_message, memory)

    decision = route_with_llm(user_message, memory)
    action = decision.get("action")

    log(f"[Agent] action={action} decision={decision}")

    if action == "block_card":
        memory.set_state("current_flow", "block_card")
        return handle_block_card(user_message, memory)

    if action == "account_query":
        return handle_account_query(user_message, memory)

    if action == "product_query":
        return handle_product_query(user_message, memory)

    return handle_general(memory)
