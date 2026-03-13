from __future__ import annotations

from typing import List

from bot.services.database import db


class ProxyManager:
    """
    Serves the merged proxy list from all stored proxy files.
    Users can only toggle proxy on/off — they never touch this list.
    Only the admin can add or delete proxy files.
    """

    def getAllProxies(self) -> List[str]:
        return db.getAllProxies()

    def hasProxies(self) -> bool:
        return len(db.getAllProxies()) > 0


proxyManager = ProxyManager()
