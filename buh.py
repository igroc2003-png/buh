# buh.py
import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request
from maxgram import Bot
from maxgram.keyboards import InlineKeyboard
from config import TOKEN, ADMIN_ID, SUPPORT_URL, ROBO_PASS2

# ================== ЛОГИ ==================
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - BOT - %(levelname)s - %(message)s")
log = logging.getLogger("BOT")

# ================== ФЛАСК ==================
app = Flask(__name__)

DB_FILE = "profiles.db"   # База профилей
GEO_DB = "geo.db"

# ================== БАЗА ДАННЫХ ==================
def create_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS profiles (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        gender TEXT,
        birthdate TEXT,
        age INTEGER,
        zodiac TEXT,
        city TEXT,
        region TEXT,
        about TEXT,
        photo_url TEXT,
        is_vip INTEGER DEFAULT 0,
        vip_until INTEGER DEFAULT NULL,
        deleted_at TEXT DEFAULT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
    )""")
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def save_profile(user_id, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profiles (user_id, name, gender, birthdate, age, zodiac,
                              city, region, about, photo_url, is_vip, vip_until)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            gender=excluded.gender,
            birthdate=excluded.birthdate,
            age=excluded.age,
            zodiac=excluded.zodiac,
            city=excluded.city,
            region=excluded.region,
            about=excluded.about,
            photo_url=excluded.photo_url,
            is_vip=excluded.is_vip,
            vip_until=excluded.vip_until
    """, (
        user_id,
        data.get("name"),
        data.get("gender"),
        data.get("birthdate"),
        data.get("age"),
        data.get("zodiac"),
        data.get("city"),
        data.get("region"),
        data.get("about"),
        data.get("photo_url"),
        data.get("is_vip", 0),
        data.get("vip_until")
    ))
    conn.commit()
    conn.close()

# ================== GEO ==================
def find_cities(prefix, limit=10):
    try:
        conn = sqlite3.connect(GEO_DB)
        cursor = conn.cursor()
        prefix = prefix.capitalize()
        cursor.execute("SELECT name, region FROM geo WHERE name LIKE ? LIMIT ?", (prefix + "%", limit))
        cities = cursor.fetchall()
        conn.close()
        return cities
    except:
        return []

# ================== ЗОДИАК ==================
def get_zodiac(day, month):
    zodiac_dates = [
        (120, "Козерог"), (218, "Водолей"), (320, "Рыбы"), (420, "Овен"),
        (521, "Телец"), (621, "Близнецы"), (722, "Рак"), (823, "Лев"),
        (923, "Дева"), (1023, "Весы"), (1122, "Скорпион"), (1222, "Стрелец"), (1231, "Козерог")
    ]
    n = month * 100 + day
    for end, sign in zodiac_dates:
        if n <= end:
            return sign
    return "Козерог"

# ================== ROBOKASSA ==================
def add_vip(user_id, days):
    profile = get_profile(user_id)
    if not profile:
        return False

    now_ts = int(datetime.now().timestamp())
    current_vip = profile.get("vip_until") or now_ts

    if current_vip > now_ts:
        new_vip = current_vip + days * 86400
    else:
        new_vip = now_ts + days * 86400

    profile["vip_until"] = new_vip
    profile["is_vip"] = 1
    save_profile(user_id, profile)
    return True

@app.route("/robokassa_result", methods=["POST"])
def robokassa_result():
    out_summ = request.form.get("OutSum")
    inv_id = request.form.get("InvId")
    signature = request.form.get("SignatureValue", "").upper()

    if not out_summ or not inv_id:
        return "bad request"

    my_crc = hashlib.md5(f"{out_summ}:{inv_id}:{ROBO_PASS2}".encode()).hexdigest().upper()
    if my_crc != signature:
        return "bad sign"

    try:
        user_id, days = inv_id.split("_")
        days = int(days)
    except:
        return "bad invoice"

    if not add_vip(user_id, days):
        return "user not found"

    return f"OK{inv_id}"

# ================== БОТ ==================
bot = Bot(TOKEN)
users = {}  # временные данные пользователей

# Главное меню
def main_menu(profile=None):
    emoji = "👤"
    if profile:
        if profile.get("gender") == "М": emoji="👨"
        if profile.get("gender") == "Ж": emoji="👩"
    return InlineKeyboard(
        [{"text":"⭐ VIP","callback":"vip"}],
        [{"text":f"{emoji} Анкета","callback":"open_profile"}],
        [{"text":"🎯 Фильтры","callback":"filters"}],
        [{"text":"🎲 Рулетка","callback":"roulette"}],
        [{"text":"🆘 Поддержка","url": SUPPORT_URL}]
    )

# ================== СТАРТ ==================
@bot.command("start")
def start(ctx):
    chat_id = str(ctx.chat_id)
    profile = get_profile(chat_id)
    if profile:
        ctx.reply("Главное меню:", keyboard=main_menu(profile))
    else:
        ctx.reply("🔞 Вам есть 18 лет?", keyboard=InlineKeyboard([{"text":"✅ Да","callback":"age_yes"},{"text":"❌ Нет","callback":"age_no"}]))

# ================== RUN ==================
if __name__ == "__main__":
    log.info("🚀 Создаём таблицы, если нет")
    create_db()

    # Запускаем бот и Flask вместе
    from threading import Thread
    def run_flask():
        app.run(host="0.0.0.0", port=5000)

    def run_bot():
        bot.run()

    Thread(target=run_flask).start()
    Thread(target=run_bot).start()
