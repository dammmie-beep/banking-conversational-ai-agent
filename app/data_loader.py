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
                "SELECT * FROM Customers WHERE Account_No = ?",
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
                """SELECT * FROM Transactions
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
                "SELECT * FROM Cards WHERE Account_No = ?",
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
                """SELECT * FROM Cards
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
                """UPDATE Cards SET Status = 'Blocked'
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