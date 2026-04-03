from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8755182960:AAGPNn68I9YPO2dAlgIVnJBrBG_bzB0k6kA"
GROUP_ID = -1003734439551
CARD_NUMBER = "5168752110788497"

waiting_for_order = {}
orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🔧 Вызвать сантехника"]
    ]

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if text == "🔧 Вызвать сантехника":
        waiting_for_order[user.id] = True
        await update.message.reply_text("Опишите проблему и адрес:")
        return

    if waiting_for_order.get(user.id):
        order_id = user.id

        orders[order_id] = {
            "text": text,
            "master": None
        }

        keyboard = [
            [InlineKeyboardButton("✅ Принять заказ", callback_data=f"take_{order_id}")]
        ]

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🆕 Новый заказ\n\n{text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("✅ Заказ отправлен!")
        waiting_for_order[user.id] = False

async def take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    master = query.from_user
    order_id = int(query.data.split("_")[1])

    if orders[order_id]["master"]:
        await query.answer("❌ Уже взяли!", show_alert=True)
        return

    orders[order_id]["master"] = master.id

    keyboard = [
        [InlineKeyboardButton("✅ Завершить заказ", callback_data=f"done_{order_id}")]
    ]

    username = master.username if master.username else "без ника"

    await query.edit_message_text(
        text=f"🔧 В работе\n\nМастер: {master.first_name}\n📞 @{username}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await context.bot.send_message(
        chat_id=order_id,
        text=f"Мастер найден!\n\n👤 {master.first_name}\n📞 @{username}"
    )

async def done_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    master = query.from_user
    order_id = int(query.data.split("_")[1])

    if orders[order_id]["master"] != master.id:
        await query.answer("❌ Не твой заказ!", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("✅ Оплатил", callback_data=f"paid_{order_id}")]
    ]

    await context.bot.send_message(
        chat_id=master.id,
        text=f"💰 Оплати 100 грн за заказ\n\n💳 Карта:\n{CARD_NUMBER}\n\nПосле оплаты нажми кнопку ниже",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.edit_message_text("💳 Ожидаем оплату мастером")

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    master = query.from_user

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"✅ Оплата получена\n\nМастер: {master.first_name}"
    )

    await query.edit_message_text("✅ Спасибо за оплату!")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(take_order, pattern="^take_"))
app.add_handler(CallbackQueryHandler(done_order, pattern="^done_"))
app.add_handler(CallbackQueryHandler(paid, pattern="^paid_"))

app.run_polling()