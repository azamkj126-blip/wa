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
    return {"countries": await manager.get_countries_catalog()}


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

    if country:
        # Match only bots that actually have this country in their catalog
        catalog = await manager.get_countries_catalog()
        matching_bots = [
            item["bot"]
            for item in catalog
            if item["country"].lower() == country.lower()
            or item.get("clean_key", "").lower() in country.lower()
        ]
        target_bots = list(dict.fromkeys(matching_bots)) or BOT_USERNAMES[:2]
        for b in target_bots:
            state = manager.bots[b]
            if state.locked:
                continue
            items, err = await manager.fetch_from_bot(b, country=country, force_refresh=refresh)
            avail = [
                {"phone": item.phone, "country": item.country, "bot": item.bot_username}
                for item in items
                if item.status == "AVAILABLE"
            ]
            if avail:
                return {"numbers": avail, "error": None}
        return {"numbers": [], "error": f"لا توجد أرقام متاحة حالياً لدولة {country}"}

    # Browser visit without parameters: return cached available numbers safely without spamming bots
    all_cached = [
        {"phone": item.phone, "country": item.country, "bot": item.bot_username}
        for state in manager.bots.values()
        for item in state.numbers
        if item.status == "AVAILABLE"
    ]
    return {
        "numbers": all_cached,
        "count": len(all_cached),
        "message": "حدد الدولة والبوت لمشاهدة الأرقام الحية: مثال /numbers?bot=cloud_number_bot&country=Yemen أو افتح التطبيق",
        "error": None,
    }


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


@app.get("/clean_groups")
@app.post("/clean_groups")
async def clean_groups():
    if not manager.authorized:
        raise HTTPException(status_code=400, detail="جلسة تليجرام غير مصرح بها حالياً")
    return await manager.clean_groups()

