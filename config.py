"""
LND (Late Night Delivery) - Bot Configuration
Edit this file to change your menu, business name, hours, etc.
Secrets (token, admin id) come from environment variables — see .env.example
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---- Secrets (set these in your .env file, never hardcode them) ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")   # your personal chat id, receives admin commands
ORDER_ALERTS_CHAT_ID = os.getenv("ORDER_ALERTS_CHAT_ID", "")  # group chat for new order alerts
CHANNEL_ID = os.getenv("CHANNEL_ID", "")         # your channel id, e.g. -1001234567890 (optional, for /broadcast)

# ---- Compliance ----
# Set this to the legal drinking age in your jurisdiction. The bot will not
# show the menu or take an order until the customer confirms they meet it.
LEGAL_AGE = 21
CONTACT_NUMBER = "9293598795"
LICENSE_NOTE = CONTACT_NUMBER
DISCLAIMER = (
    "🪪 Valid government ID is required at the door. If our rider can't verify you meet the "
    f"legal drinking age ({LEGAL_AGE}+), the order will be returned and is non-refundable.\n"
    "We do not deliver to visibly intoxicated individuals. Please drink responsibly."
)

# ---- Branding ----
BRAND_NAME = "LND — Late Night Delivery"
WELCOME_TEXT = (
    "*Welcome to LND — Late Night Delivery!*\n\n"
    "Beer, spirits & wine delivered after dark.\n"
    "Delivery available within *5 miles of Boston downtown*\n"
    "Open daily: *11:00 PM – 5:00 AM*\n"
    "Pricing shown in USD.\n\n"
    "Choose an option below to get started"
)
AGE_GATE_TEXT = (
    f"🔞 *Age Verification Required*\n\n"
    f"LND sells alcohol. You must be *{LEGAL_AGE} years or older* to order, and you'll need to "
    "show valid photo ID when your order arrives.\n\n"
    f"Are you {LEGAL_AGE} or older?"
)
AGE_DECLINED_TEXT = (
    "Sorry, we're not able to serve you. Alcohol delivery is restricted to customers who meet "
    "the legal drinking age. Come back and message us again once you do. 🙏"
)
SUPPORT_TEXT = (
    "☎️ *Need help?*\n"
    f"Message us here anytime, or call/WhatsApp: {LICENSE_NOTE}\n"
    "We reply fast, even at 2 AM 😉"
)

# ---- Menu ----
# category -> { item_name: price }
MENU = {
    "Whiskey": {
        "Black Label": 60,
        "Jameson": 55,
        "Jack Daniel's No. 7": 50,
    },
    "Vodka": {
        "Absolut Vodka": 45,
        "Tito's Handmade": 50,
        "Grey Goose": 55,
        "Pink Whitney": 40,
    },
    "Tequila": {
        "El Jimador Blanco": 60,
        "818 Tequila Blanco": 50,
    },
    "Wine": {
        "Josh Cellars": 35,
        "Decoy Cabernet": 45,
    },
    "Beer Pack 6": {
        "Corona": 30,
        "Budweiser": 35,
        "Modelo": 35,
    },
    "Jagermeister": {
        "Jagermeister": 50,
    },
}

DELIVERY_FEE = 6
CURRENCY = "$"
