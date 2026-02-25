


import sys
import json
import re
from app.llm import llm_wrapper
from app.tools import execute_tool
from app.embeddings import VectorStore, chunk_text
from app.data_loader import data_loader
from app.memory import get_session
from app.intent_router import detect_intent

_product_chunks = chunk_text(data_loader.product_text)
product_store = VectorStore(_product_chunks)


def log(msg: str):
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except OSError:
        with open("agent.log", "a") as f:
            f.write(msg + "\n")


def _extract_account_no(message: str, history: list) -> str:
    pattern = r'\b\d{6,12}\b'
    match = re.search(pattern, message)
    if match:
        return match.group()
    for msg in reversed(history[-10:]):
        content = str(msg.get("content", ""))
        m = re.search(pattern, content)
        if m:
            return m.group()
    return None


SMALL_SYSTEM = """You are a professional banking assistant for Globus Bank.
Respond conversationally and concisely in 2-3 sentences.
Do not give website navigation steps.
Do not make up procedures.
Only summarize the information provided to you.
"""

PRODUCT_SYSTEM = """You are a professional banking assistant for Globus Bank.
Answer questions about bank products using only the product information provided.
Be concise and helpful. Do not make up features or products not mentioned.
"""



# def handle_block_card(session_id: str, user_message: str, memory) -> str:
#     history = memory.get_history()
#     account_no = _extract_account_no(user_message, history)

#     # Step 1 — No account number yet
#     if not account_no:
#         response = "I can help you block your ATM card right away. Could you please provide your account number?"
#         memory.add_assistant(response)
#         return response

#     confirm_words = ["yes", "confirm", "proceed", "go ahead", "block it",
#                      "that one", "correct", "sure", "ok", "okay"]
#     is_confirming = any(word in user_message.lower() for word in confirm_words)

#     # Step 2 — If a card is already selected and customer is confirming, block it
#     selected_card = memory.get_state("selected_card")
#     if selected_card and is_confirming:
#         # result = execute_tool("block_card", {"card_id": selected_card["Card_Issuer"]})
#         result =execute_tool("block_card", {
#         "card_issuer": issuer,
#         "account_no": account_no
#         })
#         result_data = json.loads(result)
#         memory.set_state("current_flow", None)
#         memory.set_state("selected_card", None)
#         if result_data.get("success"):
#             response = (
#                 f"Done! Your {selected_card['Card_Issuer']} "
#                 f"{selected_card['Card_Type']} card has been successfully blocked. "
#                 f"Please visit any Globus Bank branch for a replacement."
#             )
#         else:
#             response = f"Unable to block the card. {result_data.get('message', 'Please contact support.')}"
#         memory.add_assistant(response)
#         return response

#     # Step 3 — Fetch linked cards
#     log(f"[Block Flow] Fetching cards for account: {account_no}")
#     cards_result = execute_tool("get_linked_cards", {"account_no": account_no})
#     log(f"[Cards Result] {cards_result}")

#     try:
#         cards_data = json.loads(cards_result)
#     except Exception as e:
#         log(f"[Error] {e}")
#         response = "I was unable to retrieve your card details. Please verify your account number and try again."
#         memory.add_assistant(response)
#         return response

#     if isinstance(cards_data, dict) and "error" in cards_data:
#         response = f"I couldn't find an account with number {account_no}. Please check and try again."
#         memory.add_assistant(response)
#         return response

#     cards = cards_data if isinstance(cards_data, list) else cards_data.get("cards", [])
#     active_cards = [c for c in cards if str(c.get("Status", "")).lower() == "active"]

#     if not active_cards:
#         memory.set_state("current_flow", None)
#         response = "There are no active cards on this account to block."
#         memory.add_assistant(response)
#         return response

#     # Step 4 — Single active card
#     if len(active_cards) == 1:
#         card = active_cards[0]
#         issuer = card.get("Card_Issuer", "Unknown")
#         card_type = card.get("Card_Type", "card")

#         if is_confirming:
#             result = execute_tool("block_card", {"card_id": issuer})
#             result_data = json.loads(result)
#             memory.set_state("current_flow", None)
#             memory.set_state("selected_card", None)
#             if result_data.get("success"):
#                 response = (
#                     f"Done! Your {issuer} {card_type} card has been successfully blocked. "
#                     f"Please visit any Globus Bank branch for a replacement."
#                 )
#             else:
#                 response = f"Unable to block the card. {result_data.get('message', 'Please contact support.')}"
#             memory.add_assistant(response)
#             return response
#         else:
#             # Save selected card in session state
#             memory.set_state("selected_card", card)
#             response = (
#                 f"I found one active card on your account — "
#                 f"a {issuer} {card_type} card. "
#                 f"Can you confirm you want to block this card?"
#             )
#             memory.add_assistant(response)
#             return response

#     # Step 5 — Multiple active cards, check if customer is selecting one
#     for card in active_cards:
#         issuer = card.get("Card_Issuer", "")
#         card_type = card.get("Card_Type", "card")

#         if issuer.lower() in user_message.lower():
#             # Save selected card in session state
#             memory.set_state("selected_card", card)
#             if is_confirming or any(w in user_message.lower() for w in ["block", "that", "this"]):
#                 result = execute_tool("block_card", {"card_id": issuer})
#                 result_data = json.loads(result)
#                 memory.set_state("current_flow", None)
#                 memory.set_state("selected_card", None)
#                 if result_data.get("success"):
#                     response = f"Done! Your {issuer} {card_type} card has been successfully blocked."
#                 else:
#                     response = f"Unable to block the card. {result_data.get('message', 'Please contact support.')}"
#                 memory.add_assistant(response)
#                 return response
#             else:
#                 response = f"You'd like to block your {issuer} {card_type} card. Can you confirm?"
#                 memory.add_assistant(response)
#                 return response

#     # Step 6 — List all active cards and ask customer to choose
#     card_list = "\n".join([
#         f"- {c.get('Card_Issuer')} {c.get('Card_Type')} card"
#         for c in active_cards
#     ])
#     response = (
#         f"I found {len(active_cards)} active cards on your account. "
#         f"Which card would you like to block?\n{card_list}"
#     )
#     memory.add_assistant(response)
#     return response

def handle_block_card(session_id: str, user_message: str, memory) -> str:
    history = memory.get_history()
    account_no = _extract_account_no(user_message, history)

    if not account_no:
        response = "I can help you block your ATM card right away. Could you please provide your account number?"
        memory.add_assistant(response)
        return response

    confirm_words = ["yes", "confirm", "proceed", "go ahead", "block it",
                     "that one", "correct", "sure", "ok", "okay"]
    is_confirming = any(word in user_message.lower() for word in confirm_words)

    # If a card was already selected and customer is confirming — block it
    selected_card = memory.get_state("selected_card")
    if selected_card and is_confirming:
        issuer = selected_card.get("Card_Issuer", "")      # ← define issuer here
        card_type = selected_card.get("Card_Type", "card") # ← define card_type here
        result = execute_tool("block_card", {
            "card_issuer": issuer,
            "account_no": account_no
        })
        result_data = json.loads(result)
        memory.set_state("current_flow", None)
        memory.set_state("selected_card", None)
        if result_data.get("success"):
            response = (
                f"Done! Your {issuer} {card_type} card has been successfully blocked. "
                f"Please visit any Globus Bank branch for a replacement."
            )
        else:
            response = f"Unable to block the card. {result_data.get('message', 'Please contact support.')}"
        memory.add_assistant(response)
        return response

    # Fetch linked cards
    log(f"[Block Flow] Fetching cards for account: {account_no}")
    cards_result = execute_tool("get_linked_cards", {"account_no": account_no})
    log(f"[Cards Result] {cards_result}")

    try:
        cards_data = json.loads(cards_result)
    except Exception as e:
        log(f"[Error] {e}")
        response = "I was unable to retrieve your card details. Please verify your account number and try again."
        memory.add_assistant(response)
        return response

    if isinstance(cards_data, dict) and "error" in cards_data:
        response = f"I couldn't find an account with number {account_no}. Please check and try again."
        memory.add_assistant(response)
        return response

    cards = cards_data if isinstance(cards_data, list) else cards_data.get("cards", [])
    active_cards = [c for c in cards if str(c.get("Status", "")).lower() == "active"]

    if not active_cards:
        memory.set_state("current_flow", None)
        response = "There are no active cards on this account to block."
        memory.add_assistant(response)
        return response

    # Single active card
    if len(active_cards) == 1:
        card = active_cards[0]
        issuer = card.get("Card_Issuer", "Unknown")        # ← defined here
        card_type = card.get("Card_Type", "card")

        if is_confirming:
            result = execute_tool("block_card", {
                "card_issuer": issuer,
                "account_no": account_no
            })
            result_data = json.loads(result)
            memory.set_state("current_flow", None)
            memory.set_state("selected_card", None)
            if result_data.get("success"):
                response = (
                    f"Done! Your {issuer} {card_type} card has been successfully blocked. "
                    f"Please visit any Globus Bank branch for a replacement."
                )
            else:
                response = f"Unable to block the card. {result_data.get('message', 'Please contact support.')}"
            memory.add_assistant(response)
            return response
        else:
            memory.set_state("selected_card", card)
            response = (
                f"I found one active card on your account — a {issuer} {card_type} card. "
                f"Can you confirm you want to block this card?"
            )
            memory.add_assistant(response)
            return response

    # Multiple active cards — check if customer is selecting one
    for card in active_cards:
        issuer = card.get("Card_Issuer", "")               # ← defined here
        card_type = card.get("Card_Type", "card")

        if issuer.lower() in user_message.lower():
            memory.set_state("selected_card", card)
            if is_confirming or any(w in user_message.lower() for w in ["block", "that", "this"]):
                result = execute_tool("block_card", {
                    "card_issuer": issuer,
                    "account_no": account_no
                })
                result_data = json.loads(result)
                memory.set_state("current_flow", None)
                memory.set_state("selected_card", None)
                if result_data.get("success"):
                    response = f"Done! Your {issuer} {card_type} card has been successfully blocked."
                else:
                    response = f"Unable to block the card. {result_data.get('message', 'Please contact support.')}"
                memory.add_assistant(response)
                return response
            else:
                response = f"You'd like to block your {issuer} {card_type} card. Can you confirm?"
                memory.add_assistant(response)
                return response

    # List all active cards and ask customer to choose
    card_list = "\n".join([
        f"- {c.get('Card_Issuer')} {c.get('Card_Type')} card"
        for c in active_cards
    ])
    response = (
        f"I found {len(active_cards)} active cards on your account. "
        f"Which card would you like to block?\n{card_list}"
    )
    memory.add_assistant(response)
    return response


def handle_account_query(session_id: str, user_message: str, memory) -> str:
    history = memory.get_history()
    account_no = _extract_account_no(user_message, history)

    if not account_no:
        response = "I can help you with your account details. Could you please provide your account number?"
        memory.add_assistant(response)
        return response

    result = execute_tool("get_account_summary", {"account_no": account_no})
    log(f"[Account] {result}")

    prompt = (
        f"The customer asked: '{user_message}'\n"
        f"Here is their account data: {result}\n"
        f"Summarize this for the customer in 3-4 sentences. "
        f"Include their balance and mention recent transactions if available. "
        f"Be professional and concise."
    )
    response = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=SMALL_SYSTEM
    )
    memory.add_assistant(response)
    return response


def handle_product_query(session_id: str, user_message: str, memory) -> str:
    rag_results = product_store.search(user_message, top_k=2)
    rag_context = "\n\n".join(rag_results) if rag_results else "No specific product info found."

    prompt = (
        f"The customer asked: '{user_message}'\n\n"
        f"Use only this product information to answer:\n{rag_context}\n\n"
        f"Give a helpful, concise answer in 3-5 sentences."
    )
    response = llm_wrapper.chat(
        [{"role": "user", "content": prompt}],
        system_prompt=PRODUCT_SYSTEM
    )
    memory.add_assistant(response)
    return response


def handle_general(session_id: str, user_message: str, memory) -> str:
    history = memory.get_history()
    response = llm_wrapper.chat(history, system_prompt=SMALL_SYSTEM)
    memory.add_assistant(response)
    return response


def run_agent(session_id: str, user_message: str) -> str:
    memory = get_session(session_id)
    memory.add_user(user_message)

    intent = detect_intent(user_message)
    current_flow = memory.get_state("current_flow")

    log(f"[Debug] intent={intent} | current_flow={current_flow} | message={user_message}")

    if intent == "block_card" or current_flow == "block_card":
        memory.set_state("current_flow", "block_card")
        return handle_block_card(session_id, user_message, memory)
    elif intent == "account_query":
        return handle_account_query(session_id, user_message, memory)
    elif intent == "product_query":
        return handle_product_query(session_id, user_message, memory)
    else:
        return handle_general(session_id, user_message, memory)
