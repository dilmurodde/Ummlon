import sqlite3
from datetime import datetime
import os
import sys

# Asosiy papkani yo'lini qo'shish
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def add_fake_users():
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()

    fake_users = [
        ("Madina", 21, "female", "Toshkent", "Chilonzor", None),
        ("Jasur", 24, "male", "Samarqand", "Markaz", None),
        ("Laylo", 19, "female", "Buxoro", "G'ijduvon", None),
        ("Sardor", 22, "male", "Andijon", "Asaka", None),
        ("Zuhra", 20, "female", "Farg'ona", "Marg'ilon", None)
    ]

    for user in fake_users:
        cursor.execute('''
            INSERT INTO users (full_name, age, gender, region, city, photo, is_fake, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (user[0], user[1], user[2], user[3], user[4], user[5], datetime.now()))
    
    conn.commit()
    conn.close()
    print("Soxta foydalanuvchilar qo'shildi! ✅")

if __name__ == "__main__":
    add_fake_users()
  
