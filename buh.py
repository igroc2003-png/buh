import os
import hashlib
import sqlite3
import requests
import urllib3
from datetime import datetime
from flask import Flask, request, abort
from maxgram import Bot
from config import TOKEN, ROBO_PASS2

# ================== ОТКЛЮЧАЕМ SSL WARNING ==================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== НАСТРОЙКИ ==================
DB_PATH = "profiles.db"
app = Flask(__name__)
bot = Bot(TOKEN)

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


# ================== ДОБАВЛЕНИЕ VIP ==================
def add_vip(user_id: str, days: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT vip_until FROM profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    current_vip = row[0] or 0
    now_ts = int(datetime.now().timestamp())

    if current_vip > now_ts:
        new_vip = current_vip + days * 86400
    else:
        new_vip = now_ts + days * 86400

    cursor.execute(
        "UPDATE profiles SET vip_until = ? WHERE user_id = ?",
        (new_vip, user_id)
    )

    conn.commit()
    conn.close()
    return True


# ================== WEBHOOK MAXGRAM ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    if not update:
        abort(400)

    bot.process_update(update)
    return "OK"


# ================== WEBHOOK ROBOKASSA ==================
@app.route("/robokassa_result", methods=["POST"])
def robokassa_result():
    out_summ = request.form.get("OutSum")
    inv_id = request.form.get("InvId")
    signature = request.form.get("SignatureValue", "").upper()

    if not out_summ or not inv_id:
        return "bad request"

    my_crc = hashlib.md5(
        f"{out_summ}:{inv_id}:{ROBO_PASS2}".encode()
    ).hexdigest().upper()

    if my_crc != signature:
        return "bad sign"

    try:
        user_id, days = inv_id.split("_")
        days = int(days)
    except Exception:
        return "bad invoice"

    success = add_vip(user_id, days)

    if not success:
        return "user not found"

    return f"OK{inv_id}"


# ================== УСТАНОВКА WEBHOOK ==================
def set_webhook():
    url = f"https://api.max.ru/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    try:
        response = requests.get(url, verify=False)
        print("✅ Webhook установлен:", response.text)
    except Exception as e:
        print("❌ Ошибка установки webhook:", e)


# ================== ЗАПУСК ==================
if __name__ == "__main__":
    init_db()
    set_webhook()

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Сервер работает на порту {port}")
    print(f"🌐 URL вебхука: {WEBHOOK_URL}")

    app.run(host="0.0.0.0", port=port)
