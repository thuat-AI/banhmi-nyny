import sqlite3

conn = sqlite3.connect("menu.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    content TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    rating TEXT,
    message TEXT
)
""")
conn.commit()
conn.close()
print("✅ Tạo xong bảng orders và feedback!")
