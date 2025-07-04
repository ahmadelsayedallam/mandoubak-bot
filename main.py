import logging
import os
import csv
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            role TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            details TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            mandoub_id INTEGER,
            offer_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, role):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()
    conn.close()

def get_user_role(user_id):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_order(user_id, details):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, details) VALUES (?, ?)", (user_id, details))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    return order_id

def get_mandoubs():
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE role = 'mandoub'")
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids

def save_offer(order_id, mandoub_id, text):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("INSERT INTO offers (order_id, mandoub_id, offer_text) VALUES (?, ?, ?)", (order_id, mandoub_id, text))
    conn.commit()
    conn.close()

# بدء الكود
TOKEN = os.getenv("TOKEN")
init_db()
user_states = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧑 أنا مستخدم", callback_data='user')],
        [InlineKeyboardButton("🛵 أنا مندوب", callback_data='mandoub')]
    ]
    await update.message.reply_text("أهلاً بيك في *مندوبك*!\nاختار نوع حسابك:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    role = query.data
    add_user(user_id, role)
    await query.edit_message_text(f"تم تسجيلك كـ { 'مستخدم 👤' if role == 'user' else 'مندوب 🛵' }")

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    role = get_user_role(user_id)
    if role != "user":
        await update.message.reply_text("الأمر ده للمستخدمين فقط.")
        return

    user_states[user_id] = "awaiting_order"
    await update.message.reply_text("اكتب الطلب + العنوان في رسالة واحدة.\nمثال: 1 كيلو طماطم – شارع النصر")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    role = get_user_role(user_id)

    if user_states.get(user_id) == "awaiting_order":
        order_id = save_order(user_id, text)
        user_states[user_id] = None
        mandoubs = get_mandoubs()
        for mid in mandoubs:
            try:
                await context.bot.send_message(mid, f"📦 طلب جديد:\n{text}\n\nابعت السعر + الوقت هنا كعرض.")
                context.user_data[mid] = order_id
            except:
                continue
        await update.message.reply_text(f"تم إرسال الطلب إلى {len(mandoubs)} مندوبين ✅")

    elif role == "mandoub":
        order_id = context.user_data.get(user_id)
        if not order_id:
            await update.message.reply_text("لا يوجد طلب حالياً.")
            return
        save_offer(order_id, user_id, text)
        await context.bot.send_message(order_id, f"📨 عرض جديد من مندوب:\n{text}")
        await update.message.reply_text("✅ تم إرسال العرض.")

    else:
        await update.message.reply_text("استخدم /start لتسجيل نوعك.")

# أوامر Debug
async def debug_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    text = "\n".join([f"ID: {r[0]} | Role: {r[1]}" for r in rows])
    await update.message.reply_text(text or "No users found.")

async def debug_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders")
    rows = c.fetchall()
    conn.close()
    text = "\n".join([f"Order ID: {r[0]} | User: {r[1]} | Details: {r[2]}" for r in rows])
    await update.message.reply_text(text or "No orders found.")

async def debug_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT * FROM offers")
    rows = c.fetchall()
    conn.close()
    text = "\n".join([f"Offer ID: {r[0]} | Order: {r[1]} | Mandoub: {r[2]} | Text: {r[3]}" for r in rows])
    await update.message.reply_text(text or "No offers found.")

async def export_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()

    with open("users.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "role"])
        writer.writerows(c.execute("SELECT * FROM users"))

    with open("orders.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "user_id", "details"])
        writer.writerows(c.execute("SELECT * FROM orders"))

    with open("offers.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "order_id", "mandoub_id", "offer_text"])
        writer.writerows(c.execute("SELECT * FROM offers"))

    conn.close()
    await update.message.reply_document(document=open("users.csv", "rb"), filename="users.csv")
    await update.message.reply_document(document=open("orders.csv", "rb"), filename="orders.csv")
    await update.message.reply_document(document=open("offers.csv", "rb"), filename="offers.csv")

# تشغيل البوت
def main():
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    # Debug commands
    app.add_handler(CommandHandler("debug_users", debug_users))
    app.add_handler(CommandHandler("debug_orders", debug_orders))
    app.add_handler(CommandHandler("debug_offers", debug_offers))
    app.add_handler(CommandHandler("export_db", export_db))

    app.run_polling()

if __name__ == "__main__":
    main()
