import os
import hashlib
import sqlite3
import requests
from datetime import datetime
from flask import Flask, request, abort
from maxgram import Bot
from config import TOKEN, ROBO_PASS2

# ================== НАСТРОЙКИ ==================
DB_PATH = "profiles.db"
app = Flask(__name__)
bot = Bot(TOKEN)

# Render автоматически даёт внешний хост
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{RENDER_HOST}/webhook"

# ================== БАЗА ==================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        gender TEXT,
        birth TEXT,
        vip_until INTEGER DEFAULT 0,
        city TEXT,
        about TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_vip(user_id: str, days: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor
