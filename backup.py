import shutil
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy("menu.db", f"backup_menu_{timestamp}.db")
print("✅ Đã sao lưu.")
