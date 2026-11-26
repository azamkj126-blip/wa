import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bot_manager import TelegramNumberManager, BOT_USERNAMES

manager = TelegramNumberManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.start()
    yield
    await manager.stop()


app = FastAPI(title="WhatsApp Numbers Hub API", lifespan=lifespan)


class ReserveRequest(BaseModel):
    phone: str
    user_id: str


@app.get("/health")
async def health():
    return {
        "status": "alive",
        "telegram_authorized": manager.authorized,
        "bots_count": len(BOT_USERNAMES),
    }


@app.get("/countries")
async def get_countries():
    return {"countries": manager.get_countries_catalog()}


@app.get("/numbers")
async def get_available_numbers(
    bot: Optional[str] = None,
    country: Optional[str] = None,
    refresh: bool = False,
):
    manager._cleanup_expired_locks()

    if bot:
        if bot not in BOT_USERNAMES:
            return {"numbers": [], "error": "البوت غير موجود"}
        state = manager.bots[bot]
        if state.locked:
            return {"numbers": [], "error": "هذا البوت محجوز حالياً لمستخدم آخر"}
        items, err = await manager.fetch_from_bot(bot, country=country, force_refresh=refresh)
        return {
            "numbers": [
                {"phone": item.phone, "country": item.country, "bot": item.bot_username}
                for item in items
                if item.status == "AVAILABLE"
            ],
            "error": err,
        }

    async def fetch_one(bot_name: str):
        state = manager.bots[bot_name]
        if state.locked:
            return []
        items, _ = await manager.fetch_from_bot(bot_name, country=country, force_refresh=refresh)
        return [
            {"phone": item.phone, "country": item.country, "bot": item.bot_username}
            for item in items
            if item.status == "AVAILABLE"
        ]

    batches = await asyncio.gather(*(fetch_one(b) for b in BOT_USERNAMES))
    results = [item for batch in batches for item in batch]
    return {"numbers": results, "error": None}


@app.get("/debug/errors")
async def debug_errors():
    return {"errors": manager.last_errors}


@app.get("/debug/trace")
async def debug_trace():
    return manager.last_trace


@app.post("/reserve")
async def reserve_number(req: ReserveRequest):
    item = manager.reserve_number(req.phone, req.user_id)
    if not item:
        raise HTTPException(status_code=409, detail="الرقم غير متاح أو تم حجزه بالفعل")
    return {
        "status": "reserved",
        "phone": item.phone,
        "country": item.country,
        "bot": item.bot_username,
    }


@app.get("/otp/{phone}")
async def check_otp(phone: str):
    if not phone.startswith("+"):
        phone = "+" + phone
    if phone in manager.completed_otps:
        data = manager.completed_otps[phone]
        return {"phone": data["phone"], "status": data["status"], "otp": data["otp"]}
    for state in manager.bots.values():
        for item in state.numbers:
            if item.phone == phone:
                return {"phone": item.phone, "status": item.status, "otp": item.otp_code}
    raise HTTPException(status_code=404, detail="الرقم غير موجود في الجلسة الحالية")


@app.post("/scan")
async def trigger_scan():
    asyncio.create_task(manager.scan_all_bots())
    return {"status": "scan_started"}


@app.post("/release/{bot_username}")
async def release_bot(bot_username: str):
    manager.release_bot(bot_username)
    return {"status": "released", "bot": bot_username}
