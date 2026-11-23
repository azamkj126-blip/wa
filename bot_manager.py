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
                        item.otp_code = clean_otp
                        item.status = "COMPLETED"
                        return

    def _serialize_msg(self, step: str, msg: Optional[Message]) -> dict:
        if not msg:
            return {"step": step, "error": "No response / Timeout"}
        btns = []
        if msg.buttons:
            for r, row in enumerate(msg.buttons):
                for c, btn in enumerate(row):
                    btns.append(f"[{r},{c}] {btn.text}")
        return {
            "step": step,
            "text": (msg.raw_text or "")[:300],
            "buttons": btns,
        }

    async def _send_and_wait(self, bot: str, text: str, timeout: int = 8) -> Optional[Message]:
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
        timeout: int = 8,
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

            res = await asyncio.wait_for(fut, timeout=timeout)
            # إذا كانت الرسالة مجرد "انتظر/جاري التحميل" بدون أزرار أو أرقام، ننتظر الرسالة التالية
            if res and not res.buttons and not self._extract_phones(res.raw_text):
                fut2 = asyncio.get_running_loop().create_future()
                async def handler2(ev):
                    if not fut2.done():
                        fut2.set_result(ev.message)
                self.client.add_event_handler(handler2, events.NewMessage(from_users=entity))
                self.client.add_event_handler(handler2, events.MessageEdited(from_users=entity))
                try:
                    res = await asyncio.wait_for(fut2, timeout=5)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self.client.remove_event_handler(handler2)
            return res
        except Exception:
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
        return list(dict.fromkeys(phones))

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

    async def fetch_from_bot(self, bot_username: str, country: Optional[str] = None, max_retries: int = 2) -> List[NumberItem]:
        state = self.bots[bot_username]
        if state.locked:
            return state.numbers

        async with self._op_locks[bot_username]:
            available_now = [n for n in state.numbers if n.status == "AVAILABLE"]
            if available_now:
                return available_now

            trace: List[dict] = []
            msg = None
            target_country = country or "Default"

            try:
                if bot_username == "B_M_Numbers_Files_bot":
                    target_country = "Yemen"
                    m1 = await self._send_and_wait(bot_username, "/getnumber")
                    trace.append(self._serialize_msg("1: /getnumber", m1))
                    m2 = await self._click_and_wait(bot_username, m1, flat_index=2) if m1 else None
                    trace.append(self._serialize_msg("2: WhatsApp btn", m2))
                    msg = await self._click_and_wait(bot_username, m2, flat_index=0) if m2 else None
                    trace.append(self._serialize_msg("3: Yemen btn", msg))

                elif bot_username == "smslybot":
                    target_country = country or "Egypt"
                    m1 = await self._send_and_wait(bot_username, "Get Number")
                    trace.append(self._serialize_msg("1: Get Number", m1))
                    m2 = await self._click_and_wait(bot_username, m1, text_contains="WhatsApp") if m1 else None
                    trace.append(self._serialize_msg("2: WhatsApp", m2))
                    msg = await self._click_and_wait(bot_username, m2, text_contains=target_country) if m2 else None
                    trace.append(self._serialize_msg(f"3: {target_country}", msg))

                elif bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
                    target_country = country or "Pakistan"
                    m1 = await self._send_and_wait(bot_username, "/start")
                    trace.append(self._serialize_msg("1: /start", m1))
                    m2 = await self._click_and_wait(bot_username, m1, flat_index=0) if m1 else None
                    trace.append(self._serialize_msg("2: WhatsApp", m2))
                    msg = await self._click_and_wait(bot_username, m2, text_contains=target_country) if m2 else None
                    trace.append(self._serialize_msg(f"3: {target_country}", msg))

                elif bot_username == "NumberNest_2_Bot":
                    target_country = country or "Italy"
                    m1 = await self._send_and_wait(bot_username, "/start")
                    trace.append(self._serialize_msg("1: /start", m1))
                    m2 = await self._click_and_wait(bot_username, m1, text_contains=target_country) if m1 else None
                    trace.append(self._serialize_msg(f"2: {target_country}", m2))
                    msg = await self._click_and_wait(bot_username, m2, flat_index=0) if m2 else None
                    trace.append(self._serialize_msg("3: Server 1", msg))

                elif bot_username == "JXOTPBot":
                    target_country = "Cambodia"
                    m1 = await self._send_and_wait(bot_username, "/start")
                    trace.append(self._serialize_msg("1: /start", m1))
                    m2 = await self._click_and_wait(bot_username, m1, flat_index=0) if m1 else None
                    trace.append(self._serialize_msg("2: WhatsApp", m2))
                    msg = await self._click_and_wait(bot_username, m2, flat_index=0) if m2 else None
                    trace.append(self._serialize_msg("3: Cambodia", msg))
            except Exception as e:
                trace.append({"step": "exception", "error": str(e)})

            self.last_trace[bot_username] = trace

            fresh_items: List[NumberItem] = []
            for _ in range(max_retries):
                if not msg:
                    break
                phones = self._extract_phones(msg.raw_text)
                fresh_items = await self._filter_fresh_numbers(phones, target_country, bot_username)
                if fresh_items:
                    break

                if bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
                    msg = await self._click_and_wait(bot_username, msg, flat_index=1)
                else:
                    next_msg = (
                        await self._click_and_wait(bot_username, msg, text_contains="تغيير")
                        or await self._click_and_wait(bot_username, msg, text_contains="جديد")
                        or await self._click_and_wait(bot_username, msg, text_contains="change")
                        or await self._click_and_wait(bot_username, msg, flat_index=0)
                    )
                    msg = next_msg

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
        msg = await self._send_and_wait(bot_username, command)
        if not msg:
            return {"error": "No response from bot"}
        buttons = []
        if msg.buttons:
            for r, row in enumerate(msg.buttons):
                for c, btn in enumerate(row):
                    buttons.append({"row": r, "col": c, "text": btn.text})
        return {"text": msg.raw_text, "buttons": buttons}
