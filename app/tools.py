# app/tools.py
import json
from app.data_loader import data_loader


TOOLS_SPEC = """
You have access to the following tools. To use a tool, respond with a JSON block like:
{"tool": "tool_name", "args": {"key": "value"}}

Available tools:
1. get_customer_info: Get customer profile details.
   Args: customer_id (string)

2. get_account_summary: Get account balance and recent transactions.
   Args: customer_id (string)

3. get_linked_cards: Get all ATM/debit cards linked to the account.
   Args: customer_id (string)

4. block_card: Block a specific ATM card.
   Args: card_id (string), reason (string)

5. search_products: Search product information (no args needed — use user's question directly).
   This is handled via RAG; do not call this as a tool.

If no tool is needed, respond conversationally.
"""


def execute_tool(tool_name: str, args: dict) -> str:
    if tool_name == "get_customer_info":
        customer = data_loader.get_customer(args["account_no"])
        if not customer:
            return "Customer not found."
        # Exclude sensitive internal keys if needed
        safe = {k: v for k, v in customer.items() if k != "pin"}
        return json.dumps(safe, default=str)

    elif tool_name == "get_account_summary":
        customer = data_loader.get_customer(args["account_no"])
        if not customer:
            return "Customer not found."
        transactions = data_loader.get_transactions(args["account_no"])
        recent = transactions[-5:]  # Last 5 transactions
        result = {
            "customer_name": customer.get("name"),
            "account_balance": customer.get("balance"),
            "recent_transactions": [
                {
                    "date": str(t["date"]),
                    "description": t.get("description"),
                    "amount": t.get("amount"),
                    "type": t.get("type")
                } for t in recent
            ]
        }
        return json.dumps(result, default=str)

    elif tool_name == "get_linked_cards":
        cards = data_loader.get_cards(args["account_no"])
        if not cards:
            return json.dumps({"error": "No cards found for this account."})
        formatted = [
            {
                "Card_Issuer": c.get("Card_Issuer"),
                "Card_Type": c.get("Card_Type"),
                "Status": c.get("Status"),
                "Card_Activation_Date": str(c.get("Card_Activation_Date", ""))
            } for c in cards
        ]
        
        return json.dumps(formatted, default=str)

    elif tool_name == "block_card":
        result = data_loader.block_card(args["card_id"])
        return json.dumps(result)

    return "Unknown tool."