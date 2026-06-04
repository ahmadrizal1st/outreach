import shutil
import os
import sys
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def backup():
    src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.sqlite"))
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "backups"))
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = os.path.join(backup_dir, f"database_{date.today()}.sqlite")

    if os.path.exists(src):
        shutil.copy2(src, backup_file)
        print(f"✅ Backup tersimpan: {backup_file}")
    else:
        print("❌ Database tidak ditemukan")

if __name__ == "__main__":
    backup()
