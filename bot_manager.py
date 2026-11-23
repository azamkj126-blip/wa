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
_raw_session = os.getenv("TG_STRING_SESSION", "").strip()
STRING_SESSION = (
    _raw_session + ("=" * ((4 - len(_raw_session[1:]) % 4) % 4))
    if _raw_session
    else ""
)
WA_CHECKER_URL = os.getenv("WA_CHECKER_URL", "")

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

# كتالوج جميع الدول المتوفرة في البوتات الخمسة
COUNTRIES_CATALOG = [
    {"country": "Yemen", "ar": "اليمن", "iso": "YE", "bot": "B_M_Numbers_Files_bot"},
    {"country": "Sudan", "ar": "السودان", "iso": "SD", "bot": "SOJIB_BRO_FRESH_NUMBER_BOT"},
    {"country": "Pakistan", "ar": "باكستان", "iso": "PK", "bot": "SOJIB_BRO_FRESH_NUMBER_BOT"},
    {"country": "Cambodia", "ar": "كمبوديا", "iso": "KH", "bot": "JXOTPBot"},
    # NumberNest_2_Bot
    {"country": "Egypt", "ar": "مصر (سيرفر 1)", "iso": "EG", "bot": "NumberNest_2_Bot"},
    {"country": "Sudan", "ar": "السودان (سيرفر 2)", "iso": "SD", "bot": "NumberNest_2_Bot"},
    {"country": "Syria", "ar": "سوريا", "iso": "SY", "bot": "NumberNest_2_Bot"},
    {"country": "Lebanon", "ar": "لبنان", "iso": "LB", "bot": "NumberNest_2_Bot"},
    {"country": "Italy", "ar": "إيطاليا (سيرفر 1)", "iso": "IT", "bot": "NumberNest_2_Bot"},
    {"country": "Ethiopia", "ar": "إثيوبيا", "iso": "ET", "bot": "NumberNest_2_Bot"},
    {"country": "Malaysia", "ar": "ماليزيا", "iso": "MY", "bot": "NumberNest_2_Bot"},
    {"country": "Mali", "ar": "مالي (سيرفر 1)", "iso": "ML", "bot": "NumberNest_2_Bot"},
    {"country": "Ukraine", "ar": "أوكرانيا", "iso": "UA", "bot": "NumberNest_2_Bot"},
    {"country": "Uzbekistan", "ar": "أوزبكستان", "iso": "UZ", "bot": "NumberNest_2_Bot"},
    {"country": "Vietnam", "ar": "فيتنام", "iso": "VN", "bot": "NumberNest_2_Bot"},
    # smslybot
    {"country": "Egypt", "ar": "مصر (سيرفر 2)", "iso": "EG", "bot": "smslybot"},
    {"country": "Italy", "ar": "إيطاليا (سيرفر 2)", "iso": "IT", "bot": "smslybot"},
    {"country": "Pakistan", "ar": "باكستان (سيرفر 2)", "iso": "PK", "bot": "smslybot"},
    {"country": "Russia", "ar": "روسيا", "iso": "RU", "bot": "smslybot"},
    {"country": "Georgia", "ar": "جورجيا", "iso": "GE", "bot": "smslybot"},
    {"country": "Bolivia", "ar": "بوليفيا", "iso": "BO", "bot": "smslybot"},
    {"country": "Cuba", "ar": "كوبا", "iso": "CU", "bot": "smslybot"},
    {"country": "Venezuela", "ar": "فنزويلا", "iso": "VE", "bot": "smslybot"},
    {"country": "Guinea", "ar": "غينيا", "iso": "GN", "bot": "smslybot"},
    {"country": "Laos", "ar": "لاوس", "iso": "LA", "bot": "smslybot"},
    {"country": "Maldives", "ar": "المالديف", "iso": "MV", "bot": "smslybot"},
    {"country": "Mali", "ar": "مالي (سيرفر 2)", "iso": "ML", "bot": "smslybot"},
    {"country": "Senegal", "ar": "السنغال", "iso": "SN", "bot": "smslybot"},
    {"country": "Timor Leste", "ar": "تيمور الشرقية", "iso": "TL", "bot": "smslybot"},
    {"country": "Togo", "ar": "توغو", "iso": "TG", "bot": "smslybot"},
    {"country": "Zambia", "ar": "زامبيا", "iso": "ZM", "bot": "smslybot"},
]


@dataclass
class NumberItem:
    phone: str
    country: str
    bot_username: str
    status: str = "AVAILABLE"
    reserved_by: Optional[str] = None
    reserved_at: float = 0.0
    otp_code: Optional[str] = None


@dataclass
class BotState:
    username: str
    locked: bool = False
    active_country: Optional[str] = None
    last_message_id: Optional[int] = None
    numbers: List[NumberItem] = field(default_factory=list)


class TelegramNumberManager:
    def __init__(self):
        self.client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        self.bots: Dict[str, BotState] = {b: BotState(username=b) for b in BOT_USERNAMES}
        self._op_locks: Dict[str, asyncio.Lock] = {b: asyncio.Lock() for b in BOT_USERNAMES}
        self.last_trace: Dict[str, List[dict]] = {b: [] for b in BOT_USERNAMES}
        self.http = httpx.AsyncClient(timeout=10.0)

    async def start(self):
        await self.client.start()
        self._register_otp_listeners()

    async def stop(self):
        await self.http.aclose()
        await self.client.disconnect()

    def get_countries_catalog(self) -> List[dict]:
        self._cleanup_expired_locks()
        result = []
        for entry in COUNTRIES_CATALOG:
            bot_state = self.bots[entry["bot"]]
            result.append({
                **entry,
                "bot_busy": bot_state.locked,
            })
        return result

    def _register_otp_listeners(self):
        monitored_chats = OTP_GROUPS + BOT_USERNAMES

        @self.client.on(events.NewMessage(chats=monitored_chats))
        async def otp_handler(event):
            if getattr(event.message, "out", False):
                return
            text = event.raw_text or ""
            search_pool = text
            if event.message and event.message.buttons:
                for row in event.message.buttons:
                    for btn in row:
                        search_pool += " " + (btn.text or "")

            otp_match = re.search(r"\b(\d{3}[-\s]?\d{3})\b", search_pool)
            if not otp_match:
                return

            clean_otp = re.sub(r"\D", "", otp_match.group(1))
            sender_chat = await event.get_chat()
            chat_username = getattr(sender_chat, "username", "") or ""

            for bot_state in self.bots.values():
                for item in bot_state.numbers:
                    if item.status != "RESERVED":
                        continue

                    last4 = item.phone[-4:]
                    if chat_username in OTP_GROUPS:
                        if last4 in re.sub(r"\s+", "", text):
                            item.otp_code = clean_otp
                            item.status = "COMPLETED"
                            return
                    elif chat_username.lower() == item.bot_username.lower():
                        if self._is_noise_message(event.message):
                            if last4 in re.sub(r"\s+", "", text):
                                item.otp_code = clean_otp
                                item.status = "COMPLETED"
                                return
                        else:
                            item.otp_code = clean_otp
                            item.status = "COMPLETED"
                            return

    def _is_noise_message(self, msg: Optional[Message]) -> bool:
        if not msg:
            return False
        text = (msg.raw_text or "").lower()
        noise_keywords = ["messga otp received", "otp received", "otp code:", "╭──────"]
        if any(k in text for k in noise_keywords):
            return True
        if msg.buttons:
            btn_texts = " ".join((b.text or "").lower() for row in msg.buttons for b in row)
            if "panel" in btn_texts and "developer" in btn_texts:
                return True
        return False

    def _has_button(self, msg: Optional[Message], text_contains: str) -> bool:
        if not msg or not msg.buttons:
            return False
        for row in msg.buttons:
            for btn in row:
                if text_contains.lower() in (btn.text or "").lower():
                    return True
        return False

    async def _send_and_wait(self, bot: str, text: str, timeout: int = 10) -> Optional[Message]:
        entity = await self.client.get_entity(bot)
        fut = asyncio.get_running_loop().create_future()

        async def handler(event):
            if getattr(event.message, "out", False) or self._is_noise_message(event.message):
                return
            if not fut.done():
                fut.set_result(event.message)

        self.client.add_event_handler(handler, events.NewMessage(chats=entity))
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
        msg: Optional[Message],
        flat_index: Optional[int] = None,
        text_contains: Optional[str] = None,
        timeout: int = 12,
    ) -> Optional[Message]:
        if not msg or not msg.buttons:
            return None

        target_rc = None
        if text_contains:
            for r_idx, b_row in enumerate(msg.buttons):
                for c_idx, btn in enumerate(b_row):
                    if text_contains.lower() in (btn.text or "").lower():
                        target_rc = (r_idx, c_idx)
                        break
                if target_rc:
                    break
            if not target_rc:
                return None
        elif flat_index is None:
            return None

        entity = await self.client.get_entity(bot)
        fut = asyncio.get_running_loop().create_future()

        async def handler(event):
            if getattr(event.message, "out", False) or self._is_noise_message(event.message):
                return
            if not fut.done():
                fut.set_result(event.message)

        self.client.add_event_handler(handler, events.NewMessage(chats=entity))
        self.client.add_event_handler(handler, events.MessageEdited(chats=entity))

        async def do_click():
            if target_rc is not None:
                return await msg.click(target_rc[0], target_rc[1])
            return await msg.click(flat_index)

        click_task = asyncio.create_task(do_click())
        try:
            done, _ = await asyncio.wait(
                {click_task, fut},
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )
            res = None
            if fut in done:
                res = fut.result()
                if not click_task.done():
                    click_task.cancel()
            else:
                if not click_task.done():
                    click_task.cancel()
                try:
                    res = await asyncio.wait_for(fut, timeout=6)
                except asyncio.TimeoutError:
                    return None

            if res and not res.buttons and not self._extract_phones_from_msg(res):
                fut2 = asyncio.get_running_loop().create_future()
                async def handler2(ev):
                    if getattr(ev.message, "out", False) or self._is_noise_message(ev.message):
                        return
                    if not fut2.done():
                        fut2.set_result(ev.message)
                self.client.add_event_handler(handler2, events.NewMessage(chats=entity))
                self.client.add_event_handler(handler2, events.MessageEdited(chats=entity))
                try:
                    res = await asyncio.wait_for(fut2, timeout=6)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self.client.remove_event_handler(handler2)

            return res
        finally:
            self.client.remove_event_handler(handler)
            if not click_task.done():
                click_task.cancel()

    def _extract_phones(self, text: str) -> List[str]:
        if not text:
            return []
        raw_matches = re.findall(r"\+?\d[\d\s\-]{7,16}\d", text)
        phones = []
        for m in raw_matches:
            digits = re.sub(r"\D", "", m)
            if 8 <= len(digits) <= 15:
                phones.append("+" + digits)
        return list(dict.fromkeys(phones))

    def _extract_phones_from_msg(self, msg: Optional[Message]) -> List[str]:
        if not msg:
            return []
        sources = [msg.raw_text or ""]
        if msg.buttons:
            for row in msg.buttons:
                for btn in row:
                    if btn.text:
                        sources.append(btn.text)
        return self._extract_phones("\n".join(sources))

    async def is_registered_on_whatsapp(self, phone: str) -> bool:
        if not WA_CHECKER_URL:
            return False
        try:
            await asyncio.sleep(2.5)
            resp = await self.http.get(WA_CHECKER_URL, params={"phone": phone.lstrip("+")})
            data = resp.json()
            return bool(data.get("registered", False))
        except Exception:
            return True

    async def _filter_fresh_numbers(self, phones: List[str], country: str, bot_username: str) -> List[NumberItem]:
        fresh = []
        for p in phones:
            is_reg = await self.is_registered_on_whatsapp(p)
            if not is_reg:
                fresh.append(NumberItem(phone=p, country=country, bot_username=bot_username))
        return fresh

    async def fetch_from_bot(
        self,
        bot_username: str,
        country: Optional[str] = None,
        force_refresh: bool = False,
        max_retries: int = 3,
    ) -> List[NumberItem]:
        state = self.bots[bot_username]
        if state.locked:
            return state.numbers

        async with self._op_locks[bot_username]:
            target_country = country or "Default"
            # نعيد الأرقام المحفوظة فقط إذا كانت لنفس الدولة المطلوبة ولم يُطلب تحديث جديد
            if (
                not force_refresh
                and state.active_country
                and state.active_country.lower() == target_country.lower()
            ):
                available_now = [n for n in state.numbers if n.status == "AVAILABLE"]
                if available_now:
                    return available_now

            msg = None
            if bot_username == "B_M_Numbers_Files_bot":
                target_country = "Yemen"
                m1 = await self._send_and_wait(bot_username, "/getnumber")
                m2 = await self._click_and_wait(bot_username, m1, text_contains="whats") if m1 else None
                msg = await self._click_and_wait(bot_username, m2, text_contains="yemen") if m2 else None

            elif bot_username == "smslybot":
                target_country = country or "Egypt"
                m1 = await self._send_and_wait(bot_username, "Get Number")
                m2 = await self._click_and_wait(bot_username, m1, text_contains="WhatsApp") if m1 else None
                msg = await self._click_and_wait(bot_username, m2, text_contains=target_country) if m2 else None

            elif bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
                target_country = country or "Pakistan"
                m1 = await self._send_and_wait(bot_username, "/start")
                m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Number") if m1 else None
                m3 = await self._click_and_wait(bot_username, m2, text_contains="whatsapp") if m2 else None
                # بدون الرجوع لـ index 0 حتى لا يعطي باكستان لو اختار المستخدم السودان ولم تتوفر
                msg = await self._click_and_wait(bot_username, m3, text_contains=target_country) if m3 else None

            elif bot_username == "NumberNest_2_Bot":
                target_country = country or "Italy"
                m1 = await self._send_and_wait(bot_username, "/start")
                if m1 and self._has_button(m1, "Get Number"):
                    m1 = await self._click_and_wait(bot_username, m1, text_contains="Get Number")
                m2 = await self._click_and_wait(bot_username, m1, text_contains=target_country) if m1 else None
                if m2 and self._extract_phones_from_msg(m2):
                    msg = m2
                elif m2:
                    msg = await self._click_and_wait(bot_username, m2, flat_index=0)

            elif bot_username == "JXOTPBot":
                target_country = "Cambodia"
                m1 = await self._send_and_wait(bot_username, "/start")
                m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Numbers") if m1 else None
                m3 = await self._click_and_wait(bot_username, m2, text_contains="whats") if m2 else None
                msg = await self._click_and_wait(bot_username, m3, text_contains="cambodia") if m3 else None

            fresh_items: List[NumberItem] = []
            for _ in range(max_retries):
                if not msg:
                    break
                phones = self._extract_phones_from_msg(msg)
                fresh_items = await self._filter_fresh_numbers(phones, target_country, bot_username)
                if fresh_items:
                    break

                next_msg = (
                    await self._click_and_wait(bot_username, msg, text_contains="change number")
                    or await self._click_and_wait(bot_username, msg, text_contains="تغيير")
                    or await self._click_and_wait(bot_username, msg, text_contains="جديد")
                    or await self._click_and_wait(bot_username, msg, text_contains="new number")
                    or await self._click_and_wait(bot_username, msg, flat_index=0)
                )
                msg = next_msg

            state.active_country = target_country
            state.numbers = fresh_items
            state.last_message_id = msg.id if msg else None
            return fresh_items

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
                    state.locked = True
                    return item
        return None

    def release_bot(self, bot_username: str):
        state = self.bots.get(bot_username)
        if state:
            state.locked = False
            state.active_country = None
            state.numbers = []

    def _cleanup_expired_locks(self, ttl_seconds: int = 300):
        now = time.time()
        for state in self.bots.values():
            if state.locked:
                reserved = [n for n in state.numbers if n.status == "RESERVED"]
                if reserved and (now - reserved[0].reserved_at) > ttl_seconds:
                    state.locked = False
                    state.active_country = None
                    state.numbers = []
