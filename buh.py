import os
import logging
import sqlite3
from flask import Flask, request
from maxgram import Bot

# ================== НАСТРОЙКИ ==================
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"
DATABASE = "profiles.db"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "https://buh-ck22.onrender.com/webhook"

# ================== ЛОГИ ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - БОТ - %(levelname)s - %(message)s")
log = logging.getLogger("БОТ")

# ================== БАЗА ДАННЫХ ==================
conn = sqlite3.connect(DATABASE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    vip INTEGER DEFAULT 0
)
""")
conn.commit()

# ================== ФЛАСК ==================
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "No data", 400

    user_id = str(data.get("user_id") or data.get("from_id"))
    username = data.get("username") or data.get("from_username") or "Unknown"

    # Проверяем команду /start
    if data.get("text") == "/start":
        cursor.execute("INSERT OR IGNORE INTO profiles (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        log.info(f"Новый пользователь: {username} ({user_id})")

        bot.send_message(user_id, "Привет! Бот работает ✅")
    return "OK", 200

# ================== БОТ ==================
bot = Bot(token=TOKEN)  # Внимание: webhook_url НЕ указываем, ставим вручную через админку Max

# ================== СТАРТ ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render задаёт порт через переменную PORT
    log.info(f"🌐 Flask запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
