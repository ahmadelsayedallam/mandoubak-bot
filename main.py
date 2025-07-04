import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import os

TOKEN = os.getenv("TOKEN")

users = {}
orders = []
offers = {}

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

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if users.get(user_id) != "user":
        await update.message.reply_text("الأمر ده مخصص للمستخدمين فقط.")
        return
    await update.message.reply_text("اكتب تفاصيل الطلب + العنوان في رسالة واحدة.\nمثال: 1 كيلو طماطم – شارع فيصل")
    context.user_data["awaiting_order"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if context.user_data.get("awaiting_order"):
        order_id = len(orders)
        orders.append({"id": order_id, "text": text, "user_id": user_id})
        context.user_data["awaiting_order"] = False

        count = 0
        for uid, role in users.items():
            if role == "mandoub":
                count += 1
                try:
                    await context.bot.send_message(uid, f"📦 طلب جديد:\n{text}\n\nلو حابب تقدم عرض، ابعت السعر والوقت هنا.")
                    offers[uid] = {"order_id": order_id, "user_id": user_id}
                except:
                    continue

        await update.message.reply_text(f"تم إرسال طلبك لـ {count} مندوبين ✅")
    else:
        await update.message.reply_text("استخدم /order لبدء طلب جديد.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'user':
        users[user_id] = "user"
        await query.edit_message_text("تم تسجيلك كمستخدم ✅\nاستخدم /order لبدء طلب.")
    elif query.data == 'mandoub':
        users[user_id] = "mandoub"
        await query.edit_message_text("تم تسجيلك كمندوب ✅")

async def handle_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if users.get(user_id) != "mandoub":
        return

    offer_text = update.message.text
    offer_data = offers.get(user_id)
    if not offer_data:
        await update.message.reply_text("لا يوجد طلب حالياً.")
        return

    user_to_notify = offer_data["user_id"]
    await context.bot.send_message(user_to_notify, f"📨 عرض من مندوب:\n{offer_text}\n\nلو موافق، ابعت 'تم'")
    await update.message.reply_text("تم إرسال العرض للمستخدم.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(users.keys()), handle_offer))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == '__main__':
    main()
add main bot file
