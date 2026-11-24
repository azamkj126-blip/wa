import asyncio
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import httpx
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession
from telethon.tl.custom import Message
from telethon.tl.types import ReplyInlineMarkup, ReplyKeyboardMarkup

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

COUNTRIES_CATALOG = [
    {"country": "Yemen", "ar": "اليمن", "iso": "YE", "bot": "B_M_Numbers_Files_bot"},
    {"country": "Sudan", "ar": "السودان", "iso": "SD", "bot": "SOJIB_BRO_FRESH_NUMBER_BOT"},
    {"country": "Pakistan", "ar": "باكستان", "iso": "PK", "bot": "SOJIB_BRO_FRESH_NUMBER_BOT"},
    {"country": "Cambodia", "ar": "كمبوديا", "iso": "KH", "bot": "JXOTPBot"},
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


COUNTRY_ALIASES: Dict[str, List[str]] = {
    "yemen": ["yemen", "اليمن"],
    "sudan": ["sudan", "السودان"],
    "pakistan": ["pakistan", "باكستان"],
    "cambodia": ["cambodia", "كمبوديا"],
    "egypt": ["egypt", "مصر"],
    "syria": ["syria", "سوريا"],
    "lebanon": ["lebanon", "لبنان"],
    "italy": ["italy", "إيطاليا", "ايطاليا"],
    "ethiopia": ["ethiopia", "إثيوبيا", "اثيوبيا"],
    "malaysia": ["malaysia", "ماليزيا"],
    "mali": ["mali", "مالي"],
    "ukraine": ["ukraine", "أوكرانيا", "اوكرانيا"],
    "uzbekistan": ["uzbekistan", "أوزبكستان", "اوزبكستان"],
    "vietnam": ["vietnam", "فيتنام"],
    "russia": ["russia", "روسيا"],
    "georgia": ["georgia", "جورجيا"],
    "bolivia": ["bolivia", "بوليفيا"],
    "cuba": ["cuba", "كوبا"],
    "venezuela": ["venezuela", "فنزويلا"],
    "guinea": ["guinea", "غينيا"],
    "laos": ["laos", "لاوس"],
    "maldives": ["maldives", "المالديف"],
    "senegal": ["senegal", "السنغال"],
    "timor leste": ["timor", "تيمور"],
    "togo": ["togo", "توغو"],
    "zambia": ["zambia", "زامبيا"],
}


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
        self._entities: Dict[str, Any] = {}
        self.last_errors: Dict[str, str] = {}
        self.last_trace: Dict[str, List[dict]] = {b: [] for b in BOT_USERNAMES}
        self.authorized: bool = False
        self._listeners_registered: bool = False
        self._ready_event = asyncio.Event()
        self._startup_task: Optional[asyncio.Task] = None
        self.http = httpx.AsyncClient(timeout=10.0)

    async def start(self, delay_seconds: int = 15):
        self._startup_task = asyncio.create_task(self._delayed_connect(delay_seconds))

    async def _delayed_connect(self, delay_seconds: int):
        try:
            await asyncio.sleep(delay_seconds)
            await self.client.connect()
            self.authorized = await self.client.is_user_authorized()
            if self.authorized:
                self._register_otp_listeners()
                print("Telegram connected and authorized successfully.")
            else:
                self.last_errors["startup"] = "TG_STRING_SESSION منتهية أو ملغاة، تحتاج تجديد"
                print("ERROR: TG_STRING_SESSION is invalid or revoked.")
        except Exception as e:
            self.authorized = False
            self.last_errors["startup"] = f"{type(e).__name__}: {e}"
            print(f"Telegram startup error: {e}")
        finally:
            self._ready_event.set()

    async def stop(self):
        if self._startup_task and not self._startup_task.done():
            self._startup_task.cancel()
        await self.http.aclose()
        if self.client.is_connected():
            await self.client.disconnect()

    async def _ensure_connected(self):
        if not self._ready_event.is_set():
            try:
                await asyncio.wait_for(self._ready_event.wait(), timeout=20)
            except asyncio.TimeoutError:
                pass
        if not self.client.is_connected():
            await self.client.connect()
        if not self.authorized:
            self.authorized = await self.client.is_user_authorized()
            if self.authorized:
                self._register_otp_listeners()
        if not self.authorized:
            raise RuntimeError("جلسة تيليجرام منتهية، يرجى تجديد TG_STRING_SESSION")

    async def _get_entity_cached(self, username: str):
        await self._ensure_connected()
        if username not in self._entities:
            self._entities[username] = await self.client.get_entity(username)
        return self._entities[username]

    def get_countries_catalog(self) -> List[dict]:
        self._cleanup_expired_locks()
        return [
            {**entry, "bot_busy": self.bots[entry["bot"]].locked}
            for entry in COUNTRIES_CATALOG
        ]

    def _register_otp_listeners(self):
        if self._listeners_registered:
            return
        self._listeners_registered = True
        monitored_chats = OTP_GROUPS + BOT_USERNAMES

        @self.client.on(events.NewMessage(chats=monitored_chats))
        async def otp_handler(event):
            try:
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
            except Exception:
                pass

    def _is_noise_message(self, msg: Optional[Message]) -> bool:
        if not msg:
            return False
        text = (msg.raw_text or "").lower()
        noise_keywords = [
            "messga otp received",
            "otp received",
            "otp code:",
            "╭──────",
            "استخدم كيبورد البوت",
        ]
        if any(k in text for k in noise_keywords):
            return True
        if msg.buttons:
            btn_texts = " ".join((b.text or "").lower() for row in msg.buttons for b in row)
            if "panel" in btn_texts and "developer" in btn_texts:
                return True
        return False

    def _button_signature(self, msg: Optional[Message]) -> Tuple[str, ...]:
        """توقيع مبسّط للأزرار (بدون الأرقام المتغيرة) لاكتشاف الرسائل المكررة"""
        if not msg or not msg.buttons:
            return ()
        sig = []
        for row in msg.buttons:
            for btn in row:
                normalized = re.sub(r"\d+", "", (btn.text or "").lower()).strip()
                sig.append(re.sub(r"\s+", " ", normalized))
        return tuple(sig)

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
            "text": (msg.raw_text or "")[:200],
            "buttons": btns[:20],
        }

    def _find_button_rc(self, msg: Optional[Message], keywords: List[str]) -> Optional[Tuple[int, int]]:
        if not msg or not msg.buttons:
            return None
        expanded = list(keywords)
        for kw in keywords:
            aliases = COUNTRY_ALIASES.get(kw.lower(), [])
            expanded.extend(aliases)

        for kw in expanded:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue
            for r_idx, row in enumerate(msg.buttons):
                for c_idx, btn in enumerate(row):
                    btn_text = (btn.text or "").strip().lower()
                    if kw_clean in btn_text:
                        return (r_idx, c_idx)
        return None

    def _find_first_non_back_rc(self, msg: Optional[Message]) -> Optional[Tuple[int, int]]:
        if not msg or not msg.buttons:
            return None
        for r_idx, row in enumerate(msg.buttons):
            for c_idx, btn in enumerate(row):
                txt = (btn.text or "").lower()
                if "رجوع" in txt or "back" in txt or "⬅" in txt or "🔙" in txt:
                    continue
                return (r_idx, c_idx)
        return None

    async def _safe_reset_bot(self, bot_username: str):
        try:
            entity = await self._get_entity_cached(bot_username)
            await self.client.send_message(entity, "/start")
        except Exception:
            pass

    async def _send_and_wait(self, bot: str, text: str, timeout: int = 10) -> Optional[Message]:
        entity = await self._get_entity_cached(bot)
        fut = asyncio.get_running_loop().create_future()

        async def handler(event):
            if getattr(event.message, "out", False) or self._is_noise_message(event.message):
                return
            if not fut.done():
                fut.set_result(event.message)

        self.client.add_event_handler(handler, events.NewMessage(chats=entity))
        self.client.add_event_handler(handler, events.MessageEdited(chats=entity))
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
        rc: Optional[Tuple[int, int]] = None,
        timeout: int = 10,
    ) -> Optional[Message]:
        if not msg or not msg.buttons:
            return None

        target_rc = rc
        if target_rc is None and text_contains:
            target_rc = self._find_button_rc(msg, [text_contains])
            # If not found on current page, check for Next / >> pagination button
            if not target_rc:
                next_rc = self._find_button_rc(msg, ["next", ">>", "التالي", "➡️", ">"])
                if next_rc:
                    try:
                        p2 = await msg.click(next_rc[0], next_rc[1])
                        if p2 and p2.buttons:
                            msg = p2
                            target_rc = self._find_button_rc(msg, [text_contains])
                    except Exception:
                        pass
            if not target_rc:
                return None
        elif target_rc is None and flat_index is None:
            return None

        is_inline_click = isinstance(msg.reply_markup, ReplyInlineMarkup)
        prev_sig = self._button_signature(msg)

        entity = await self._get_entity_cached(bot)
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        async def handler(event):
            ev_msg = event.message
            if getattr(ev_msg, "out", False) or self._is_noise_message(ev_msg):
                return
            # تجاهل رسائل الكيبورد السفلي عندما نضغط على زر Inline
            if is_inline_click and isinstance(ev_msg.reply_markup, ReplyKeyboardMarkup):
                return
            # تجاهل التعديلات/الرسائل المكررة التي تحمل نفس الأزرار بدون أرقام
            new_sig = self._button_signature(ev_msg)
            if new_sig and new_sig == prev_sig and not self._extract_phones_from_msg(ev_msg):
                return
            if not fut.done():
                fut.set_result(ev_msg)

        self.client.add_event_handler(handler, events.NewMessage(chats=entity))
        self.client.add_event_handler(handler, events.MessageEdited(chats=entity))

        async def do_click():
            if target_rc is not None:
                return await msg.click(target_rc[0], target_rc[1])
            return await msg.click(flat_index)

        click_task = asyncio.create_task(do_click())
        try:
            deadline = loop.time() + timeout
            while not fut.done():
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                if click_task.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(fut), timeout=remaining)
                    except asyncio.TimeoutError:
                        pass
                    break
                await asyncio.wait(
                    {click_task, fut},
                    timeout=remaining,
                    return_when=asyncio.FIRST_COMPLETED,
                )

            if not fut.done():
                return None

            res = fut.result()

            if res and not res.buttons and not self._extract_phones_from_msg(res):
                fut2 = loop.create_future()

                async def handler2(ev):
                    ev_msg = ev.message
                    if getattr(ev_msg, "out", False) or self._is_noise_message(ev_msg):
                        return
                    if is_inline_click and isinstance(ev_msg.reply_markup, ReplyKeyboardMarkup):
                        return
                    if not fut2.done():
                        fut2.set_result(ev_msg)

                self.client.add_event_handler(handler2, events.NewMessage(chats=entity))
                self.client.add_event_handler(handler2, events.MessageEdited(chats=entity))
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
            if not click_task.done():
                click_task.cancel()
            else:
                try:
                    click_task.exception()
                except Exception:
                    pass

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
            await asyncio.sleep(1.5)
            resp = await self.http.get(WA_CHECKER_URL, params={"phone": phone.lstrip("+")})
            data = resp.json()
            return bool(data.get("registered", False))
        except Exception:
            return True

    async def _filter_fresh_numbers(self, phones: List[str], country: str, bot_username: str) -> List[NumberItem]:
        fresh = []
        for p in phones:
            if not await self.is_registered_on_whatsapp(p):
                fresh.append(NumberItem(phone=p, country=country, bot_username=bot_username))
        return fresh

    async def fetch_from_bot(
        self,
        bot_username: str,
        country: Optional[str] = None,
        force_refresh: bool = False,
        max_retries: int = 2,
    ) -> Tuple[List[NumberItem], Optional[str]]:
        state = self.bots[bot_username]
        if state.locked:
            return state.numbers, "هذا البوت محجوز حالياً لمستخدم آخر"

        try:
            await asyncio.wait_for(self._op_locks[bot_username].acquire(), timeout=5.0)
        except asyncio.TimeoutError:
            return [], "البوت مشغول بطلب آخر حالياً، حاول بعد ثوانٍ"

        try:
            return await asyncio.wait_for(
                self._fetch_from_bot_locked(bot_username, country, force_refresh, max_retries),
                timeout=22.0,
            )
        except asyncio.TimeoutError:
            err = "انتهت مهلة استجابة البوت، حاول مجدداً"
            self.last_errors[bot_username] = err
            return [], err
        finally:
            self._op_locks[bot_username].release()

    async def _fetch_from_bot_locked(
        self,
        bot_username: str,
        country: Optional[str],
        force_refresh: bool,
        max_retries: int,
    ) -> Tuple[List[NumberItem], Optional[str]]:
        state = self.bots[bot_username]
        target_country = country or "Default"

        if (
            not force_refresh
            and state.active_country
            and state.active_country.lower() == target_country.lower()
        ):
            available_now = [n for n in state.numbers if n.status == "AVAILABLE"]
            if available_now:
                return available_now, None

        self.last_errors.pop(bot_username, None)
        trace: List[dict] = []
        self.last_trace[bot_username] = trace
        msg = None

        try:
            if bot_username == "B_M_Numbers_Files_bot":
                target_country = "Yemen"
                m1 = await self._send_and_wait(bot_username, "/getnumber")
                trace.append(self._serialize_msg("1: /getnumber", m1))
                m2 = await self._click_and_wait(bot_username, m1, text_contains="whats") if m1 else None
                trace.append(self._serialize_msg("2: WhatsApp", m2))
                msg = await self._click_and_wait(bot_username, m2, text_contains="yemen") if m2 else None
                trace.append(self._serialize_msg("3: Yemen", msg))

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
                m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Number") if m1 else None
                trace.append(self._serialize_msg("2: Get Number", m2))
                m3 = await self._click_and_wait(bot_username, m2, text_contains="whatsapp") if m2 else None
                trace.append(self._serialize_msg("3: WHATSAPP", m3))
                msg = await self._click_and_wait(bot_username, m3, text_contains=target_country) if m3 else None
                trace.append(self._serialize_msg(f"4: {target_country}", msg))

            elif bot_username == "NumberNest_2_Bot":
                target_country = country or "Italy"
                m1 = await self._send_and_wait(bot_username, "/start")
                trace.append(self._serialize_msg("1: /start", m1))
                if m1 and self._find_button_rc(m1, ["Get Number"]):
                    m1 = await self._click_and_wait(bot_username, m1, text_contains="Get Number")
                    trace.append(self._serialize_msg("1b: Get Number", m1))
                m2 = await self._click_and_wait(bot_username, m1, text_contains=target_country) if m1 else None
                trace.append(self._serialize_msg(f"2: {target_country}", m2))
                if m2 and self._extract_phones_from_msg(m2):
                    msg = m2
                elif m2:
                    branch_rc = self._find_first_non_back_rc(m2)
                    if branch_rc:
                        msg = await self._click_and_wait(bot_username, m2, rc=branch_rc)
                        trace.append(self._serialize_msg("3: Branch", msg))
                    else:
                        trace.append({"step": "3: Branch", "error": "No available branch"})

            elif bot_username == "JXOTPBot":
                target_country = "Cambodia"
                m1 = await self._send_and_wait(bot_username, "/start")
                trace.append(self._serialize_msg("1: /start", m1))
                m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Numbers") if m1 else None
                trace.append(self._serialize_msg("2: Get Numbers", m2))
                m3 = await self._click_and_wait(bot_username, m2, text_contains="whats") if m2 else None
                trace.append(self._serialize_msg("3: WhatsApp", m3))
                msg = await self._click_and_wait(bot_username, m3, text_contains="cambodia") if m3 else None
                trace.append(self._serialize_msg(f"4: {target_country}", msg))

        except FloodWaitError as e:
            err = f"تيليجرام طلب الانتظار {e.seconds} ثانية قبل الطلب مجدداً"
            self.last_errors[bot_username] = err
            return [], err
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            self.last_errors[bot_username] = err
            return [], str(e) if "جلسة تيليجرام" in str(e) else "تعذر الاتصال ببوت الأرقام حالياً، حاول مرة أخرى"

        if not msg:
            asyncio.create_task(self._safe_reset_bot(bot_username))
            err = "الدولة غير متوفرة حالياً في هذا البوت أو لم يستجب البوت"
            self.last_errors[bot_username] = err
            return [], err

        fresh_items: List[NumberItem] = []
        for _ in range(max_retries):
            phones = self._extract_phones_from_msg(msg)
            fresh_items = await self._filter_fresh_numbers(phones, target_country, bot_username)
            if fresh_items:
                break
            change_rc = self._find_button_rc(
                msg, ["change number", "تغيير الرقم", "تغيير", "رقم جديد", "new number"]
            )
            if not change_rc:
                break
            msg = await self._click_and_wait(bot_username, msg, rc=change_rc)
            if not msg:
                break

        state.active_country = target_country
        state.numbers = fresh_items
        state.last_message_id = msg.id if msg else None
        if not fresh_items:
            return [], "لم تتوفر أرقام جديدة حالياً لهذه الدولة"
        return fresh_items, None

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
