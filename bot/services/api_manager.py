from __future__ import annotations

import json
from typing import List, Dict, Any, Tuple, Optional

from apis import API_CONFIGS as _BASE_CONFIGS # type: ignore
from bot.services.database import db


class ApiManager:
    """
    Single source of truth for all API configs.
    Merges the static apis.py list with admin-added APIs from the database.
    No restart needed when APIs are added or deleted via the admin panel.
    """

    def getMergedConfigs(self) -> List[Dict[str, Any]]:
        configs = list(_BASE_CONFIGS)
        for row in db.getAllCustomApis():
            try:
                cfg = json.loads(row["configJson"])
                configs.append(cfg)
            except Exception:
                pass
        return configs

    def validateApiJson(self, raw: str) -> Tuple[bool, Optional[Dict], str]:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            lines = [l for l in lines if not l.startswith("```")]
            raw = "\n".join(lines).strip()

        try:
            cfg = json.loads(raw)
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {e}"

        if not isinstance(cfg, dict):
            return False, None, "JSON must be an object, not a list or value."

        for field in ["name", "method", "url"]:
            if field not in cfg:
                return False, None, f"Missing required field: \"{field}\""

        if cfg["method"].upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            return False, None, f"Invalid method: {cfg['method']}"

        if not cfg["url"].startswith("http"):
            return False, None, "URL must start with http:// or https://"

        cfg["method"] = cfg["method"].upper()
        return True, cfg, ""

    def formatApiPreview(self, cfg: dict) -> str:
        lines = [
            "API Preview\n",
            f"Name   : {cfg['name']}",
            f"Method : {cfg['method']}",
            f"URL    : {cfg['url']}",
        ]
        if cfg.get("headers"):
            lines.append(f"Headers: {len(cfg['headers'])} defined")
        if cfg.get("json"):
            lines.append(f"Body   : JSON ({len(cfg['json'])} fields)")
        elif cfg.get("data"):
            lines.append(f"Body   : Form data ({len(cfg['data'])} fields)")
        if cfg.get("params"):
            lines.append(f"Params : {len(cfg['params'])} defined")
        return "\n".join(lines)


apiManager = ApiManager()