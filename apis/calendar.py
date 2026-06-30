import httpx
from apis.base import BaseAPI, APIResult

class NagerDateAPI(BaseAPI):
    category = "calendar"
    source = "nager_next"
    label = "Upcoming Holidays"
    cache_ttl = 3600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://date.nager.at/api/v3/NextPublicHolidaysWorldwide")
                if r.status_code == 200:
                    items = [{"country": h["countryCode"], "name": h["localName"], "date": h["date"], "global": h.get("global")} for h in r.json()[:20]]
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
