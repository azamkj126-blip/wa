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

BOT_USERNAMES = [
    "B_M_Numbers_Files_bot",
    "smslybot",
    "SOJIB_BRO_FRESH_NUMBER_BOT",
    "NumberNest_2_Bot",
    "JXOTPBot",
    "seven1tel_Number_Bot",
]

COUNTRY_DB: Dict[str, Tuple[str, str, str]] = {
    "yemen": ("Yemen", "اليمن", "YE"),
    "sudan": ("Sudan", "السودان", "SD"),
    "egypt": ("Egypt", "مصر", "EG"),
    "saudi arabia": ("Saudi Arabia", "السعودية", "SA"),
    "saudi": ("Saudi Arabia", "السعودية", "SA"),
    "jordan": ("Jordan", "الأردن", "JO"),
    "syria": ("Syria", "سوريا", "SY"),
    "lebanon": ("Lebanon", "لبنان", "LB"),
    "iraq": ("Iraq", "العراق", "IQ"),
    "palestine": ("Palestine", "فلسطين", "PS"),
    "kuwait": ("Kuwait", "الكويت", "KW"),
    "uae": ("UAE", "الإمارات", "AE"),
    "united arab emirates": ("UAE", "الإمارات", "AE"),
    "qatar": ("Qatar", "قطر", "QA"),
    "bahrain": ("Bahrain", "البحرين", "BH"),
    "oman": ("Oman", "عمان", "OM"),
    "morocco": ("Morocco", "المغرب", "MA"),
    "algeria": ("Algeria", "الجزائر", "DZ"),
    "tunisia": ("Tunisia", "تونس", "TN"),
    "libya": ("Libya", "ليبيا", "LY"),
    "mauritania": ("Mauritania", "موريتانيا", "MR"),
    "somalia": ("Somalia", "الصومال", "SO"),
    "djibouti": ("Djibouti", "جيبوتي", "DJ"),
    "cambodia": ("Cambodia", "كمبوديا", "KH"),
    "senegal": ("Senegal", "السنغال", "SN"),
    "pakistan": ("Pakistan", "باكستان", "PK"),
    "india": ("India", "الهند", "IN"),
    "bangladesh": ("Bangladesh", "بنغلاديش", "BD"),
    "indonesia": ("Indonesia", "إندونيسيا", "ID"),
    "malaysia": ("Malaysia", "ماليزيا", "MY"),
    "vietnam": ("Vietnam", "فيتنام", "VN"),
    "philippines": ("Philippines", "الفلبين", "PH"),
    "thailand": ("Thailand", "تايلاند", "TH"),
    "laos": ("Laos", "لاوس", "LA"),
    "nepal": ("Nepal", "نيبال", "NP"),
    "turkey": ("Turkey", "تركيا", "TR"),
    "iran": ("Iran", "إيران", "IR"),
    "afghanistan": ("Afghanistan", "أفغانستان", "AF"),
    "uzbekistan": ("Uzbekistan", "أوزبكستان", "UZ"),
    "kazakhstan": ("Kazakhstan", "كازاخستان", "KZ"),
    "kyrgyzstan": ("Kyrgyzstan", "قيرغيزستان", "KG"),
    "tajikistan": ("Tajikistan", "طاجيكستان", "TJ"),
    "russia": ("Russia", "روسيا", "RU"),
    "ukraine": ("Ukraine", "أوكرانيا", "UA"),
    "georgia": ("Georgia", "جورجيا", "GE"),
    "germany": ("Germany", "ألمانيا", "DE"),
    "united kingdom": ("United Kingdom", "بريطانيا", "GB"),
    "italy": ("Italy", "إيطاليا", "IT"),
    "spain": ("Spain", "إسبانيا", "ES"),
    "france": ("France", "فرنسا", "FR"),
    "belgium": ("Belgium", "بلجيكا", "BE"),
    "montenegro": ("Montenegro", "الجبل الأسود", "ME"),
    "netherlands": ("Netherlands", "هولندا", "NL"),
    "poland": ("Poland", "بولندا", "PL"),
    "sweden": ("Sweden", "السويد", "SE"),
    "greece": ("Greece", "اليونان", "GR"),
    "united states": ("United States", "أمريكا", "US"),
    "usa": ("United States", "أمريكا", "US"),
    "canada": ("Canada", "كندا", "CA"),
    "brazil": ("Brazil", "البرازيل", "BR"),
    "colombia": ("Colombia", "كولومبيا", "CO"),
    "argentina": ("Argentina", "الأرجنتين", "AR"),
    "bolivia": ("Bolivia", "بوليفيا", "BO"),
    "cuba": ("Cuba", "كوبا", "CU"),
    "venezuela": ("Venezuela", "فنزويلا", "VE"),
    "haiti": ("Haiti", "هايتي", "HT"),
    "ethiopia": ("Ethiopia", "إثيوبيا", "ET"),
    "mali": ("Mali", "مالي", "ML"),
    "guinea": ("Guinea", "غينيا", "GN"),
    "togo": ("Togo", "توغو", "TG"),
    "zambia": ("Zambia", "زامبيا", "ZM"),
    "tanzania": ("Tanzania", "تانزانيا", "TZ"),
    "malawi": ("Malawi", "مالاوي", "MW"),
    "cote d'ivoire": ("Côte d'Ivoire", "كوت ديفوار", "CI"),
    "ivory coast": ("Côte d'Ivoire", "كوت ديفوار", "CI"),
    "côte d'ivoire": ("Côte d'Ivoire", "كوت ديفوار", "CI"),
    "mozambique": ("Mozambique", "موزمبيق", "MZ"),
    "maldives": ("Maldives", "المالديف", "MV"),
    "timor leste": ("Timor Leste", "تيمور الشرقية", "TL"),
    "timor": ("Timor Leste", "تيمور الشرقية", "TL"),
    "nigeria": ("Nigeria", "نيجيريا", "NG"),
    "kenya": ("Kenya", "كينيا", "KE"),
    "ghana": ("Ghana", "غانا", "GH"),
    "uganda": ("Uganda", "أوغندا", "UG"),
    "angola": ("Angola", "أنغولا", "AO"),
    "cameroon": ("Cameroon", "الكاميرون", "CM"),
}

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
    "germany": ["germany", "ألمانيا", "المانيا", "deutschland"],
    "united kingdom": ["united kingdom", "uk", "بريطانيا", "المملكة المتحدة"],
    "united states": ["united states", "usa", "us", "أمريكا", "امريكا"],
    "saudi arabia": ["saudi", "السعودية", "المملكة العربية السعودية"],
    "iraq": ["iraq", "العراق"],
    "jordan": ["jordan", "الأردن", "الاردن"],
    "turkey": ["turkey", "تركيا"],
    "morocco": ["morocco", "المغرب"],
    "algeria": ["algeria", "الجزائر"],
    "nepal": ["nepal", "نيبال"],
    "kazakhstan": ["kazakhstan", "كازاخستان"],
    "iran": ["iran", "إيران", "ايران"],
    "haiti": ["haiti", "هايتي"],
    "malawi": ["malawi", "مالاوي"],
    "côte d'ivoire": ["côte d'ivoire", "cote d'ivoire", "ivory coast", "كوت ديفوار", "كوتي"],
    "tanzania": ["tanzania", "تانزانيا"],
    "belgium": ["belgium", "بلجيكا"],
    "montenegro": ["montenegro", "الجبل الأسود"],
}

EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2705\u274c]"
)

NAV_KEYWORDS = [
    "back",
    "رجوع",
    "⬅",
    "🔙",
    "next",
    "prev",
    "previous",
    "التالي",
    "السابق",
    "➡️",
    "⬅️",
    ">>",
    "<<",
    "developer",
    "panel",
    "قناة",
    "الدعم",
    "support",
    "channel",
    "rules",
    "شروط",
    "مطور",
    "balance",
    "wallet",
    "top",
    "traffic",
    "services",
    "الخدمات",
    "القائمة",
    "menu",
]

BUSY_KEYWORDS = [
    "مشغول",
    "محجوز",
    "مستخدم",
    "مباع",
    "منتهي",
    "غير متاح",
    "نفد",
    "نفذ",
    "taken",
    "busy",
    "sold",
    "used",
    "reserved",
    "expired",
    "unavailable",
    "❌",
    "🚫",
    "⛔",
    "🔒",
    "✖",
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
    locked_at: float = 0.0
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
        self._scanner_task: Optional[asyncio.Task] = None
        self.http = httpx.AsyncClient(timeout=10.0)
        self._discovered_countries: Dict[str, List[dict]] = {b: [] for b in BOT_USERNAMES}
        self.completed_otps: Dict[str, dict] = {}

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
                self._scanner_task = asyncio.create_task(self.start_periodic_scanner())
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
        if self._scanner_task and not self._scanner_task.done():
            self._scanner_task.cancel()
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
                if not self._scanner_task or self._scanner_task.done():
                    self._scanner_task = asyncio.create_task(self.start_periodic_scanner())
        if not self.authorized:
            raise RuntimeError("جلسة تيليجرام منتهية، يرجى تجديد TG_STRING_SESSION")

    async def _get_entity_cached(self, username: str):
        await self._ensure_connected()
        if username not in self._entities:
            self._entities[username] = await self.client.get_entity(username)
        return self._entities[username]

    def parse_country_button(self, btn_text: str, bot_username: str) -> Optional[dict]:
        cleaned = EMOJI_PATTERN.sub("", btn_text).strip()
        if not cleaned:
            return None

        server_match = (
            re.search(r"\b(?:WS|Server|سيرفر)\s*([1-9]|Top)\b", cleaned, re.IGNORECASE)
            or re.search(r"\b[A-Za-z]+\s+([1-9])\s+[\d,]+", cleaned)
            or re.search(r"\b[A-Za-z]+\s+([1-9])\b(?!\s*[-\d,])", cleaned)
        )
        server_label = ""
        server_label_ar = ""
        if server_match:
            s_val = server_match.group(1).upper()
            server_label = f" (Server {s_val})"
            server_label_ar = f" (سيرفر {s_val})"

        lowered = cleaned.lower()
        for key, (en, ar, iso) in sorted(COUNTRY_DB.items(), key=lambda x: len(x[0]), reverse=True):
            if key in lowered:
                return {
                    "country": f"{en}{server_label}",
                    "ar": f"{ar}{server_label_ar}",
                    "iso": iso,
                    "bot": bot_username,
                    "raw_button": btn_text,
                    "clean_key": key,
                }

        # Fallback for any unmapped country
        first_word = cleaned.split()[0] if cleaned.split() else cleaned
        return {
            "country": f"{first_word}{server_label}",
            "ar": f"{first_word}{server_label_ar}",
            "iso": "UN",
            "bot": bot_username,
            "raw_button": btn_text,
            "clean_key": first_word.lower(),
        }

    def _is_navigation_button(self, text: str) -> bool:
        lowered = text.lower()
        return any(k in lowered for k in NAV_KEYWORDS)

    async def start_periodic_scanner(self):
        await asyncio.sleep(5)
        while True:
            try:
                await self.scan_all_bots()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in periodic scanner: {e}")
            await asyncio.sleep(150)

    async def scan_all_bots(self):
        print("Periodic scan: scanning available countries across bots...")
        for bot in BOT_USERNAMES:
            state = self.bots[bot]
            if state.locked:
                continue

            try:
                await asyncio.wait_for(self._op_locks[bot].acquire(), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                continue

            try:
                countries = await self._scan_single_bot(bot)
                if countries:
                    self._discovered_countries[bot] = countries
                    print(f"Periodic scan: {bot} has {len(countries)} countries available.")
            except Exception as e:
                print(f"Periodic scan error on {bot}: {e}")
            finally:
                try:
                    await self._safe_reset_bot(bot)
                except Exception:
                    pass
                self._op_locks[bot].release()

            await asyncio.sleep(2.0)

    async def _scan_single_bot(self, bot_username: str) -> List[dict]:
        msg = await self._navigate_to_country_menu(bot_username)
        if not msg or not msg.buttons:
            return []

        discovered = []
        seen_keys = set()
        for row in msg.buttons:
            for btn in row:
                text = (btn.text or "").strip()
                if not text or self._is_navigation_button(text):
                    continue
                parsed = self.parse_country_button(text, bot_username)
                if parsed:
                    unique_id = (parsed["country"], parsed["bot"])
                    if unique_id not in seen_keys:
                        seen_keys.add(unique_id)
                        discovered.append(parsed)
        return discovered

    def get_countries_catalog(self) -> List[dict]:
        self._cleanup_expired_locks(ttl_seconds=300)
        result = []
        seen = set()
        for bot in BOT_USERNAMES:
            if self.bots[bot].locked:
                continue
            for item in self._discovered_countries.get(bot, []):
                unique_key = (item["country"], item["bot"])
                if unique_key not in seen:
                    seen.add(unique_key)
                    result.append({**item, "bot_busy": False})
        return result

    def _register_otp_listeners(self):
        if self._listeners_registered:
            return
        self._listeners_registered = True

        @self.client.on(events.NewMessage())
        async def otp_handler(event):
            try:
                if getattr(event.message, "out", False):
                    return

                active_items = [
                    item
                    for state in self.bots.values()
                    for item in state.numbers
                    if item.status == "RESERVED"
                ]
                if not active_items:
                    return

                text = event.raw_text or ""
                if event.message and event.message.buttons:
                    for row in event.message.buttons:
                        for btn in row:
                            text += " " + (btn.text or "")

                otp_match = re.search(r"\b(\d{3}[-\s]?\d{3})\b", text)
                if not otp_match:
                    otp_match = re.search(r"(?i)(?:code|كود|رمز|otp)[^\d]*(\d{4,8})\b", text)
                if not otp_match:
                    return

                clean_otp = re.sub(r"\D", "", otp_match.group(1))
                cleaned_digits_pool = re.sub(r"\D", "", text)

                sender_chat = await event.get_chat()
                chat_username = (getattr(sender_chat, "username", "") or "").lower()

                for item in active_items:
                    last4 = re.sub(r"\D", "", item.phone)[-4:]
                    matched = False
                    if last4 in cleaned_digits_pool:
                        matched = True
                    elif chat_username and chat_username == item.bot_username.lower():
                        if not self._is_noise_message(event.message):
                            matched = True

                    if matched:
                        item.otp_code = clean_otp
                        item.status = "COMPLETED"
                        self.completed_otps[item.phone] = {
                            "phone": item.phone,
                            "status": "COMPLETED",
                            "otp": clean_otp,
                            "bot": item.bot_username,
                            "completed_at": time.time(),
                        }
                        # Immediately release bot lock so its countries reappear in the app
                        bot_state = self.bots.get(item.bot_username)
                        if bot_state:
                            bot_state.locked = False
                            bot_state.locked_at = 0.0
                            bot_state.active_country = None
                            print(f"OTP received for {item.phone}! Bot {item.bot_username} unlocked immediately.")
                            asyncio.create_task(self._safe_reset_bot(item.bot_username))
                        return
            except Exception:
                pass

        @self.client.on(events.MessageEdited())
        async def otp_edited_handler(event):
            await otp_handler(event)

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
                if any(k in txt for k in ["رجوع", "back", "⬅", "🔙"]):
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
            if is_inline_click and isinstance(ev_msg.reply_markup, ReplyKeyboardMarkup):
                return
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
        cleaned_lines = []
        for line in text.splitlines():
            if any(b in line.lower() for b in BUSY_KEYWORDS):
                continue
            cleaned_lines.append(line)
        cleaned_text = "\n".join(cleaned_lines)

        raw_matches = re.findall(r"\+?\b\d[\d\s\-]{7,15}\d\b", cleaned_text)
        phones = []
        for m in raw_matches:
            digits = re.sub(r"\D", "", m)
            if 8 <= len(digits) <= 15:
                if re.search(r"202[4-9]\d{4}", digits):
                    continue
                phones.append("+" + digits)
        return list(dict.fromkeys(phones))

    def _extract_phones_from_msg(self, msg: Optional[Message]) -> List[str]:
        if not msg:
            return []
        valid_phones = []
        if msg.buttons:
            for row in msg.buttons:
                for btn in row:
                    text = (btn.text or "").strip()
                    if not text:
                        continue
                    if any(busy in text.lower() for busy in BUSY_KEYWORDS):
                        continue
                    btn_phones = self._extract_phones(text)
                    valid_phones.extend(btn_phones)

        text_phones = self._extract_phones(msg.raw_text or "")
        valid_phones.extend(text_phones)
        return list(dict.fromkeys(valid_phones))

    async def is_registered_on_whatsapp(self, phone: str) -> bool:
        if not WA_CHECKER_URL:
            return False
        try:
            await asyncio.sleep(1.5)
            resp = await self.http.get(WA_CHECKER_URL, params={"phone": phone.lstrip("+")})
            data = resp.json()
            return bool(data.get("registered", False))
        except Exception:
            return False

    async def _filter_fresh_numbers(
        self, phones: List[str], country: str, bot_username: str
    ) -> List[NumberItem]:
        if not WA_CHECKER_URL:
            return [NumberItem(phone=p, country=country, bot_username=bot_username) for p in phones]
        fresh = []
        for p in phones:
            if not await self.is_registered_on_whatsapp(p):
                fresh.append(NumberItem(phone=p, country=country, bot_username=bot_username))
        return fresh

    async def _navigate_to_country_menu(self, bot_username: str) -> Optional[Message]:
        if bot_username == "B_M_Numbers_Files_bot":
            m1 = await self._send_and_wait(bot_username, "/getnumber", timeout=8)
            if not m1:
                return None
            return await self._click_and_wait(bot_username, m1, text_contains="whats", timeout=8)

        elif bot_username == "smslybot":
            m1 = await self._send_and_wait(bot_username, "Get Number", timeout=8)
            if not m1:
                return None
            return await self._click_and_wait(bot_username, m1, text_contains="WhatsApp", timeout=8)

        elif bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Number", timeout=8)
            if not m2:
                return None
            return await self._click_and_wait(bot_username, m2, text_contains="WHATSAPP", timeout=8)

        elif bot_username == "NumberNest_2_Bot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            if self._find_button_rc(m1, ["Get Number"]):
                m1 = await self._click_and_wait(bot_username, m1, text_contains="Get Number", timeout=8)
            wa_btn = self._find_button_rc(m1, ["WhatsApp", "whatsapp", "واتس"])
            if wa_btn:
                m2 = await self._click_and_wait(bot_username, m1, rc=wa_btn, timeout=8)
                if m2 and m2.buttons:
                    return m2
            return m1

        elif bot_username == "JXOTPBot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Numbers", timeout=8)
            if not m2:
                m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Number", timeout=8)
            if not m2:
                return None
            return await self._click_and_wait(bot_username, m2, text_contains="whats", timeout=8)

        elif bot_username == "seven1tel_Number_Bot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            m2 = await self._click_and_wait(bot_username, m1, text_contains="get number", timeout=8)
            if not m2:
                m2 = await self._click_and_wait(bot_username, m1, text_contains="طلب رقم", timeout=8)
            if not m2:
                return None
            m3 = await self._click_and_wait(bot_username, m2, text_contains="WhatsApp", timeout=8)
            if not m3:
                m3 = await self._click_and_wait(bot_username, m2, text_contains="واتس", timeout=8)
            return m3

        return None

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
                timeout=25.0,
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
            entity = await self._get_entity_cached(bot_username)

            # Fast path for change number / refresh
            if force_refresh and state.last_message_id and state.active_country == target_country:
                try:
                    last_msg = await self.client.get_messages(entity, ids=state.last_message_id)
                    if last_msg and last_msg.buttons:
                        change_rc = self._find_button_rc(
                            last_msg, ["change number", "تغيير الرقم", "تغيير", "رقم جديد", "new number", "🔁"]
                        )
                        if change_rc:
                            msg = await self._click_and_wait(bot_username, last_msg, rc=change_rc, timeout=8)
                            if msg and self._extract_phones_from_msg(msg):
                                trace.append(self._serialize_msg("Fast Change Number", msg))
                except Exception:
                    msg = None

            if not msg:
                # Step 1: Navigate to country menu
                country_menu = await self._navigate_to_country_menu(bot_username)
                trace.append(self._serialize_msg("Country Menu", country_menu))
                if not country_menu or not country_menu.buttons:
                    err = "تعذر فتح قائمة الدول في هذا البوت"
                    self.last_errors[bot_username] = err
                    return [], err

                # Step 2: Find the matching country button
                clean_target = (
                    target_country.lower()
                    .replace("(server 1)", "")
                    .replace("(server 2)", "")
                    .replace("(server 3)", "")
                    .replace("(server jx)", "")
                    .replace("(server top)", "")
                    .strip()
                )

                country_rc = self._find_button_rc(country_menu, [clean_target])
                if not country_rc:
                    err = f"الدولة {target_country} غير متوفرة حالياً في البوت"
                    self.last_errors[bot_username] = err
                    trace.append({"step": "Select Country", "error": err})
                    return [], err

                # Step 3: Click country button
                msg = await self._click_and_wait(bot_username, country_menu, rc=country_rc, timeout=10)
                trace.append(self._serialize_msg(f"Clicked {target_country}", msg))

                # Step 4: Handle branch submenus (e.g. NumberNest branches)
                if msg and not self._extract_phones_from_msg(msg) and msg.buttons:
                    branch_rc = self._find_first_non_back_rc(msg)
                    if branch_rc:
                        msg = await self._click_and_wait(bot_username, msg, rc=branch_rc, timeout=8)
                        trace.append(self._serialize_msg("Branch Click", msg))

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
            err = "الدولة غير متوفرة حالياً أو لم يستجب البوت"
            self.last_errors[bot_username] = err
            return [], err

        fresh_items: List[NumberItem] = []
        for _ in range(max_retries):
            phones = self._extract_phones_from_msg(msg)
            fresh_items = await self._filter_fresh_numbers(phones, target_country, bot_username)
            if fresh_items:
                break
            change_rc = self._find_button_rc(
                msg, ["change number", "تغيير الرقم", "تغيير", "رقم جديد", "new number", "🔁"]
            )
            if not change_rc:
                break
            msg = await self._click_and_wait(bot_username, msg, rc=change_rc, timeout=8)
            if not msg:
                break

        state.active_country = target_country
        state.numbers = fresh_items
        state.last_message_id = msg.id if msg else None
        if not fresh_items:
            return [], "لم تتوفر أرقام جديدة حالياً لهذه الدولة"
        return fresh_items, None

    def reserve_number(self, phone: str, user_id: str) -> Optional[NumberItem]:
        self._cleanup_expired_locks(ttl_seconds=300)
        for state in self.bots.values():
            if state.locked:
                continue
            for item in state.numbers:
                if item.phone == phone and item.status == "AVAILABLE":
                    item.status = "RESERVED"
                    item.reserved_by = user_id
                    item.reserved_at = time.time()
                    state.locked = True
                    state.locked_at = time.time()
                    return item
        return None

    def release_bot(self, bot_username: str):
        state = self.bots.get(bot_username)
        if state:
            state.locked = False
            state.locked_at = 0.0
            state.active_country = None
            state.numbers = []

    def _cleanup_expired_locks(self, ttl_seconds: int = 300):
        now = time.time()
        for state in self.bots.values():
            if state.locked:
                reserved = [n for n in state.numbers if n.status == "RESERVED"]
                is_expired = False
                if not reserved:
                    is_expired = True
                elif getattr(state, "locked_at", 0.0) > 0 and (now - state.locked_at) > ttl_seconds:
                    is_expired = True
                elif (now - reserved[0].reserved_at) > ttl_seconds:
                    is_expired = True

                if is_expired:
                    state.locked = False
                    state.locked_at = 0.0
                    state.active_country = None
                    state.numbers = []

        expired_phones = [
            p for p, data in self.completed_otps.items()
            if (now - data.get("completed_at", now)) > 1800
        ]
        for p in expired_phones:
            self.completed_otps.pop(p, None)
