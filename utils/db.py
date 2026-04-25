import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                age INTEGER,
                gender TEXT,
                region TEXT,
                city TEXT,
                photo TEXT,
                lang TEXT,
                is_fake INTEGER DEFAULT 0,
                created_at DATETIME
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username, lang):
        self.cursor.execute('INSERT OR IGNORE INTO users (user_id, username, lang, created_at) VALUES (?, ?, ?, ?)',
                           (user_id, username, lang, datetime.now()))
        self.conn.commit()

    def update_user(self, user_id, **kwargs):
        keys = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(user_id)
        self.cursor.execute(f'UPDATE users SET {keys} WHERE user_id = ?', values)
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    def get_random_users(self, gender, limit=10):
        self.cursor.execute('SELECT * FROM users WHERE gender = ? ORDER BY RANDOM() LIMIT ?', (gender, limit))
        return self.cursor.fetchall()

    def add_fake_user(self, full_name, age, gender, region, city, photo):
        self.cursor.execute('''
            INSERT INTO users (full_name, age, gender, region, city, photo, is_fake, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (full_name, age, gender, region, city, photo, datetime.now()))
        self.conn.commit()
      
