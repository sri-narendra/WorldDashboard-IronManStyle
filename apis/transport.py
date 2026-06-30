import httpx
from apis.base import BaseAPI, APIResult

class OpenSkyAPI(BaseAPI):
    category = "transport"
    source = "opensky"
    label = "Live Flights"
    cache_ttl = 60
    poll_interval = 3600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get("https://opensky-network.org/api/states/all?lamin=20&lomin=-130&lamax=50&lomax=-60")
                if r.status_code == 200:
                    states = r.json().get("states", [])[:30]
                    items = []
                    for s in states:
                        items.append({
                            "callsign": (s[1] or "").strip(),
                            "country": s[2],
                            "altitude": s[7],
                            "velocity": s[9],
                            "heading": s[10],
                            "lat": s[6],
                            "lon": s[5],
                            "on_ground": s[8],
                        })
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

