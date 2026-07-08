import sqlite3
conn = sqlite3.connect("dev.db")
rows = conn.execute("SELECT id, community, area, room_type, rent_price, status, owner_id, store_id FROM houses").fetchall()
print(f"Houses: {len(rows)}")
for r in rows:
    print(f"  id={r[0][:20]}... commun={r[1]} area={r[2]} type={r[3]} price={r[4]} status={r[5]} owner={r[6]} store={r[7]}")
conn.close()
