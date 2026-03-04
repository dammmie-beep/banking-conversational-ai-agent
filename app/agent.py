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
    confirm_words = [
        "yes", "confirm", "proceed", "go ahead",
        "correct", "sure", "ok", "okay"
    ]
    msg = (message or "").lower()
    return any(w in msg for w in confirm_words)


def _extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    SmolLM may add extra words. We extract the first {...} blob and parse it.
    """
    if not text:
        return None

    # Try direct parse first
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Find first JSON object
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None

    try:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None

    return None


def _looks_like_refusal(text: str) -> bool:
    t = (text or "").lower()
    refusal_markers = [
        "unable", "can't", "cannot", "not able", "i'm sorry",
        "personal banking", "i can only provide", "cannot assist",
        "i don’t have access", "i do not have access"
    ]
    return any(m in t for m in refusal_markers)


# -----------------------------
# System prompts
# -----------------------------
BASE_SYSTEM = """
You are a professional banking assistant for Globus Bank.
Respond conversationally in 2–3 sentences.
Do not invent procedures.
Use only the information provided.
"""

PRODUCT_SYSTEM = """You are a banking assistant for Globus Bank.
You MUST answer using ONLY the provided product information.
If the user asks about ONE specific product, answer ONLY about that product.
Do NOT list multiple products unless the user asks for options/comparison.
If the product information does not contain the answer, say:
"I don’t have that information in the provided product details."
Do NOT guess or invent."""


# -----------------------------
# LLM routing (NO keyword intent router)
# -----------------------------
ROUTER_SYSTEM = """You are the ROUTER for an offline banking assistant.

Choose the next action for the user message.

Actions:
- "account_query": balance, transactions, statement, account info/summary.
- "block_card": lost/stolen/missing card, freeze/block/cancel/deactivate card.
- "product_query": ANY question about bank products, account types, loans, interest rates, features, requirements, or general bank offerings.
- "general": ONLY greetings or chit-chat with no request for information. Examples: "hi", "hello", "good morning", "thanks".

RULES:
- Return ONLY valid JSON. No extra text.
- Do NOT answer the user.
- "general" must be used ONLY for pure greetings/chitchat.
- For any question asking for information, choose product_query unless it is clearly account_query or block_card.
- If message contains an account number, include "account_no".

Return JSON:
{"action":"account_query|block_card|product_query|general","account_no":"optional","card_issuer":"optional"}
"""

def route_with_llm(user_message: str, memory) -> Dict[str, Any]:
    history = memory.get_history()
    msg = (user_message or "").lower()

    
    card_incident = any(w in msg for w in ["lost", "stolen", "missing", "block", "freeze", "deactivate", "cancel"])
    if "card" in msg and card_incident:
        return {"action": "block_card"}

    # Pre-extract account number locally (robust even if SmolLM fails JSON)
    detected_account_no = extract_account_no(user_message, history)

    # Provide a compact state summary (helps for multi-step card blocking)
    current_flow = memory.get_state("current_flow")
    selected_card = memory.get_state("selected_card")
    state_summary = {
        "current_flow": current_flow,
        "awaiting_block_confirmation": bool(selected_card),
        "selected_card_issuer": (selected_card.get("Card_Issuer") if isinstance(selected_card, dict) else None),
    }

    prompt = f"""
Conversation (most recent last):
{json.dumps(history[-8:], ensure_ascii=False)}

State:
{json.dumps(state_summary, ensure_ascii=False)}

User message:
{user_message}
"""

    raw = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=ROUTER_SYSTEM
    )

    parsed = _extract_first_json_object(raw)

    # ✅ SmolLM-safe fallback:
    # If routing JSON fails but an account number exists, go to account tools.
    if not parsed or "action" not in parsed:
        if detected_account_no:
            return {"action": "account_query", "account_no": detected_account_no}
        return {"action": "general"}

    # Normalize
    action = str(parsed.get("action", "")).strip().lower()
    account_no = parsed.get("account_no") or detected_account_no
    card_issuer = parsed.get("card_issuer")

    if action not in {"account_query", "block_card", "product_query", "general"}:
        action = "product_query"

    # ✅ Hard override:
    # If an account number is present, never allow product/general.
    if account_no and action in {"product_query", "general"}:
        action = "account_query"

    out = {"action": action}
    if account_no:
        out["account_no"] = account_no
    if card_issuer:
        out["card_issuer"] = card_issuer
    return out


# -----------------------------
# Block Card Flow (unchanged logic, but triggered by LLM routing/state)
# -----------------------------
def handle_block_card(user_message, memory):

    history = memory.get_history()
    account_no = extract_account_no(user_message, history)

    if not account_no:
        response = "Please provide your account number so I can locate your cards."
        memory.add_assistant(response)
        return response

    cards_result = execute_tool("get_linked_cards", {"account_no": account_no})

    # Always parse JSON
    try:
        cards = json.loads(cards_result)
    except Exception:
        response = "I couldn’t retrieve your linked cards right now. Please try again."
        memory.add_assistant(response)
        return response

    # Tool-level error
    if isinstance(cards, dict) and cards.get("error"):
        response = cards["error"]
        memory.add_assistant(response)
        return response

    active_cards = [
        c for c in cards
        if str(c.get("Status", "")).lower() == "active"
    ]

    if not active_cards:
        response = "There are no active cards linked to this account."
        memory.add_assistant(response)
        return response

    selected_card = memory.get_state("selected_card")

    # Confirm blocking
    if selected_card and is_confirmation(user_message):
        issuer = selected_card["Card_Issuer"]

        result = execute_tool(
            "block_card",
            {"card_issuer": issuer, "account_no": account_no}
        )

        try:
            data = json.loads(result)
        except Exception:
            data = {"success": False}

        memory.set_state("selected_card", None)
        memory.set_state("current_flow", None)

        if data.get("success"):
            response = f"Your {issuer} card has been successfully blocked."
        else:
            response = "I couldn't block the card right now. Please contact support."

        memory.add_assistant(response)
        return response

    # Single card
    if len(active_cards) == 1:
        card = active_cards[0]
        issuer = card["Card_Issuer"]

        memory.set_state("selected_card", card)
        response = f"You have one active card: {issuer}. Should I block it?"
        memory.add_assistant(response)
        return response

    # Multiple cards — allow issuer selection from user text
    for card in active_cards:
        issuer = card["Card_Issuer"]
        if issuer and issuer.lower() in (user_message or "").lower():
            memory.set_state("selected_card", card)
            response = f"You want to block your {issuer} card. Please confirm."
            memory.add_assistant(response)
            return response

    card_list = "\n".join([f"- {c['Card_Issuer']} {c['Card_Type']}" for c in active_cards])

    response = (
        f"You have multiple active cards.\n"
        f"Which one would you like to block?\n{card_list}"
    )
    memory.add_assistant(response)
    return response


# -----------------------------
# Account queries (kept from your improved version)
# -----------------------------
def handle_account_query(user_message, memory):
    history = memory.get_history()
    account_no = extract_account_no(user_message, history)

    if not account_no:
        response = "Please provide your account number so I can check your account."
        memory.add_assistant(response)
        return response

    result = execute_tool("get_account_summary", {"account_no": account_no})

    try:
        data = json.loads(result)
    except Exception:
        response = "I couldn’t retrieve your account details right now. Please confirm the account number and try again."
        memory.add_assistant(response)
        return response

    if isinstance(data, dict) and data.get("error"):
        response = data["error"]
        memory.add_assistant(response)
        return response

    name = data.get("customer_name") or "Customer"
    balance = data.get("account_balance", "N/A")
    txs = data.get("recent_transactions") or []

    tx_lines = []
    for t in txs[:5]:
        tx_lines.append(
            f"- {t.get('date','')}: {t.get('type','')} {t.get('amount','')} ({t.get('description','')})"
        )
    tx_block = "\n".join(tx_lines) if tx_lines else "No recent transactions found."

    ACCOUNT_SYSTEM = """You are a professional banking assistant for Globus Bank.
You MUST answer using ONLY the provided account facts.
Do not refuse or mention policy limitations.
If details are missing, say what is missing and ask a short follow-up.
Keep it to 2–4 sentences.
"""

    prompt = f"""
Customer question:
{user_message}

Account facts (authoritative):
Name: {name}
Account Number: {account_no}
Balance: {balance}
Recent Transactions:
{tx_block}

Task:
Answer the customer in 2–4 sentences using ONLY the facts above.
"""

    llm_response = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=ACCOUNT_SYSTEM
    )

    if _looks_like_refusal(llm_response):
        # Deterministic fallback
        if tx_lines:
            response = f"{name}, your current balance is {balance}. Your recent transactions are:\n{tx_block}"
        else:
            response = f"{name}, your current balance is {balance}. I couldn’t find recent transactions on this account."
        memory.add_assistant(response)
        return response

    memory.add_assistant(llm_response)
    return llm_response


# -----------------------------
# Product queries (RAG)
# -----------------------------
def handle_product_query(user_message: str, memory) -> str:
    docs = product_store.search(user_message, top_k=3, min_score=0.28)
    

    # Fallback: if user asked about a specific product keyword, filter to matching chunks
    q = (user_message or "").lower()
    focus_terms = []
    for term in ["savings", "domiciliary", "kiddies", "current account", "non resident", "overdraft", "mortgage", "loan"]:
        if term in q:
            focus_terms.append(term)

    if focus_terms:
        filtered = []
        for d in docs:
            dl = d.lower()
            if any(t in dl for t in focus_terms):
                filtered.append(d)
        if filtered:
            docs = filtered[:5]
        else:
            # last-resort: scan all chunks for literal match
            literal = [c for c in _product_chunks if any(t in c.lower() for t in focus_terms)]
            if literal:
                docs = literal[:5]



    if not docs:
        response = "I don’t have that information in the provided product details."
        memory.add_assistant(response)
        return response

    context = "\n\n".join(docs) if docs else "No specific product info found."

    prompt = f"""
Customer asked:
{user_message}

Use ONLY this product information:

{context}

Answer clearly.
Give a helpful, concise answer in 3-5 sentences.
"""

    response = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=PRODUCT_SYSTEM
    )

    memory.add_assistant(response)
    return response


# -----------------------------
# General questions
# -----------------------------
def handle_general(memory):
    history = memory.get_history()
    response = llm_wrapper.chat(history, system_prompt=BASE_SYSTEM)
    memory.add_assistant(response)
    return response


# -----------------------------
# Main Agent (LLM-routed)
# -----------------------------
def run_agent(session_id, user_message):
    memory = get_session(session_id)
    memory.add_user(user_message)

    current_flow = memory.get_state("current_flow")

    # Continue existing flow (block card confirmation/selection)
    if current_flow == "block_card":
        log(f"[Agent] continuing flow=block_card")
        return handle_block_card(user_message, memory)

    # Decide action using SmolLM (no keywords router)
    decision = route_with_llm(user_message, memory)
    
    action = decision.get("action")
    msg = (user_message or "").strip().lower()

    
    if action == "general" and ("?" in msg or msg.startswith(("what", "how", "tell", "explain", "describe", "which"))):
        action = "product_query"
        decision["action"] = "product_query"
        
    print("DEBUG_DECISION:", decision)
    log(f"[Agent] action={action} decision={decision}")

    if action == "block_card":
        memory.set_state("current_flow", "block_card")
        return handle_block_card(user_message, memory)

    if action == "account_query":
        return handle_account_query(user_message, memory)

    if action == "product_query":
        return handle_product_query(user_message, memory)

    return handle_general(memory)