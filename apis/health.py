import httpx
from apis.base import BaseAPI, APIResult

class OpenDiseaseAPI(BaseAPI):
    category = "health"
    source = "opendisease"
    label = "Disease Outbreaks"
    cache_ttl = 600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://disease.sh/v3/covid-19/continents")
                if r.status_code == 200:
                    items = [{"continent": d["continent"], "cases": d["cases"], "deaths": d["deaths"], "recovered": d["recovered"], "active": d["active"], "todayCases": d["todayCases"], "todayDeaths": d["todayDeaths"], "population": d["population"]} for d in r.json()]
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class GlobalHealthAPI(BaseAPI):
    category = "health"
    source = "global_health"
    label = "World Health Stats"
    cache_ttl = 3600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get("https://disease.sh/v3/covid-19/all")
                if r.status_code == 200:
                    d = r.json()
                    return APIResult(category=self.category, source=self.source, label=self.label, data={
                        "total_cases": d.get("cases"), "total_deaths": d.get("deaths"),
                        "total_recovered": d.get("recovered"), "active_cases": d.get("active"),
                        "critical": d.get("critical"), "cases_per_million": d.get("casesPerOneMillion"),
                        "deaths_per_million": d.get("deathsPerOneMillion"), "tests": d.get("tests"),
                        "affected_countries": d.get("affectedCountries"), "updated": d.get("updated"),
                    })
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
