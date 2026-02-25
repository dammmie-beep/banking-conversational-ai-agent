# migrate_to_sqlite.py
import sqlite3
import pandas as pd

EXCEL_PATH = "data\Globus_AI_Engr_Interview_Data.xlsx"
DB_PATH = "data/banking.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    xls = pd.ExcelFile(EXCEL_PATH)

    # ── Customer table ──────────────────────────────────────
    df_cust = pd.read_excel(xls, sheet_name="Customer")
    df_cust.to_sql("Customer", conn, if_exists="replace", index=False)
    print(f"Customer table: {len(df_cust)} rows inserted")

    # ── Transaction table ───────────────────────────────────
    df_tx = pd.read_excel(xls, sheet_name="Transaction")
    df_tx["Transaction_Date"] = pd.to_datetime(
        df_tx["Transaction_Date"],
        format="%d/%m/%Y %H:%M:%S"
    ).astype(str)
    df_tx.to_sql("Transaction", conn, if_exists="replace", index=False)
    print(f"Transaction table: {len(df_tx)} rows inserted")

    # ── Card table ──────────────────────────────────────────
    df_card = pd.read_excel(xls, sheet_name="Card")
    df_card.to_sql("Card", conn, if_exists="replace", index=False)
    print(f"Card table: {len(df_card)} rows inserted")

    conn.commit()
    conn.close()
    print(f"\nDone! Database created at {DB_PATH}")

if __name__ == "__main__":
    migrate()