import os
import logging
import psycopg2
from flask import Flask, request
from maxgram import Bot

# ================= ЛОГИ =================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("BOT")

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    raise Exception("Нет BOT_TOKEN")

if not DATABASE_URL:
    raise Exception("Нет DATABASE_URL")

bot = Bot(TOKEN)
app = Flask(__name__)

# ================= ПОДКЛЮЧЕНИЕ К БД =================
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# ================= ГЛАВНАЯ =================
@app.route("/")
def home():
    return "Bot with PostgreSQL running", 200


# ================= WEBHOOK =================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "no data", 400

    text = data.get("text")
    user_id = str(data.get("user_id") or data.get("from_id"))

    if text == "/start":
        cursor.execute(
            "INSERT INTO profiles (user_id) VALUES (%s) ON CONFLICT DO NOTHING;",
            (user_id,)
        )

        bot.send_message(user_id, "Привет! Ты сохранён в PostgreSQL ✅")

    return "ok", 200


# ================= ЗАПУСК =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
