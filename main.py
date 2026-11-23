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
    # مسار لإبقاء سيرفر Render مستيقظاً عبر خدمة مراقبة خارجية
    return {"status": "alive", "bots_count": len(BOT_USERNAMES)}


@app.get("/numbers")
async def get_available_numbers(refresh: bool = False, country: Optional[str] = None):
    """
    يعرض الأرقام المتوفرة من كل بوت (رقم/دفعة من كل بوت غير مقفل).
    """
    manager._cleanup_expired_locks()
    results = []
    for bot_name in BOT_USERNAMES:
        state = manager.bots[bot_name]
        if state.locked:
            continue
        if refresh or not state.numbers:
            await manager.fetch_from_bot(bot_name, country=country)
        for item in state.numbers:
            if item.status == "AVAILABLE":
                results.append({
                    "phone": item.phone,
                    "country": item.country,
                    "bot": item.bot_username,
                })
    return {"numbers": results}


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
    for state in manager.bots.values():
        for item in state.numbers:
            if item.phone == phone:
                return {
                    "phone": item.phone,
                    "status": item.status,
                    "otp": item.otp_code,
                }
    raise HTTPException(status_code=404, detail="الرقم غير موجود في الجلسة الحالية")


@app.post("/release/{bot_username}")
async def release_bot(bot_username: str):
    manager.release_bot(bot_username)
    return {"status": "released", "bot": bot_username}


@app.get("/debug/inspect/{bot_username}")
async def debug_inspect(bot_username: str, cmd: str = "/start"):
    return await manager.inspect_bot_buttons(bot_username, cmd)
