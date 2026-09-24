"""
LND — Late Night Delivery — Telegram Bot
Built with python-telegram-bot v21 (async)

Run:
    pip install -r requirements.txt
    cp .env.example .env   # then fill in BOT_TOKEN and ADMIN_CHAT_ID
    python bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

import config
import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("lnd-bot")

# Conversation states
CHOOSING_ITEM, CHOOSING_QTY, ADD_MORE, GET_NAME, GET_ADDRESS, GET_PHONE, CONFIRM = range(7)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍾 View Menu / Order", callback_data="menu")],
        [InlineKeyboardButton("📦 My Orders", callback_data="myorders")],
        [InlineKeyboardButton("☎️ Support", callback_data="support")],
    ])


def age_gate_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Yes, I'm {config.LEGAL_AGE}+", callback_data="verify_age|yes")],
        [InlineKeyboardButton("❌ No", callback_data="verify_age|no")],
    ])


def is_age_verified(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get("age_verified"))


def category_keyboard():
    if len(config.MENU) == 1:
        category = next(iter(config.MENU))
        buttons = []
        ordered_items = list(config.MENU[category].items())
        for i in range(0, len(ordered_items), 2):
            row = []
            for name, price in ordered_items[i:i + 2]:
                row.append(InlineKeyboardButton(f"{name} — {config.CURRENCY}{price}", callback_data=f"item|{category}|{name}"))
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🛒 Checkout", callback_data="checkout")])
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
        return InlineKeyboardMarkup(buttons)

    buttons = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in config.MENU]
    buttons.append([InlineKeyboardButton("🛒 Checkout", callback_data="checkout")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def items_keyboard(category):
    buttons = []
    ordered_items = list(config.MENU[category].items())
    for i in range(0, len(ordered_items), 2):
        row = []
        for name, price in ordered_items[i:i + 2]:
            row.append(InlineKeyboardButton(f"{name} — {config.CURRENCY}{price}", callback_data=f"item|{category}|{name}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Back to categories", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)


def qty_keyboard(category, item):
    buttons = [[InlineKeyboardButton(str(n), callback_data=f"qty|{category}|{item}|{n}") for n in (1, 2, 3, 4)]]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"cat|{category}")])
    return InlineKeyboardMarkup(buttons)


def cart_total(cart):
    return sum(price * qty for (_, price, qty) in cart)


def cart_text(cart):
    if not cart:
        return "Your cart is empty."
    lines = [f"• {name} x{qty} — {config.CURRENCY}{price*qty}" for (name, price, qty) in cart]
    lines.append(f"\nDelivery fee: {config.CURRENCY}{config.DELIVERY_FEE}")
    lines.append(f"*Total: {config.CURRENCY}{cart_total(cart) + config.DELIVERY_FEE}*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handlers — general
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("cart", [])
    if is_age_verified(context):
        await update.message.reply_text(config.WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text(config.AGE_GATE_TEXT, parse_mode="Markdown", reply_markup=age_gate_keyboard())
    return ConversationHandler.END


async def verify_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, answer = q.data.split("|", 1)
    if answer == "yes":
        context.user_data["age_verified"] = True
        await q.edit_message_text(config.WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        context.user_data["age_verified"] = False
        await q.edit_message_text(config.AGE_DECLINED_TEXT)
    return ConversationHandler.END


async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_age_verified(context):
        await q.edit_message_text(config.AGE_GATE_TEXT, parse_mode="Markdown", reply_markup=age_gate_keyboard())
        return ConversationHandler.END
    await q.edit_message_text(config.WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(config.SUPPORT_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    orders = db.get_user_orders(q.from_user.id)
    if not orders:
        text = "You have no orders yet."
    else:
        lines = []
        for o in orders:
            lines.append(f"#{o['id']} — {o['status']} — {config.CURRENCY}{o['total']} — {o['created_at']}")
        text = "*Your recent orders:*\n" + "\n".join(lines)
    await q.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


# ---------------------------------------------------------------------------
# Handlers — ordering flow
# ---------------------------------------------------------------------------

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_age_verified(context):
        await q.edit_message_text(config.AGE_GATE_TEXT, parse_mode="Markdown", reply_markup=age_gate_keyboard())
        return ConversationHandler.END
    context.user_data.setdefault("cart", [])

    if len(config.MENU) == 1:
        category = next(iter(config.MENU))
        text = (
            "*Whisky, Vodka, Wine & Beer*\n\n"
            "The full list lives in the bot — this is the short version for the road."
        )
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=items_keyboard(category))
        return CHOOSING_ITEM

    await q.edit_message_text("Pick a category:", reply_markup=category_keyboard())
    return CHOOSING_ITEM


async def show_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, category = q.data.split("|", 1)
    await q.edit_message_text(f"*{category}*\nPick an item:", parse_mode="Markdown", reply_markup=items_keyboard(category))
    return CHOOSING_ITEM


async def ask_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, category, item = q.data.split("|", 2)
    await q.edit_message_text(f"How many *{item}*?", parse_mode="Markdown", reply_markup=qty_keyboard(category, item))
    return CHOOSING_QTY


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Added to cart ✅")
    _, category, item, qty = q.data.split("|", 3)
    qty = int(qty)
    price = config.MENU[category][item]
    context.user_data.setdefault("cart", []).append((item, price, qty))

    text = f"Added: {item} x{qty}\n\n*Your cart:*\n{cart_text(context.user_data['cart'])}"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add more items", callback_data="menu")],
        [InlineKeyboardButton("🛒 Checkout", callback_data="checkout")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])
    await q.edit_message_text(text, parse_mode="Markdown", reply_markup=buttons)
    return ADD_MORE


async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cart = context.user_data.get("cart", [])
    if not cart:
        await q.edit_message_text("Your cart is empty. Add something first!", reply_markup=category_keyboard())
        return CHOOSING_ITEM
    await q.edit_message_text(
        f"*Order summary:*\n{cart_text(cart)}\n\n� Please type your *customer name*:",
        parse_mode="Markdown",
    )
    return GET_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    customer_name = update.message.text.strip() or "Customer"
    context.user_data["customer_name"] = customer_name
    await update.message.reply_text("📍 Now send your *delivery address*:", parse_mode="Markdown")
    return GET_ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text("📱 Now send your *phone number* (for delivery contact):", parse_mode="Markdown")
    return GET_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    cart = context.user_data.get("cart", [])
    customer_name = context.user_data.get("customer_name", "Customer")
    address = context.user_data["address"]
    phone = context.user_data["phone"]
    total = cart_total(cart) + config.DELIVERY_FEE

    text = (
        f"*Please confirm your order:*\n\n{cart_text(cart)}\n\n"
        f"👤 Customer: {customer_name}\n"
        f"📍 Address: {address}\n📱 Phone: {phone}\n\n"
        f"⚠️ *Cash payment only.* Money will be taken in cash strictly on delivery.\n\n"
        f"{config.DISCLAIMER}\n\nConfirm?"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Order", callback_data="confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="home")],
    ])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=buttons)
    return CONFIRM


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cart = context.user_data.get("cart", [])
    customer_name = context.user_data.get("customer_name", "Customer")
    address = context.user_data.get("address", "")
    phone = context.user_data.get("phone", "")
    total = cart_total(cart) + config.DELIVERY_FEE
    items_text = ", ".join(f"{name} x{qty}" for (name, _, qty) in cart)

    user = q.from_user
    order_id = db.create_order(user.id, customer_name, items_text, total, address, phone)

    await q.edit_message_text(
        f"🎉 *Order #{order_id} placed!*\n\nCustomer: {customer_name}\n"
        f"We'll deliver to:\n📍 {address}\n\n"
        f"Total: {config.CURRENCY}{total}\n\n"
        f"📞 For delivery updates, call/WhatsApp: {config.CONTACT_NUMBER}\n\n"
        f"Track it anytime with *My Orders*.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

    # Notify admin / order alerts group
    alert_chat_id = config.ORDER_ALERTS_CHAT_ID or config.ADMIN_CHAT_ID
    if alert_chat_id:
        try:
            await context.bot.send_message(
                chat_id=alert_chat_id,
                text=(
                    f"🔔 *New Order #{order_id}*\n"
                    f"Customer: {customer_name}\n"
                    f"Customer Telegram: @{user.username or user.full_name} (id: {user.id})\n"
                    f"Items: {items_text}\n"
                    f"Total: {config.CURRENCY}{total}\n"
                    f"Address: {address}\n"
                    f"Phone: {phone}\n\n"
                    f"Mark delivered with: /done {order_id}"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            log.warning(f"Could not notify order alerts chat: {e}")

    context.user_data["cart"] = []
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = []
    await update.message.reply_text("Order cancelled.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Admin commands
# ---------------------------------------------------------------------------

def is_admin(update: Update) -> bool:
    return config.ADMIN_CHAT_ID and str(update.effective_user.id) == str(config.ADMIN_CHAT_ID)


async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    orders = db.get_pending_orders()
    if not orders:
        await update.message.reply_text("No pending orders. 🎉")
        return
    lines = [f"#{o['id']} | {o['status']} | {config.CURRENCY}{o['total']} | {o['items']} | 📍{o['address']} | 📱{o['phone']}" for o in orders]
    await update.message.reply_text("\n\n".join(lines))


async def admin_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /done <order_id>")
        return
    order_id = int(context.args[0])
    db.update_status(order_id, "DELIVERED")
    order = db.get_order(order_id)
    await update.message.reply_text(f"Order #{order_id} marked as DELIVERED ✅")
    if order:
        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=f"🛵 Your order #{order_id} has been delivered! Enjoy — thanks for ordering from {config.BRAND_NAME}."
            )
        except Exception as e:
            log.warning(f"Could not notify customer: {e}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /broadcast <message> — posts to the configured channel."""
    if not is_admin(update):
        return
    if not config.CHANNEL_ID:
        await update.message.reply_text("CHANNEL_ID not set in .env — add your channel's chat id first.")
        return
    text = update.message.text.partition(" ")[2]
    if not text:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    await context.bot.send_message(chat_id=config.CHANNEL_ID, text=text)
    await update.message.reply_text("Posted to channel ✅")


# ---------------------------------------------------------------------------
# App wiring
# ---------------------------------------------------------------------------

def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN not set. Copy .env.example to .env and fill it in.")

    db.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_menu, pattern="^menu$")],
        states={
            CHOOSING_ITEM: [
                CallbackQueryHandler(show_items, pattern=r"^cat\|"),
                CallbackQueryHandler(ask_qty, pattern=r"^item\|"),
                CallbackQueryHandler(checkout_start, pattern="^checkout$"),
                CallbackQueryHandler(show_menu, pattern="^menu$"),
                CallbackQueryHandler(go_home, pattern="^home$"),
            ],
            CHOOSING_QTY: [
                CallbackQueryHandler(add_to_cart, pattern=r"^qty\|"),
                CallbackQueryHandler(show_items, pattern=r"^cat\|"),
            ],
            ADD_MORE: [
                CallbackQueryHandler(show_menu, pattern="^menu$"),
                CallbackQueryHandler(checkout_start, pattern="^checkout$"),
                CallbackQueryHandler(go_home, pattern="^home$"),
            ],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CONFIRM: [
                CallbackQueryHandler(confirm_order, pattern="^confirm$"),
                CallbackQueryHandler(go_home, pattern="^home$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_age, pattern=r"^verify_age\|"))
    app.add_handler(order_conv)
    app.add_handler(CallbackQueryHandler(go_home, pattern="^home$"))
    app.add_handler(CallbackQueryHandler(support, pattern="^support$"))
    app.add_handler(CallbackQueryHandler(my_orders, pattern="^myorders$"))

    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CommandHandler("done", admin_done))
    app.add_handler(CommandHandler("broadcast", broadcast))

    log.info("LND bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
