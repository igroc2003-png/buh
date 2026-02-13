import logging
from flask import Flask, request, jsonify
from maxgram import Bot
from config import TOKEN
import sqlite3

# ================== ЛОГИ ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - БОТ - %(levelname)s - %(message)s"
)
log = logging.getLogger("БОТ")

# ================== Flask ==================
app = Flask("buh")

# ================== Инициализация бота ==================
bot = Bot(token=TOKEN)  # Без webhook_url, мы будем ставить вручную через setWebhook

# ================== БД ==================
conn = sqlite3.connect("profiles.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    vip INTEGER DEFAULT 0
)
""")
conn.commit()

# ================== Вебхук ==================
WEBHOOK_URL = "https://buh-ck22.onrender.com/webhook"

def set_webhook():
    import requests
    try:
        r = requests.get(f"https://api.max.ru/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
        if r.status_code == 200:
            log.info(f"Вебхук установлен: {WEBHOOK_URL}")
        else:
            log.error(f"Ошибка установки вебхука: {r.text}")
    except Exception as e:
        log.error(f"Ошибка при setWebhook: {e}")

set_webhook()

# ================== Обработчик вебхука ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "empty"}), 400

        user_id = data.get("user_id")
        text = data.get("text")

        if text == "/start":
            # Проверяем есть ли пользователь в базе
            cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
            profile = cursor.fetchone()
            if not profile:
                cursor.execute("INSERT INTO profiles(user_id, vip) VALUES(?, ?)", (user_id, 0))
                conn.commit()
            bot.send_message(user_id, "Привет! Ваш профиль создан ✅")
            return jsonify({"status": "ok"})

        # Здесь можно обрабатывать другие команды
        bot.send_message(user_id, f"Вы написали: {text}")
        return jsonify({"status": "ok"})

    except Exception as e:
        log.error(f"Ошибка вебхука: {e}")
        return jsonify({"status": "error"}), 500

# ================== Главный запуск ==================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    log.info(f"🌐 Flask запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
