import logging
import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

TOKEN = os.getenv("TOKEN")

# ---------- DB Setup ----------
conn = sqlite3.connect("mandoubak.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    role TEXT
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    mandoub_id INTEGER,
    offer_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ---------- Logger ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧑 أنا مستخدم", callback_data='user')],
        [InlineKeyboardButton("🙵 أنا مندوب", callback_data='mandoub')]
    ]
    await update.message.reply_text("أهلاً بيك في *مندوبك*!\nاختار نوع حسابك:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    role = 'user' if query.data == 'user' else 'mandoub'
    c.execute("REPLACE INTO users (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()

    await query.edit_message_text(f"تم تسجيلك ك{'مستخدم' if role == 'user' else 'مندوب'} ✅")

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    c.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if not result or result[0] != 'user':
        await update.message.reply_text("الأمر ده مخصص للمستخدمين فقط.")
        return

    await update.message.reply_text("اكتب تفاصيل الطلب + العنوان في رسالة واحدة.\nمثال: 1 كيلو طماطم – شارع فيصل")
    context.user_data["awaiting_order"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if context.user_data.get("awaiting_order"):
        context.user_data["awaiting_order"] = False
        c.execute("INSERT INTO orders (user_id, details) VALUES (?, ?)", (user_id, text))
        conn.commit()
        order_id = c.lastrowid

        c.execute("SELECT user_id FROM users WHERE role = 'mandoub'")
        mandoubs = c.fetchall()

        for (mid,) in mandoubs:
            try:
                await context.bot.send_message(mid, f"📦 طلب جديد:
{text}\n
لو حابب تقدم عرض، ابعت السعر والوقت هنا.")
                context.application.chat_data[mid] = {"order_id": order_id, "user_id": user_id}
            except:
                continue

        await update.message.reply_text(f"تم إرسال طلبك لـ {len(mandoubs)} مندوبين ✅")
    else:
        await update.message.reply_text("استخدم /order لبدء طلب جديد.")

async def handle_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mandoub_id = update.message.from_user.id
    c.execute("SELECT role FROM users WHERE user_id = ?", (mandoub_id,))
    result = c.fetchone()
    if not result or result[0] != 'mandoub':
        return

    offer_text = update.message.text
    data = context.application.chat_data.get(mandoub_id)
    if not data:
        await update.message.reply_text("لا يوجد طلب حالياً.")
        return

    order_id = data["order_id"]
    user_id = data["user_id"]
    c.execute("INSERT INTO offers (order_id, mandoub_id, offer_text) VALUES (?, ?, ?)", (order_id, mandoub_id, offer_text))
    conn.commit()

    await context.bot.send_message(user_id, f"📨 عرض من مندوب:
{offer_text}\n
لو موافق، ابعت 'تم'")
    await update.message.reply_text("تم إرسال العرض للمستخدم.")

# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(?!/).*"), handle_offer))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
