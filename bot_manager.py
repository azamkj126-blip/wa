import asyncio
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import httpx
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.custom import Message

API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
STRING_SESSION = os.getenv("TG_STRING_SESSION", "")
WA_CHECKER_URL = os.getenv("WA_CHECKER_URL", "")  # رابط خدمة فحص الواتساب

OTP_GROUPS = [
    "Group_Messaga_N",
    "JXCodez",
]

BOT_USERNAMES = [
    "B_M_Numbers_Files_bot",
    "smslybot",
    "SOJIB_BRO_FRESH_NUMBER_BOT",
    "NumberNest_2_Bot",
    "JXOTPBot",
]


@dataclass
class NumberItem:
    phone: str
    country: str
    bot_username: str
    status: str = "AVAILABLE"  # AVAILABLE | RESERVED | COMPLETED
    reserved_by: Optional[str] = None
    reserved_at: float = 0.0
    otp_code: Optional[str] = None


@dataclass
class BotState:
    username: str
    locked: bool = False
    last_message_id: Optional[int] = None
    numbers: List[NumberItem] = field(default_factory=list)


class TelegramNumberManager:
    def __init__(self):
        self.client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        self.bots: Dict[str, BotState] = {b: BotState(username=b) for b in BOT_USERNAMES}
        self._op_locks: Dict[str, asyncio.Lock] = {b: asyncio.Lock() for b in BOT_USERNAMES}
        self.http = httpx.AsyncClient(timeout=10.0)

    async def start(self):
        await self.client.start()
        self._register_otp_listeners()

    async def stop(self):
        await self.http.aclose()
        await self.client.disconnect()

    # ==========================================================
    # 1. مستمع الأكواد (القروبات العامة + المحادثات الخاصة مع البوتات)
    # ==========================================================
    def _register_otp_listeners(self):
        monitored_chats = OTP_GROUPS + BOT_USERNAMES

        @self.client.on(events.NewMessage(chats=monitored_chats))
        async def otp_handler(event):
            text = event.raw_text or ""
            otp_match = re.search(r"\b(\d{3}[-\s]?\d{3})\b", text)
            if not otp_match:
                return

            clean_otp = re.sub(r"\D", "", otp_match.group(1))
            sender_chat = await event.get_chat()
            chat_username = getattr(sender_chat, "username", "") or ""

            # مطابقة الكود مع الأرقام المحجوزة حالياً
            for bot_state in self.bots.values():
                for item in bot_state.numbers:
                    if item.status != "RESERVED":
                        continue

                    last4 = item.phone[-4:]
                    # إذا جاء الكود من قروب عام: يجب مطابقة آخر 4 أرقام من الرقم المحجوز
                    if chat_username in OTP_GROUPS:
                        if last4 in re.sub(r"\s+", "", text):
                            item.otp_code = clean_otp
                            item.status = "COMPLETED"
                            return
                    # إذا جاء الكود من نفس شات البوت الذي أخذنا منه الرقم
                    elif chat_username.lower() == item.bot_username.lower():
                        # لو ذكر آخر 4 أرقام أو كان هو الرقم الوحيد المحجوز من هذا البوت
                        item.otp_code = clean_otp
                        item.status = "COMPLETED"
                        return

    # ==========================================================
    # 2. دوال مساعدة للضغط على الأزرار واستخراج الأرقام
    # ==========================================================
    async def _send_and_wait(self, bot: str, text: str, timeout: int = 12) -> Optional[Message]:
        entity = await self.client.get_entity(bot)
        fut = asyncio.get_running_loop().create_future()

        async def handler(event):
            if not fut.done():
                fut.set_result(event.message)

        self.client.add_event_handler(handler, events.NewMessage(from_users=entity))
        try:
            await self.client.send_message(entity, text)
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self.client.remove_event_handler(handler)

    async def _click_and_wait(
        self,
        bot: str,
        msg: Message,
        row: Optional[int] = None,
        col: Optional[int] = None,
        flat_index: Optional[int] = None,
        text_contains: Optional[str] = None,
        timeout: int = 12,
    ) -> Optional[Message]:
        entity = await self.client.get_entity(bot)
        fut = asyncio.get_running_loop().create_future()

        async def handler(event):
            if not fut.done():
                fut.set_result(event.message)

        self.client.add_event_handler(handler, events.NewMessage(from_users=entity))
        self.client.add_event_handler(handler, events.MessageEdited(from_users=entity))
        try:
            if text_contains:
                clicked = False
                if msg.buttons:
                    for r_idx, b_row in enumerate(msg.buttons):
                        for c_idx, btn in enumerate(b_row):
                            if text_contains.lower() in (btn.text or "").lower():
                                await msg.click(r_idx, c_idx)
                                clicked = True
                                break
                        if clicked:
                            break
                if not clicked:
                    return None
            elif flat_index is not None:
                await msg.click(flat_index)
            elif row is not None and col is not None:
                await msg.click(row, col)
            else:
                return None

            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self.client.remove_event_handler(handler)

    def _extract_phones(self, text: str) -> List[str]:
        if not text:
            return []
        raw_matches = re.findall(r"\+?\d[\d\s\-]{7,16}\d", text)
        phones = []
        for m in raw_matches:
            digits = re.sub(r"\D", "", m)
            if 8 <= len(digits) <= 15:
                phones.append("+" + digits)
        # إزالة التكرار مع حفظ الترتيب
        return list(dict.fromkeys(phones))

    async def is_registered_on_whatsapp(self, phone: str) -> bool:
        """
        يتصل بخدمة فحص الواتساب الخارجية (مثل whatsmeow أو Baileys).
        إذا لم يتم ضبط WA_CHECKER_URL يرجع False مؤقتاً للتجربة.
        """
        if not WA_CHECKER_URL:
            return False
        try:
            # فاصل زمني لحماية رقم الفحص من الحظر
            await asyncio.sleep(2.5)
            resp = await self.http.get(WA_CHECKER_URL, params={"phone": phone.lstrip("+")})
            data = resp.json()
            return bool(data.get("registered", False))
        except Exception:
            # في حال خطأ بالاتصال، نعتبره مسجلاً لتجنب عرض أرقام غير مفحوصة
            return True

    async def _filter_fresh_numbers(self, phones: List[str], country: str, bot_username: str) -> List[NumberItem]:
        fresh = []
        for p in phones:
            is_reg = await self.is_registered_on_whatsapp(p)
            if not is_reg:
                fresh.append(NumberItem(phone=p, country=country, bot_username=bot_username))
        return fresh

    # ==========================================================
    # 3. مسارات السحب المخصصة لكل بوت من البوتات الخمسة
    # ==========================================================
    async def fetch_from_bot(self, bot_username: str, country: Optional[str] = None, max_retries: int = 3) -> List[NumberItem]:
        state = self.bots[bot_username]
        if state.locked:
            # البوت مقفل لأن هناك رقماً نشطاً محجوزاً منه
            return state.numbers

        async with self._op_locks[bot_username]:
            # إذا كانت هناك أرقام متاحة بالفعل من هذا البوت، لا تطلب غيرها
            available_now = [n for n in state.numbers if n.status == "AVAILABLE"]
            if available_now:
                return available_now

            msg = None
            target_country = country or "Default"

            if bot_username == "B_M_Numbers_Files_bot":
                # /getnumber -> الزر 3 (index 2) واتساب -> الزر 1 (index 0) اليمن
                target_country = "Yemen"
                m1 = await self._send_and_wait(bot_username, "/getnumber")
                m2 = await self._click_and_wait(bot_username, m1, flat_index=2) if m1 else None
                msg = await self._click_and_wait(bot_username, m2, flat_index=0) if m2 else None

            elif bot_username == "smslybot":
                # أزرار كيبورد ثابتة -> إرسال نص الزر Get Number -> واتساب -> الدولة
                target_country = country or "Egypt"
                m1 = await self._send_and_wait(bot_username, "Get Number")
                m2 = await self._click_and_wait(bot_username, m1, text_contains="whats") if m1 else None
                msg = await self._click_and_wait(bot_username, m2, text_contains=target_country) if m2 else None

            elif bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
                # /start -> زر واتساب (index 0) -> باكستان أو السودان
                target_country = country or "Pakistan"
                m1 = await self._send_and_wait(bot_username, "/start")
                m2 = await self._click_and_wait(bot_username, m1, flat_index=0) if m1 else None
                msg = await self._click_and_wait(bot_username, m2, text_contains=target_country) if m2 else None

            elif bot_username == "NumberNest_2_Bot":
                # /start -> الدولة -> أول سيرفر فرعي (index 0) -> رقم واحد
                target_country = country or "Italy"
                m1 = await self._send_and_wait(bot_username, "/start")
                m2 = await self._click_and_wait(bot_username, m1, text_contains=target_country) if m1 else None
                msg = await self._click_and_wait(bot_username, m2, flat_index=0) if m2 else None

            elif bot_username == "JXOTPBot":
                # /start -> الزر 1 (index 0) واتساب -> الزر 1 (index 0) كمبوديا
                target_country = "Cambodia"
                m1 = await self._send_and_wait(bot_username, "/start")
                m2 = await self._click_and_wait(bot_username, m1, flat_index=0) if m1 else None
                msg = await self._click_and_wait(bot_username, m2, flat_index=0) if m2 else None

            # فحص الدفعة وإعادة المحاولة بزر التغيير إذا كانت كل الأرقام مسجلة مسبقاً
            fresh_items: List[NumberItem] = []
            for attempt in range(max_retries):
                if not msg:
                    break
                phones = self._extract_phones(msg.raw_text)
                fresh_items = await self._filter_fresh_numbers(phones, target_country, bot_username)
                if fresh_items:
                    break

                # لم نجد رقماً غير مسجل -> نضغط زر تغيير الرقم حسب مكان الزر في كل بوت
                if bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
                    # الزر الثاني تحت الأرقام (تخطي الزر الأول غير المعروف)
                    msg = await self._click_and_wait(bot_username, msg, flat_index=1)
                else:
                    # في بقية البوتات، زر التغيير هو الأول أو يحتوي كلمة تغيير/جديد/change/new
                    next_msg = await self._click_and_wait(bot_username, msg, text_contains="تغيير")
                    if not next_msg:
                        next_msg = await self._click_and_wait(bot_username, msg, text_contains="جديد")
                    if not next_msg:
                        next_msg = await self._click_and_wait(bot_username, msg, text_contains="change")
                    if not next_msg:
                        next_msg = await self._click_and_wait(bot_username, msg, flat_index=0)
                    msg = next_msg

            state.numbers = fresh_items
            state.last_message_id = msg.id if msg else None
            return fresh_items

    # ==========================================================
    # 4. الحجز، فك القفل، وأداة فحص أزرار البوتات
    # ==========================================================
    def reserve_number(self, phone: str, user_id: str) -> Optional[NumberItem]:
        self._cleanup_expired_locks()
        for state in self.bots.values():
            if state.locked:
                continue
            for item in state.numbers:
                if item.phone == phone and item.status == "AVAILABLE":
                    item.status = "RESERVED"
                    item.reserved_by = user_id
                    item.reserved_at = time.time()
                    state.locked = True  # قفل البوت بالكامل حتى ينتهي التفعيل
                    return item
        return None

    def release_bot(self, bot_username: str):
        state = self.bots.get(bot_username)
        if state:
            state.locked = False
            state.numbers = []

    def _cleanup_expired_locks(self, ttl_seconds: int = 300):
        now = time.time()
        for state in self.bots.values():
            if state.locked:
                reserved = [n for n in state.numbers if n.status == "RESERVED"]
                if reserved and (now - reserved[0].reserved_at) > ttl_seconds:
                    state.locked = False
                    state.numbers = []

    async def inspect_bot_buttons(self, bot_username: str, command: str = "/start"):
        """أداة مساعدة لكشف النص الدقيق وترتيب الأزرار لأي بوت"""
        msg = await self._send_and_wait(bot_username, command)
        if not msg:
            return {"error": "No response from bot"}
        buttons = []
        if msg.buttons:
            for r, row in enumerate(msg.buttons):
                for c, btn in enumerate(row):
                    buttons.append({"row": r, "col": c, "text": btn.text})
        return {"text": msg.raw_text, "buttons": buttons}
