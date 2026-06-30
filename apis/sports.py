import httpx
from datetime import datetime
from apis.base import BaseAPI, APIResult

class OpenF1API(BaseAPI):
    category = "sports"
    source = "openf1"
    label = "F1 Live"
    cache_ttl = 30
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            year = datetime.now().year
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"https://api.openf1.org/v1/meetings?year={year}")
                if r.status_code == 200:
                    return APIResult(category=self.category, source=self.source, label=self.label, data=r.json())
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class NBALiveAPI(BaseAPI):
    category = "sports"
    source = "nba_live"
    label = "NBA Scores"
    cache_ttl = 30
    poll_interval = 30

    async def _fetch(self) -> APIResult:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://www.nba.com/"}
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json", headers=headers)
                if r.status_code == 200:
                    games = []
                    for g in r.json().get("scoreboard", {}).get("games", []):
                        games.append({
                            "home": g["homeTeam"]["teamName"],
                            "visitor": g["awayTeam"]["teamName"],
                            "home_score": g["homeTeam"]["score"],
                            "visitor_score": g["awayTeam"]["score"],
                            "period": g["period"],
                            "status": g["gameStatusText"],
                            "date": g.get("gameDateTimeUTC", ""),
                        })
                    return APIResult(category=self.category, source=self.source, label=self.label, data=games)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
