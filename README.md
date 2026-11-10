# Gold AI Alerts — Phase 1

A minimal TradingView webhook receiver for XAUUSD M5 BUY test alerts. No trading execution or OpenAI API integration yet.

## Configure
Set these environment variables in Render (never commit secrets):
- `TELEGRAM_BOT_TOKEN`: newly rotated Telegram token
- `TELEGRAM_CHAT_ID`: your private Telegram chat ID
- `WEBHOOK_SECRET`: long random string (`python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`)

## Deploy on Render
1. Push this folder to a **private** GitHub repository.
2. Render > New > Web Service > select repository.
3. Runtime: Python. Build command: `pip install -r requirements.txt`.
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Choose a **paid always-on** instance, add the environment variables, and deploy.
6. Verify `https://YOUR-SERVICE.onrender.com/health` returns `{"status":"ok"}`.
7. Your webhook URL is `https://YOUR-SERVICE.onrender.com/webhook/YOUR_WEBHOOK_SECRET`.

## TradingView alert
On the OANDA:XAUUSD 5-minute chart, paste this Pine Script v6 in Pine Editor:

```pine
//@version=6
indicator("Gold AI M5 BUY Test", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
buy = ta.crossover(fast, slow) and close > fast and close > slow and barstate.isconfirmed
plot(fast, "EMA 9", color=color.green)
plot(slow, "EMA 21", color=color.orange)
plotshape(buy, title="BUY", style=shape.labelup, location=location.belowbar, color=color.green, text="BUY")
if buy
    alert('{"signal":"BUY","symbol":"' + syminfo.tickerid + '","timeframe":"' + timeframe.period + '","price":' + str.tostring(close) + '}', alert.freq_once_per_bar_close)
```

Create Alert > Condition: `Gold AI M5 BUY Test` > `Any alert() function call`; Notifications > Webhook URL: paste the URL above. Set once per bar close if offered. TradingView requires 2FA for webhooks.

## Immediate webhook test (no market signal required)
Use a terminal; keep your secret out of shell history by reading it interactively:

```bash
read -r -p 'Render service URL (https://...onrender.com): ' SERVICE_URL
read -r -s -p 'Webhook secret: ' WEBHOOK_SECRET; echo
curl -sS -X POST "${SERVICE_URL}/webhook/${WEBHOOK_SECRET}" -H 'Content-Type: application/json' -d '{"signal":"BUY","symbol":"OANDA:XAUUSD","timeframe":"5","price":4000}'
unset WEBHOOK_SECRET
```

The price 4000 is **synthetic test data**, not a live quote. Expect `{"accepted":true}` and a Telegram test notification. The initial demo uses an in-process async task; for reliable production delivery, replace it with a durable queue, retries, deduplication and monitoring. The path secret is a basic shared secret; it may appear in request logs. Never share webhook URL publicly, and rotate if exposed.
