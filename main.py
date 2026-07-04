import sqlite3
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 100,
    bank INTEGER DEFAULT 0,
    last_daily INTEGER DEFAULT 0,
    last_steal INTEGER DEFAULT 0
)
""")
conn.commit()

def create_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,100,0,0,0)", (uid,))
    conn.commit()

def get(uid):
    cursor.execute("SELECT coins, bank, last_daily, last_steal FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()

def update(uid, coins=None, bank=None, last_daily=None, last_steal=None):
    c,b,d,s = get(uid)

    cursor.execute("""
    UPDATE users SET coins=?, bank=?, last_daily=?, last_steal=? WHERE user_id=?
    """, (
        coins if coins is not None else c,
        bank if bank is not None else b,
        last_daily if last_daily is not None else d,
        last_steal if last_steal is not None else s,
        uid
    ))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    create_user(update.effective_user.id)
    await update.message.reply_text("🎮 ربات آماده است!\n/daily /balance /steal /bank")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    create_user(uid)
    c,b,_,_ = get(uid)
    await update.message.reply_text(f"💰 {c}\n🏦 {b}")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    create_user(uid)

    c,b,d,s = get(uid)
    now = int(time.time())

    if now - d < 86400:
        await update.message.reply_text("⏳ قبلاً گرفتی")
        return

    update(uid, coins=c+100, last_daily=now)
    await update.message.reply_text("🎁 +100 سکه")

async def steal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("روی کسی ریپلای کن")
        return

    a = update.effective_user.id
    v = update.message.reply_to_message.from_user.id

    create_user(a)
    create_user(v)

    ac,ab,ad,as_ = get(a)
    vc,vb,vd,vs = get(v)

    now = int(time.time())

    if now - as_ < 60:
        await update.message.reply_text("⏳ صبر کن")
        return

    if random.randint(1,100) > 50:
        amt = random.randint(5,40)
        update(v, coins=vc-amt)
        update(a, coins=ac+amt, last_steal=now)
        await update.message.reply_text(f"🟢 دزدیدی {amt}")
    else:
        update(a, coins=max(0, ac-20), last_steal=now)
        await update.message.reply_text("🔴 لو رفتی")

async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    create_user(uid)

    c,b,_,_ = get(uid)

    amt = min(c,50)
    update(uid, coins=c-amt, bank=b+amt+int(amt*0.1))

    await update.message.reply_text("🏦 واریز شد")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("steal", steal))
    app.add_handler(CommandHandler("bank", bank))

    app.run_polling()

if __name__ == "__main__":
    main()
