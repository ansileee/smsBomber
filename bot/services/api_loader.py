from __future__ import annotations

from typing import List, Dict, Any

from apis import API_CONFIGS as _RAW # type: ignore

APIS_PER_PAGE = 6


class ApiLoader:
    def __init__(self) -> None:
        self._apis: List[Dict[str, Any]] = []
        self.reload()

    def reload(self) -> None:
        seen = set()
        self._apis = []
        for api in _RAW:
            key = (api["name"], api["url"])
            if key not in seen:
                seen.add(key)
                self._apis.append(api)

    @property
    def all(self) -> List[Dict[str, Any]]:
        return self._apis

    @property
    def totalPages(self) -> int:
        return max(1, -(-len(self._apis) // APIS_PER_PAGE))

    def page(self, pageNum: int) -> List[Dict[str, Any]]:
        start = pageNum * APIS_PER_PAGE
        return self._apis[start:start + APIS_PER_PAGE]

    def formatPage(self, pageNum: int) -> str:
        items = self.page(pageNum)
        if not items:
            return "No APIs loaded."

        lines = [
            f"API List  (page {pageNum + 1} of {self.totalPages})",
            f"Total: {len(self._apis)}",
            "",
        ]
        for i, api in enumerate(items, start=pageNum * APIS_PER_PAGE + 1):
            url = api["url"]
            displayUrl = url if len(url) <= 50 else url[:47] + "..."
            lines.append(f"{i}. {api['name']}")
            lines.append(f"   {api['method']}  {displayUrl}")
            lines.append("")

        return "\n".join(lines).rstrip()


apiLoader = ApiLoader()