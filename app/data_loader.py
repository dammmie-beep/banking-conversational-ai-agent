# # app/data_loader.py
# import pandas as pd
# from config import Config

# class DataLoader:
#     def __init__(self):
#         self.customers = {}
#         self.transactions = {}
#         self.cards = {}
#         self.product_text = ""
#         self._load()

#     def _load(self):
#         # ── Excel ──────────────────────────────────────────────
#         xls = pd.ExcelFile(Config.EXCEL_PATH)

#         # Customer sheet
#         df_cust = pd.read_excel(xls, sheet_name="Customer")
#         for _, row in df_cust.iterrows():
#             cid = str(row["Account_No"])
#             self.customers[cid] = row.to_dict()

#         # Transaction sheet
#         df_tx = pd.read_excel(xls, sheet_name="Transaction")
#         df_tx["date"] = pd.to_datetime(df_tx["Transaction_Date"], format="%d/%m/%Y %H:%M:%S")
#         for _, row in df_tx.iterrows():
#             cid = str(row["Account_No"])
#             self.transactions.setdefault(cid, []).append(row.to_dict())

#         # Card sheet
#         df_card = pd.read_excel(xls, sheet_name="Card")
#         for _, row in df_card.iterrows():
#             cid = str(row["Account_No"])
#             self.cards.setdefault(cid, []).append(row.to_dict())

#         # ── Product text file ──────────────────────────────────
#         with open(Config.PRODUCTS_PATH, "r") as f:
#             self.product_text = f.read()

#     def get_customer(self, customer_id: str):
#         return self.customers.get(customer_id)

#     def get_transactions(self, customer_id: str):
#         return self.transactions.get(customer_id, [])

#     def get_cards(self, customer_id: str):
#         return self.cards.get(customer_id, [])
#     def block_card(self, card_identifier: str):
#         """Block card by Card_Issuer name e.g. 'Visa' or 'Afrigo'"""
#         for cid, card_list in self.cards.items():
#             for card in card_list:
#                 issuer = str(card.get("Card_Issuer", "")).lower()
#                 if issuer == card_identifier.lower():
#                     if str(card.get("Status", "")).lower() == "blocked":
#                         return {"success": False, "message": "Card is already blocked."}
#                     card["Status"] = "Blocked"
#                     return {
#                         "success": True,
#                         "message": f"{card.get('Card_Issuer')} {card.get('Card_Type')} card has been successfully blocked."
#                     }
#         return {"success": False, "message": "Card not found."}



# # Singleton — load once at startup
# data_loader = DataLoader()

# app/data_loader.py
import sqlite3
import json
from config import Config


class DataLoader:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.product_text = ""
        self._load_products()

    def _get_conn(self):
        """Get a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # allows dict-like access
        return conn

    def _load_products(self):
        with open(Config.PRODUCTS_PATH, "r") as f:
            self.product_text = f.read()

    def get_customer(self, account_no: str):
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM Customer WHERE Account_No = ?",
                (account_no,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_transactions(self, account_no: str):
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """SELECT * FROM Transaction
                   WHERE Account_No = ?
                   ORDER BY Transaction_Date DESC""",
                (account_no,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_cards(self, account_no: str):
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM Card WHERE Account_No = ?",
                (account_no,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def block_card(self, card_issuer: str, account_no: str):
        conn = self._get_conn()
        try:
            # Check current status first
            cursor = conn.execute(
                """SELECT * FROM Card
                   WHERE Account_No = ? AND Card_Issuer = ?""",
                (account_no, card_issuer)
            )
            card = cursor.fetchone()

            if not card:
                return {"success": False, "message": "Card not found."}

            if str(card["Status"]).lower() == "blocked":
                return {"success": False, "message": "Card is already blocked."}

            # Update status in database
            conn.execute(
                """UPDATE Card SET Status = 'Blocked'
                   WHERE Account_No = ? AND Card_Issuer = ?""",
                (account_no, card_issuer)
            )
            conn.commit()

            return {
                "success": True,
                "message": f"{card_issuer} {card['Card_Type']} card has been successfully blocked."
            }
        finally:
            conn.close()


# Singleton
data_loader = DataLoader()