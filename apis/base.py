import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

CACHE_DIR = Path(__file__).parent.parent / "cache"

@dataclass
class APIResult:
    category: str
    source: str
    label: str
    data: Any = field(default_factory=list)
    error: Optional[str] = None
    updated_at: float = 0.0

    def dict(self):
        return asdict(self)

class BaseAPI:
    category: str = ""
    source: str = ""
    label: str = ""
    cache_ttl: int = 60

    def __init__(self):
        CACHE_DIR.mkdir(exist_ok=True)
        self._cache_path = CACHE_DIR / f"{self.category}_{self.source}.json"

    def _load_cache(self) -> Optional[APIResult]:
        if self._cache_path.exists():
            try:
                data = json.loads(self._cache_path.read_text())
                if time.time() - data.get("updated_at", 0) < self.cache_ttl:
                    return APIResult(**data)
            except Exception:
                pass
        return None

    def _save_cache(self, result: APIResult):
        try:
            self._cache_path.write_text(json.dumps(result.dict()))
        except Exception:
            pass

    async def fetch(self) -> APIResult:
        cached = self._load_cache()
        if cached:
            return cached
        result = await self._fetch()
        result.updated_at = time.time()
        self._save_cache(result)
        return result

    async def _fetch(self) -> APIResult:
        raise NotImplementedError
