import asyncio
import httpx
from apis.base import BaseAPI, APIResult

class RestCountriesAPI(BaseAPI):
    category = "government"
    source = "restcountries"
    label = "World Countries"
    cache_ttl = 86400

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
                pos_r = await c.get("https://countriesnow.space/api/v0.1/countries/positions")
                cap_r = await c.get("https://countriesnow.space/api/v0.1/countries/capital")
                info_r = await c.get("https://countriesnow.space/api/v0.1/countries/info?returns=flag,population,capital,currency,language,region")
                if pos_r.status_code != 200 or cap_r.status_code != 200:
                    return APIResult(category=self.category, source=self.source, label=self.label, error=f"CountriesNow fetch failed (pos={pos_r.status_code}, cap={cap_r.status_code})")
                pos_map = {d["name"]: d for d in pos_r.json().get("data", [])}
                cap_map = {d["name"]: d for d in cap_r.json().get("data", [])}
                info_data = info_r.json().get("data", []) if info_r.status_code == 200 else []
                info_map = {d["name"]: d for d in info_data}
                names = sorted(set(k for k in pos_map if k != "Undefined"))[:80]
                countries = []
                for name in names:
                    p = pos_map.get(name, {})
                    c2 = cap_map.get(name, {})
                    i = info_map.get(name, {})
                    countries.append({
                        "name": name,
                        "capital": c2.get("capital", ""),
                        "flag": i.get("flag", ""),
                        "currency": i.get("currency", ""),
                        "region": i.get("region", ""),
                        "iso2": p.get("iso2", ""),
                        "latitude": p.get("lat"),
                        "longitude": p.get("long"),
                    })
                return APIResult(category=self.category, source=self.source, label=self.label, data=countries)
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class USDebtAPI(BaseAPI):
    category = "government"
    source = "usdebt"
    label = "US National Debt"
    cache_ttl = 3600
    poll_interval = 3600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?sort=-record_date&limit=1")
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    if data:
                        d = data[0]
                        return APIResult(category=self.category, source=self.source, label=self.label, data={
                            "total_debt": float(d.get("tot_pub_debt_out_amt", 0)),
                            "record_date": d.get("record_date", ""),
                        })
                    return APIResult(category=self.category, source=self.source, label=self.label, error="No debt data")
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class NagerHolidaysAPI(BaseAPI):
    category = "government"
    source = "nager_holidays"
    label = "Public Holidays"
    cache_ttl = 86400

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                from datetime import datetime
                year = datetime.now().year
                countries_lim = ["US", "GB", "JP", "DE", "FR", "IN", "CN", "BR", "AU", "RU"]
                async def fetch_country(code):
                    r = await c.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{code}")
                    if r.status_code != 200:
                        return []
                    return [{"country": code, "name": h["localName"], "date": h["date"], "global": h.get("global")} for h in r.json()[:3]]
                raw = await asyncio.gather(*(fetch_country(code) for code in countries_lim))
                items = [h for sub in raw for h in sub]
                return APIResult(category=self.category, source=self.source, label=self.label, data=items)
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
