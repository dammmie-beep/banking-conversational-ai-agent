# app/tools.py
import json
from typing import Any, Dict, Optional
from app.data_loader import data_loader


TOOLS_SPEC = """
You have access to the following tools. To use a tool, respond with a JSON block like:
{"tool": "tool_name", "args": {"key": "value"}}

Available tools:
1. get_customer_info: Get customer profile details.
   Args: account_no (string)

2. get_account_summary: Get account balance and recent transactions.
   Args: account_no (string)

3. get_linked_cards: Get all ATM/debit cards linked to the account.
   Args: account_no (string)

4. block_card: Block a specific ATM card.
   Args: card_issuer (string), account_no (string)

5. search_products: Search product information (no args needed — use user's question directly).
   This is handled via RAG; do not call this as a tool.

If no tool is needed, respond conversationally.
"""


def _ok(payload: Any) -> str:
    return json.dumps(payload, default=str)


def _err(message: str, extra: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {"error": message}
    if extra:
        payload.update(extra)
    return json.dumps(payload, default=str)


def execute_tool(tool_name: str, args: dict) -> str:
    """Executes a tool and ALWAYS returns a JSON string."""
    try:
        if tool_name == "get_customer_info":
            if "account_no" not in args:
                return _err("Missing required argument: account_no")
            customer = data_loader.get_customer(args["account_no"])
            if not customer:
                return _err("Customer not found.")
            safe = {k: v for k, v in customer.items() if k.lower() != "pin"}
            return _ok(safe)

        elif tool_name == "get_account_summary":
            if "account_no" not in args:
                return _err("Missing required argument: account_no")
            customer = data_loader.get_customer(args["account_no"])
            if not customer:
                return _err("Customer not found.")
            transactions = data_loader.get_transactions(args["account_no"]) or []
            recent = transactions[:5]
            result = {
                "customer_name": customer.get("Account_Name"),
                "account_balance": customer.get("Current_Balance"),
                "recent_transactions": [
                    {
                        "date": str(t.get("Transaction_Date", "")),
                        "description": t.get("Narration"),
                        "amount": t.get("Transaction_Amount"),
                        "type": t.get("Transaction_Type"),
                    }
                    for t in recent
                ],
            }
            return _ok(result)

        elif tool_name == "get_linked_cards":
            if "account_no" not in args:
                return _err("Missing required argument: account_no")
            cards = data_loader.get_cards(args["account_no"]) or []
            if not cards:
                return _err("No cards found for this account.")
            formatted = [
                {
                    "Card_Issuer": c.get("Card_Issuer"),
                    "Card_Type": c.get("Card_Type"),
                    "Status": c.get("Status"),
                    "Card_Activation_Date": str(c.get("Card_Activation_Date", "")),
                }
                for c in cards
            ]
            return _ok(formatted)

        elif tool_name == "block_card":
            if "account_no" not in args:
                return _err("Missing required argument: account_no")
            if "card_issuer" not in args:
                return _err("Missing required argument: card_issuer")
            result = data_loader.block_card(args["card_issuer"], args["account_no"])
            return _ok(result)

        return _err("Unknown tool.", {"tool_name": tool_name})

    except Exception as e:
        return _err("Tool execution error.", {"details": str(e), "tool_name": tool_name})
