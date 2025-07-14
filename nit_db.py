import sqlite3

# Kết nối với CSDL
conn = sqlite3.connect("menu.db")

# Tạo bảng menu nếu chưa tồn tại
conn.execute("""
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price TEXT NOT NULL,
    image TEXT
)
""")

conn.commit()
conn.close()
print("✅ Đã tạo xong bảng 'menu' trong file menu.db")
