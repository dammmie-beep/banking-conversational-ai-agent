# app/data_loader.py
import pandas as pd
from config import Config

class DataLoader:
    def __init__(self):
        self.customers = {}
        self.transactions = {}
        self.cards = {}
        self.product_text = ""
        self._load()

    def _load(self):
        # ── Excel ──────────────────────────────────────────────
        xls = pd.ExcelFile(Config.EXCEL_PATH)

        # Customer sheet
        df_cust = pd.read_excel(xls, sheet_name="Customer")
        for _, row in df_cust.iterrows():
            cid = str(row["Account_No"])
            self.customers[cid] = row.to_dict()

        # Transaction sheet
        df_tx = pd.read_excel(xls, sheet_name="Transaction")
        df_tx["date"] = pd.to_datetime(df_tx["Transaction_Date"], format="%d/%m/%Y %H:%M:%S")
        for _, row in df_tx.iterrows():
            cid = str(row["Account_No"])
            self.transactions.setdefault(cid, []).append(row.to_dict())

        # Card sheet
        df_card = pd.read_excel(xls, sheet_name="Card")
        for _, row in df_card.iterrows():
            cid = str(row["Account_No"])
            self.cards.setdefault(cid, []).append(row.to_dict())

        # ── Product text file ──────────────────────────────────
        with open(Config.PRODUCTS_PATH, "r") as f:
            self.product_text = f.read()

    def get_customer(self, customer_id: str):
        return self.customers.get(customer_id)

    def get_transactions(self, customer_id: str):
        return self.transactions.get(customer_id, [])

    def get_cards(self, customer_id: str):
        return self.cards.get(customer_id, [])
    def block_card(self, card_identifier: str):
        """Block card by Card_Issuer name e.g. 'Visa' or 'Afrigo'"""
        for cid, card_list in self.cards.items():
            for card in card_list:
                issuer = str(card.get("Card_Issuer", "")).lower()
                if issuer == card_identifier.lower():
                    if str(card.get("Status", "")).lower() == "blocked":
                        return {"success": False, "message": "Card is already blocked."}
                    card["Status"] = "Blocked"
                    return {
                        "success": True,
                        "message": f"{card.get('Card_Issuer')} {card.get('Card_Type')} card has been successfully blocked."
                    }
        return {"success": False, "message": "Card not found."}

    # def block_card(self, card_id: str):
    #     """
    #     In production, this writes to a database.
    #     Here we mutate in-memory state and return result.
    #     """
    #     for cid, card_list in self.cards.items():
    #         for card in card_list:
    #             if str(card.get("card_id")) == str(card_id):
    #                 if card.get("status", "").lower() == "blocked":
    #                     return {"success": False, "message": "Card is already blocked."}
    #                 card["status"] = "Blocked"
    #                 return {
    #                     "success": True,
    #                     "message": f"Card ending in {str(card['card_number'])[-4:]} has been successfully blocked."
    #                 }
    #     return {"success": False, "message": "Card not found."}


# Singleton — load once at startup
data_loader = DataLoader()