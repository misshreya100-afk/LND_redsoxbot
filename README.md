# LND — Late Night Delivery — Telegram Bot & Channel Setup

Everything below takes ~10 minutes. Steps 1–3 must be done by you (they need your own Telegram account). Step 4 onward is just running the code I built.

## 1. Create the bot with BotFather

1. Open Telegram, search for **@BotFather**, tap **Start**.
2. Send `/newbot`.
3. Name it: `LND - Late Night Delivery`
4. Choose a username ending in `bot`, e.g. `LND_LateNightDelivery_bot` (must be unique).
5. BotFather replies with a **token** like `123456789:AAExample...` — copy it. This goes in `.env`.
6. (Optional polish) Send BotFather:

- `/setdescription` → "Order food for late night delivery, right here on Telegram."
- `/setabouttext` → "LND — we deliver when everyone else is asleep."
- `/setuserpic` → upload a logo image.

## 2. Create the channel

1. In Telegram: **☰ Menu → New Channel**.
2. Name: `LND — Late Night Delivery`
3. Choose Public (get a link like `t.me/LND_LateNight`) or Private.
4. Add your bot as an **Administrator** of the channel (Channel → Administrators → Add Admin → search your bot's username → give it "Post Messages" permission).
5. Get the channel's numeric ID:

- Post any message in the channel, forward it to **@userinfobot** (or @JsonDumpBot), it will show the `channel_id` — a negative number like `-1001234567890`.
- Put that in `.env` as `CHANNEL_ID`.

## 3. Get your own admin chat ID

Message **@userinfobot** on Telegram — it replies with your numeric user ID. Put that in `.env` as `ADMIN_CHAT_ID`. This authorizes the `/orders`, `/done`, and `/broadcast` admin commands.

## 3b. Create a separate group for order alerts (recommended)

If `ADMIN_CHAT_ID` is the only place alerts go, and you ever test-order using your own account, the order confirmation *and* the admin alert land in the exact same chat (they're the same conversation) — confusing to read. Fix it by giving alerts their own home:

1. Create a normal Telegram **group** (not a channel) — e.g. "LND — Orders"
2. Add your bot to the group as a member
3. Send any message in the group
4. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
5. Find `"chat":{"id":-987654321,"type":"group",...}` in the response — that's the group's ID
6. Put it in `.env` as `ORDER_ALERTS_CHAT_ID`

Now every new order posts to the group, completely separate from any individual customer's chat with the bot — including your own, if you're testing.

## 4. Configure the project

```bash
cd lnd_bot
cp .env.example .env
# edit .env and paste in BOT_TOKEN, ADMIN_CHAT_ID, CHANNEL_ID
```

Edit `config.py` to customize your menu, prices, hours, and support contact — it's plain Python, no framework needed.

## 5. Install & run locally

```bash
pip install -r requirements.txt
python bot.py
```

Open Telegram, find your bot, send `/start`. That's it — ordering flow, cart, checkout, and admin alerts all work immediately.

## 6. Keep it running 24/7 (deployment)

Running `python bot.py` on your laptop only works while it's on. For real 24/7 uptime, deploy it for free/cheap on one of:

- **Railway.app** — connect your GitHub repo, add the same env vars in its dashboard, deploy. Easiest option.
- **Render.com** — "Background Worker" service type, same env vars.
- **A cheap VPS** (e.g. Hetzner, DigitalOcean) — run with `pm2` or a `systemd` service so it restarts on crash/reboot.

## How the bot works

- `/start` → welcome + main menu (View Menu, My Orders, Support)
- Customer taps through categories → items → quantity → adds to cart
- Checkout asks for address + phone → confirms → saves order to SQLite (`lnd_orders.db`)
- You (admin) instantly get a Telegram DM with the full order details
- `/orders` (admin only) — lists all pending orders
- `/done <order_id>` (admin only) — marks delivered, auto-notifies the customer
- `/broadcast <text>` (admin only) — posts an announcement to your channel
- Customers can check `My Orders` anytime to see status

## Files

- `bot.py` — all bot logic
- `config.py` — your menu, prices, branding text (edit this freely)
- `db.py` — SQLite storage, no setup needed
- `.env.example` — copy to `.env` with your real token/IDs
- `requirements.txt` — dependencies
