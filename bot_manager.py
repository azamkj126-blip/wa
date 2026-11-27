import asyncio
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import httpx
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, AuthKeyUnregisteredError
from telethon.sessions import StringSession
from telethon.tl.custom import Message
from telethon.tl.types import ReplyInlineMarkup, ReplyKeyboardMarkup

API_ID = int(os.getenv("TG_API_ID", "35177791"))
API_HASH = os.getenv("TG_API_HASH", "25b0e654c1c1202707167407e4d21d3f")
_NEW_VERIFIED_SESSION = "1BJWap1wBuyOMivhpY7uzhxYpHYfC5vxyjlhterbwgSTAnorKG3Uq3GAsMnPrjYjHRnubyBE4chQlM9DvsauMLrYe2E5LsWHDPPBW2KqGh0GIdLVF3WsbBMT2lzXfmWEC0RhdH3rLb1Mt8qSDgksZ7vFpqE08CuGs2olf-xt7WgnveHLp0ikVLl5eehBUebWyIwJwbdRkf1uyeq_zpDNsUtndPVYdWGqBUbIkqYVFl9yMz9hDnHYL8gIC8-q2RZ7QUfLTZwM-9URREUvjpSrxsR6mChJ_1dK0DyopZ_rGYZPYTwV4T0L6Y77r7NSrQI3FnYkIR5rOoXXKVaJdW9M_Pil7raNfk3U="
_raw_session = os.getenv("TG_STRING_SESSION", "").strip()
if not _raw_session or not _raw_session.startswith("1BJWap1wBuyOM"):
    _raw_session = _NEW_VERIFIED_SESSION
STRING_SESSION = (
    _raw_session + ("=" * ((4 - len(_raw_session[1:]) % 4) % 4))
    if _raw_session
    else ""
)
WA_CHECKER_URL = os.getenv("WA_CHECKER_URL", "")

BOT_USERNAMES = [
    "cloud_number_bot",
    "fb_sms_number_bot",
    "seven1tel_Number_Bot",
    "NumberNest_2_Bot",
    "smslybot",
    "SOJIB_BRO_FRESH_NUMBER_BOT",
    "B_M_Numbers_3OTP_bot",
    "B_M_Numbers_Files_bot",
    "JXOTPBot",
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
    "south africa": ("South Africa", "جنوب أفريقيا", "ZA"),
    "mexico": ("Mexico", "المكسيك", "MX"),
    "chile": ("Chile", "تشيلي", "CL"),
    "peru": ("Peru", "بيرو", "PE"),
    "azerbaijan": ("Azerbaijan", "أذربيجان", "AZ"),
    "armenia": ("Armenia", "أرمينيا", "AM"),
    "moldova": ("Moldova", "مولدوفا", "MD"),
    "romania": ("Romania", "رومانيا", "RO"),
    "czech republic": ("Czech Republic", "التشيك", "CZ"),
    "czechia": ("Czech Republic", "التشيك", "CZ"),
    "hungary": ("Hungary", "المجر", "HU"),
    "portugal": ("Portugal", "البرتغال", "PT"),
    "austria": ("Austria", "النمسا", "AT"),
    "switzerland": ("Switzerland", "سويسرا", "CH"),
    "hong kong": ("Hong Kong", "هونغ كونغ", "HK"),
    "singapore": ("Singapore", "سنغافورة", "SG"),
    "israel": ("Israel", "إسرائيل", "IL"),
    "sri lanka": ("Sri Lanka", "سريلانكا", "LK"),
    "myanmar": ("Myanmar", "ميانمار", "MM"),
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
    "بحث",
    "search",
    "page",
    "صفحة",
    "الرئيسية",
    "main",
    "قروب",
    "group",
    "otp group",
    "facebook",
    "whatsapp",
    "tiktok",
    "imo",
    "instagram",
    "telegram",
    "viber",
    "google",
    "twitter",
    "snapchat",
    "amazon",
    "authmsg",
    "blocco19",
    "boomerang",
    "openfiber",
    "shein",
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
        self._last_scan_time: float = 0.0
        self._scan_lock = asyncio.Lock()
        self.CACHE_TTL_SECONDS: float = 600.0  # 10 minutes cache TTL

    async def start(self, delay_seconds: int = 15):
        self._startup_task = asyncio.create_task(self._delayed_connect(delay_seconds))

    async def _delayed_connect(self, delay_seconds: int):
        try:
            await asyncio.sleep(delay_seconds)
            await self.client.connect()
            self.authorized = await self.client.is_user_authorized()
            if self.authorized:
                self._register_otp_listeners()
                asyncio.create_task(self._ensure_joined_channel("Cloud_Number2"))
                print("Telegram connected and authorized successfully.")
                # Run an initial scan on startup so countries are populated immediately
                asyncio.create_task(self.scan_all_bots())
            else:
                self.last_errors["startup"] = "TG_STRING_SESSION منتهية أو ملغاة، تحتاج تجديد"
                print("ERROR: TG_STRING_SESSION is invalid or revoked.")
        except Exception as e:
            self.authorized = False
            self.last_errors["startup"] = f"{type(e).__name__}: {e}"
            print(f"Telegram startup error: {e}")
        finally:
            self._ready_event.set()

    async def _ensure_joined_channel(self, channel_or_link: str):
        if not self.authorized:
            return
        try:
            from telethon import functions
            clean = channel_or_link.strip().rstrip("/")
            if "t.me/+" in clean or "joinchat/" in clean:
                invite_hash = clean.split("+")[-1].split("joinchat/")[-1].split("/")[0].split("?")[0]
                if invite_hash:
                    try:
                        await self.client(functions.messages.ImportChatInviteRequest(invite_hash))
                        print(f"Joined private OTP group: {invite_hash}")
                    except Exception:
                        pass
            else:
                username = clean.split("t.me/")[-1].split("/")[-1].split("?")[0].lstrip("@")
                if username and not username.lower().endswith("bot"):
                    try:
                        await self.client(functions.channels.JoinChannelRequest(username))
                        print(f"Joined public OTP channel: {username}")
                    except Exception:
                        pass
        except Exception as e:
            print(f"Channel join note ({channel_or_link}): {e}")

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
            aliases = COUNTRY_ALIASES.get(key, [])
            if key in lowered or ar.lower() in lowered or any(a in lowered for a in aliases):
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

    async def _safe_scan_catalog(self):
        if not self.authorized:
            return
        async with self._scan_lock:
            now = time.time()
            has_countries = any(len(c) > 0 for c in self._discovered_countries.values())
            if has_countries and (now - self._last_scan_time) < self.CACHE_TTL_SECONDS:
                return
            print("10-minute cache window expired or empty: refreshing countries dynamically from bots...")
            await self.scan_all_bots()

    async def scan_all_bots(self):
        if not self.authorized:
            return
        print("Scanning live available countries across all 6 bots...")
        for bot in BOT_USERNAMES:
            if not self.authorized:
                break
            state = self.bots[bot]
            if state.locked:
                continue

            try:
                await asyncio.wait_for(self._op_locks[bot].acquire(), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                continue

            try:
                countries = await asyncio.wait_for(self._scan_single_bot(bot), timeout=25.0)
                if countries:
                    existing = {item["country"]: item for item in self._discovered_countries.get(bot, [])}
                    for c in countries:
                        existing[c["country"]] = c
                    self._discovered_countries[bot] = list(existing.values())
                    print(f"Scan result: {bot} has {len(self._discovered_countries[bot])} live countries.")
            except AuthKeyUnregisteredError:
                self.authorized = False
                print("Scan: AuthKeyUnregisteredError, Telegram session has been revoked.")
                break
            except Exception as e:
                print(f"Scan error on {bot}: {e}")
            finally:
                try:
                    await self._safe_reset_bot(bot)
                except Exception:
                    pass
                if self._op_locks[bot].locked():
                    try:
                        self._op_locks[bot].release()
                    except Exception:
                        pass

            await asyncio.sleep(4.0)

        self._last_scan_time = time.time()
        print(f"Scan completed. Total countries discovered: {sum(len(c) for c in self._discovered_countries.values())}. Cache valid for 10 minutes.")

    async def _scan_single_bot(self, bot_username: str) -> List[dict]:
        msg = await self._navigate_to_country_menu(bot_username)
        if not msg or not msg.buttons:
            return []

        discovered = []
        seen_keys = set()
        visited_pages = 0
        current_msg = msg

        while current_msg and current_msg.buttons and visited_pages < 5:
            visited_pages += 1
            for row in current_msg.buttons:
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

            next_rc = self._find_button_rc(current_msg, ["next", ">>", "التالي", "➡️", "صفحة 2", "صفحة 3", "page 2", "page 3"])
            if not next_rc:
                break
            try:
                next_msg = await self._click_and_wait(bot_username, current_msg, rc=next_rc, timeout=6)
                if next_msg and next_msg.buttons and self._button_signature(next_msg) != self._button_signature(current_msg):
                    current_msg = next_msg
                else:
                    break
            except Exception:
                break

        return discovered

    async def get_countries_catalog(self) -> List[dict]:
        self._cleanup_expired_locks(ttl_seconds=300)
        now = time.time()
        has_countries = any(len(c) > 0 for c in self._discovered_countries.values())
        cache_expired = (now - self._last_scan_time) >= self.CACHE_TTL_SECONDS

        # When a user opens the app:
        # If cache expired (older than 10 minutes) or has no countries:
        # Scan the bots dynamically. If cache is fresh (<10 min), return same countries instantly!
        if (cache_expired or not has_countries) and self.authorized:
            if not has_countries:
                # First open with empty cache: wait for scan so real countries are returned
                await self._safe_scan_catalog()
            else:
                # Cache expired but we have previous data: refresh in background so response is instantaneous
                if not self._scan_lock.locked():
                    asyncio.create_task(self._safe_scan_catalog())

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
                    item_phone_digits = re.sub(r"\D", "", item.phone)
                    last4 = item_phone_digits[-4:] if len(item_phone_digits) >= 4 else item_phone_digits
                    last6 = item_phone_digits[-6:] if len(item_phone_digits) >= 6 else item_phone_digits

                    matched = False
                    if item_phone_digits and item_phone_digits in cleaned_digits_pool:
                        matched = True
                    elif last6 and last6 in cleaned_digits_pool:
                        matched = True
                    elif last4 and last4 in cleaned_digits_pool:
                        matched = True
                    elif chat_username and chat_username == item.bot_username.lower():
                        if not self._is_noise_message(event.message):
                            matched = True

                    if matched:
                        # Extract OTP without confusing it with the phone number
                        text_without_phone = text
                        if item_phone_digits:
                            text_without_phone = text_without_phone.replace(item_phone_digits, "")

                        otp_extracted = (
                            re.search(r"(?i)(?:code|كود|رمز|otp|whatsapp|واتساب)[^\d]*(\d{3}[-\s]?\d{3})\b", text_without_phone)
                            or re.search(r"(?i)(?:code|كود|رمز|otp|whatsapp|واتساب)[^\d]*(\d{4,8})\b", text_without_phone)
                            or re.search(r"\b(\d{3}[-\s]\d{3})\b", text_without_phone)
                            or re.search(r"\b(\d{6})\b", text_without_phone)
                            or otp_match
                        )
                        if not otp_extracted:
                            continue

                        clean_otp = re.sub(r"\D", "", otp_extracted.group(1))
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
                            print(f"OTP received for {item.phone}: {clean_otp}! Bot {item.bot_username} unlocked immediately.")
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
                    b_type = type(getattr(btn, "button", btn)).__name__
                    b_data = getattr(getattr(btn, "button", None), "data", None)
                    data_str = f" data={b_data.decode('utf-8', errors='ignore')}" if b_data else ""
                    btns.append(f"[{r},{c}] ({b_type}{data_str}) {btn.text}")
        return {
            "step": step,
            "text": (msg.raw_text or "")[:200],
            "buttons": btns[:30],
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
        if not self.authorized:
            return
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
                await asyncio.wait(
                    {click_task, fut},
                    timeout=remaining,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if fut.done():
                    break
                if click_task.done():
                    remaining2 = deadline - loop.time()
                    if remaining2 <= 0:
                        break
                    try:
                        await asyncio.wait_for(asyncio.shield(fut), timeout=remaining2)
                    except asyncio.TimeoutError:
                        pass
                    break

            res = None
            if fut.done():
                res = fut.result()
            elif click_task.done() and not click_task.cancelled():
                try:
                    c_res = click_task.result()
                    if isinstance(c_res, Message) and c_res.buttons and self._button_signature(c_res) != prev_sig:
                        res = c_res
                except Exception:
                    pass

            if not res:
                try:
                    latest = await self.client.get_messages(entity, limit=1)
                    if latest and latest[0].buttons and self._button_signature(latest[0]) != prev_sig:
                        res = latest[0]
                except Exception:
                    pass

            if not res:
                return None
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
        if bot_username == "cloud_number_bot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            self.last_trace[bot_username].append(self._serialize_msg("Start Response", m1))

            # Step 1: Click "الحصول على رقم" / "Get Number" to reveal platforms
            gn_rc = self._find_button_rc(m1, ["الحصول على رقم", "طلب رقم", "get number", "رقم جديد"])
            if gn_rc:
                m2 = await self._click_and_wait(bot_username, m1, rc=gn_rc, timeout=8)
            else:
                m2 = await self._send_and_wait(bot_username, "الحصول على رقم", timeout=8)

            if not m2:
                # If bot already showed platforms in m1
                m2 = m1
            self.last_trace[bot_username].append(self._serialize_msg("Platforms Menu", m2))

            # Step 2: Now find and click WhatsApp on the platforms menu
            wa_rc = self._find_button_rc(m2, ["whatsapp", "whats", "واتس", "واتساب"])
            if not wa_rc and m2.buttons:
                for r_idx, row in enumerate(m2.buttons):
                    for c_idx, btn in enumerate(row):
                        b_txt = (btn.text or "").lower()
                        if "what" in b_txt or "واتس" in b_txt:
                            wa_rc = (r_idx, c_idx)
                            break
                    if wa_rc:
                        break
            if not wa_rc:
                wa_rc = (1, 0) # Fallback to [1,0] which is WhatsApp (1625)

            m3 = await self._click_and_wait(bot_username, m2, rc=wa_rc, timeout=12)
            if not m3:
                try:
                    m3 = await self._click_and_wait(bot_username, m2, text_contains="what", timeout=12)
                except Exception:
                    pass
            self.last_trace[bot_username].append(self._serialize_msg(f"Clicked WhatsApp {wa_rc}", m3))
            asyncio.create_task(self._ensure_joined_channel("Cloud_Number2"))
            return m3

        elif bot_username == "fb_sms_number_bot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            gn_rc = self._find_button_rc(m1, ["get number", "get", "طلب رقم"])
            if gn_rc:
                m2 = await self._click_and_wait(bot_username, m1, rc=gn_rc, timeout=8)
            else:
                m2 = await self._send_and_wait(bot_username, "Get Number", timeout=8)
            if not m2:
                return None
            wa_rc = self._find_button_rc(m2, ["whatsapp", "whats", "واتس", "واتساب"])
            if not wa_rc and m2.buttons:
                last_row = m2.buttons[-1]
                wa_rc = (len(m2.buttons) - 1, len(last_row) - 1)
            if not wa_rc:
                return None
            m3 = await self._click_and_wait(bot_username, m2, rc=wa_rc, timeout=8)
            if not m3:
                try:
                    m3 = await self._click_and_wait(bot_username, m2, text_contains="what", timeout=8)
                except Exception:
                    pass
            return m3

        elif bot_username in ("B_M_Numbers_3OTP_bot", "B_M_Numbers_Files_bot"):
            m1 = await self._send_and_wait(bot_username, "/getnumber", timeout=8)
            if not m1 or not m1.buttons:
                m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            return await self._click_and_wait(bot_username, m1, text_contains="whats", timeout=8)

        elif bot_username == "smslybot":
            m1 = await self._send_and_wait(bot_username, "Get Number", timeout=8)
            if not m1 or not m1.buttons:
                m_start = await self._send_and_wait(bot_username, "/start", timeout=8)
                gn_btn = self._find_button_rc(m_start, ["get number", "طلب رقم"])
                if gn_btn:
                    m1 = await self._click_and_wait(bot_username, m_start, rc=gn_btn, timeout=8)
                else:
                    m1 = await self._send_and_wait(bot_username, "Get Number", timeout=8)
            if not m1:
                return None
            return await self._click_and_wait(bot_username, m1, text_contains="WhatsApp", timeout=8)

        elif bot_username == "SOJIB_BRO_FRESH_NUMBER_BOT":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            wa_rc = self._find_button_rc(m1, ["whatsapp", "whats", "واتس", "واتساب"])
            if wa_rc:
                return await self._click_and_wait(bot_username, m1, rc=wa_rc, timeout=8)
            m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Number", timeout=8)
            if m2:
                return await self._click_and_wait(bot_username, m2, text_contains="WHATSAPP", timeout=8)
            return None

        elif bot_username == "NumberNest_2_Bot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            wa_btn = self._find_button_rc(m1, ["WhatsApp", "whatsapp", "واتس"])
            if wa_btn:
                m2 = await self._click_and_wait(bot_username, m1, rc=wa_btn, timeout=8)
                if m2 and m2.buttons:
                    return m2
            if self._find_button_rc(m1, ["Get Number"]):
                m1_gn = await self._click_and_wait(bot_username, m1, text_contains="Get Number", timeout=8)
                if m1_gn:
                    wa_btn = self._find_button_rc(m1_gn, ["WhatsApp", "whatsapp", "واتس"])
                    if wa_btn:
                        return await self._click_and_wait(bot_username, m1_gn, rc=wa_btn, timeout=8)
            return None

        elif bot_username == "JXOTPBot":
            m1 = await self._send_and_wait(bot_username, "/start", timeout=8)
            if not m1:
                return None
            wa_btn = self._find_button_rc(m1, ["whatsapp", "whats", "واتس"])
            if wa_btn:
                return await self._click_and_wait(bot_username, m1, rc=wa_btn, timeout=8)
            m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Numbers", timeout=8)
            if not m2:
                m2 = await self._click_and_wait(bot_username, m1, text_contains="Get Number", timeout=8)
            if m2:
                return await self._click_and_wait(bot_username, m2, text_contains="whats", timeout=8)
            return None

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
            if self._op_locks[bot_username].locked():
                try:
                    self._op_locks[bot_username].release()
                except Exception:
                    pass

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
        except AuthKeyUnregisteredError:
            self.authorized = False
            err = "انتهت جلسة تيليجرام أو تم تسجيل الخروج، يرجى تجديد TG_STRING_SESSION في Render"
            self.last_errors[bot_username] = err
            return [], err
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            self.last_errors[bot_username] = err
            if "AuthKey" in str(e) or "unregistered" in str(e).lower():
                self.authorized = False
                return [], "انتهت جلسة تيليجرام أو تم تسجيل الخروج، يرجى تجديد TG_STRING_SESSION في Render"
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

        # Auto-join OTP group/channel if link is present in buttons
        if msg and msg.buttons:
            for row in msg.buttons:
                for btn in row:
                    btn_url = getattr(btn, "url", None)
                    if btn_url and ("t.me/" in btn_url or "telegram.me/" in btn_url):
                        asyncio.create_task(self._ensure_joined_channel(btn_url))
        if bot_username == "cloud_number_bot":
            asyncio.create_task(self._ensure_joined_channel("Cloud_Number2"))
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

    async def clean_groups(self) -> Dict[str, Any]:
        if not self.client or not self.client.is_connected():
            await self.start()

        from telethon import functions
        dialogs = await self.client.get_dialogs(limit=None)
        number_keywords = [
            "رقم", "ارقام", "أرقام", "number", "numbers", "sms", "otp",
            "واتساب", "whatsapp", "sim", "تفعيل", "كود", "حسابات", "بوت",
            "bot", "virtual", "fake", "free", "traffic", "سيرفر"
        ]

        left_count = 0
        kept_count = 0
        errors = 0

        for d in dialogs:
            if d.is_channel or d.is_group:
                title = d.title or ""
                title_lower = title.lower()
                is_number_related = any(kw in title_lower for kw in number_keywords)

                if is_number_related:
                    kept_count += 1
                else:
                    try:
                        if d.is_channel:
                            await self.client(functions.channels.LeaveChannelRequest(d.input_entity))
                        else:
                            await self.client.delete_dialog(d.entity)
                        left_count += 1
                        await asyncio.sleep(0.3)
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except Exception:
                        errors += 1

        try:
            await self.client.send_message(
                "me",
                f"تم اكتمال تنظيف الحساب بنجاح!\n- تم مغادرة: {left_count} قروب وقناة سبام\n- تم الإبقاء على: {kept_count} قناة وقروب متخصصة في الأرقام والبوتات"
            )
        except Exception:
            pass

        return {
            "status": "success",
            "left_count": left_count,
            "kept_count": kept_count,
            "errors": errors,
            "total_scanned": len(dialogs)
        }
