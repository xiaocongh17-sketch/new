"""Add new AI collection columns to existing houses table."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dev.db")

NEW_COLUMNS = [
    ("building_type", "VARCHAR(16)"),
    ("total_floors", "INTEGER"),
    ("has_parking", "BOOLEAN"),
    ("parking_count", "INTEGER"),
    ("occupancy_status", "VARCHAR(16)"),
    ("tenant_cooperation", "VARCHAR(32)"),
    ("lease_expiry", "VARCHAR(32)"),
    ("decoration_year", "VARCHAR(16)"),
    ("decoration_quality", "TEXT"),
    ("key_location", "VARCHAR(128)"),
    ("viewing_password", "VARCHAR(32)"),
    ("listed_on_beike", "BOOLEAN"),
    ("list_price", "NUMERIC(12,2)"),
    ("list_duration", "VARCHAR(32)"),
    ("unsold_reason", "TEXT"),
    ("viewing_count", "INTEGER"),
    ("purchase_year", "VARCHAR(16)"),
    ("is_only_home", "BOOLEAN"),
    ("tax_note", "TEXT"),
    ("seller_motivation", "VARCHAR(128)"),
    ("ai_collected_fields", "VARCHAR(256)"),
    ("collector_score", "INTEGER"),
    ("deal_probability", "INTEGER"),
]

conn = sqlite3.connect(DB_PATH)
existing = {r[1] for r in conn.execute("PRAGMA table_info(houses)").fetchall()}

added = 0
for col_name, col_type in NEW_COLUMNS:
    if col_name not in existing:
        conn.execute(f"ALTER TABLE houses ADD COLUMN {col_name} {col_type}")
        added += 1
        print(f"  + {col_name} {col_type}")

conn.commit()
conn.close()
print(f"\nAdded {added} new columns. DB ready!")
