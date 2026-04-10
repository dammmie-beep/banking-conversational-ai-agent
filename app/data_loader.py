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

    def block_card(self, card_issuer: str, account_no: str, session_blocked: set = None):
        """
        Validates that the card exists and is not already blocked.
        Does NOT write to the database — blocking is session-only so state
        resets when the session ends.
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """SELECT * FROM Cards
                   WHERE Account_No = ? AND Card_Issuer = ?""",
                (account_no, card_issuer)
            )
            card = cursor.fetchone()

            if not card:
                return {"success": False, "message": "Card not found."}

            db_blocked = str(card["Status"]).lower() == "blocked"
            session_blocked = session_blocked or set()
            if db_blocked or card_issuer in session_blocked:
                return {"success": False, "message": "Card is already blocked."}

            return {
                "success": True,
                "message": f"{card_issuer} {card['Card_Type']} card has been successfully blocked.",
                "card_type": card["Card_Type"],
            }
        finally:
            conn.close()


# Singleton
data_loader = DataLoader()