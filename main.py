import os
import json
import hmac
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gold-alerts')
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')

@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = [k for k in ('TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','WEBHOOK_SECRET') if not os.getenv(k)]
    if missing:
        raise RuntimeError('Missing environment variables: ' + ', '.join(missing))
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health():
    return {'status': 'ok'}

async def send_telegram(message: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage', json={'chat_id': CHAT_ID, 'text': message})
            r.raise_for_status()
    except Exception:
        logger.exception('Telegram delivery failed')

@app.post('/webhook/{secret}')
async def webhook(secret: str, request: Request):
    if not hmac.compare_digest(secret, WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail='Forbidden')
    if int(request.headers.get('content-length', '0') or 0) > 4096:
        raise HTTPException(status_code=413, detail='Payload too large')
    raw = await request.body()
    if len(raw) > 4096:
        raise HTTPException(status_code=413, detail='Payload too large')
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail='Invalid JSON')
    if not isinstance(data, dict) or data.get('signal') != 'BUY' or data.get('symbol') != 'OANDA:XAUUSD' or data.get('timeframe') != '5':
        raise HTTPException(status_code=422, detail='Unexpected signal')
    try:
        price = float(data['price'])
        if not 0 < price < 100000:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail='Invalid price')
    msg = f"XAUUSD BUY test alert\nSymbol: OANDA:XAUUSD\nTimeframe: M5\nPrice: {price:.2f}\nNot investment advice."
    asyncio.create_task(send_telegram(msg))
    return {'accepted': True}
