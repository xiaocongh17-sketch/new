"""Import community dictionary from Excel into SQLite."""
import sqlite3
import openpyxl
import os

EXCEL_PATH = r"C:\Users\94128\OneDrive\Desktop\楼盘字典.xlsx"
DB_PATH = os.path.join(os.path.dirname(__file__), "dev.db")

def import_data():
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS community_dict (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(region, name)
        )
    """)
    conn.execute("DELETE FROM community_dict")

    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        region, name = row[0], row[1]
        if region and name:
            region = str(region).strip()
            name = str(name).strip()
            try:
                conn.execute(
                    "INSERT INTO community_dict (region, name) VALUES (?, ?)",
                    (region, name),
                )
                count += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()
    print(f"Imported {count} communities from {EXCEL_PATH}")


if __name__ == "__main__":
    import_data()
