import asyncio
import httpx
from apis.base import BaseAPI, APIResult

class GDACSAPI(BaseAPI):
    category = "environment"
    source = "gdacs"
    label = "Global Disasters"
    cache_ttl = 300

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://www.gdacs.org/xml/rss.xml")
                if r.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(r.text)
                    items = []
                    for entry in root.iter("item"):
                        title = entry.findtext("title", "")
                        desc = entry.findtext("description", "")[:200]
                        link = entry.findtext("link", "")
                        pub_date = entry.findtext("pubDate", "")
                        items.append({"title": title, "description": desc, "link": link, "date": pub_date})
                        if len(items) >= 10:
                            break
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class OpenMeteoMarineAPI(BaseAPI):
    category = "environment"
    source = "marine_weather"
    label = "Marine Weather"
    cache_ttl = 600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                oceans = [
                    ("North Atlantic", 40, -40),
                    ("South Pacific", -30, -130),
                    ("Indian Ocean", -20, 80),
                    ("Arctic", 78, 10),
                    ("Southern Ocean", -60, 0),
                ]
                async def fetch_ocean(name, lat, lon):
                    r = await c.get(f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,wind_wave_height&timezone=auto")
                    if r.status_code != 200:
                        return None
                    cur = r.json().get("current", {})
                    return {"region": name, "wave_height": cur.get("wave_height"), "wave_direction": cur.get("wave_direction"), "wave_period": cur.get("wave_period"), "swell_height": cur.get("swell_wave_height"), "swell_direction": cur.get("swell_wave_direction")}

                raw = await asyncio.gather(*(fetch_ocean(n, la, lo) for n, la, lo in oceans))
                return APIResult(category=self.category, source=self.source, label=self.label, data=[it for it in raw if it is not None])
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class AuroraForecastAPI(BaseAPI):
    category = "environment"
    source = "aurora"
    label = "Aurora Forecast"
    cache_ttl = 300
    poll_interval = 300

    @staticmethod
    def _parse_json_bom(content: bytes):
        import json
        return json.loads(content.decode("utf-8-sig"))

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                kp = await c.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json")
                ov = await c.get("https://services.swpc.noaa.gov/json/ovation_aurora_latest.json")
                data = {}
                if kp.status_code == 200:
                    rows = self._parse_json_bom(kp.content)
                    if rows:
                        latest = rows[-1]
                        data["kp_index"] = float(latest[1]) if len(latest) > 1 else None
                        data["kp_status"] = latest[2] if len(latest) > 2 else ""
                        data["kp_time"] = latest[0] if len(latest) > 0 else ""
                if ov.status_code == 200:
                    ov_data = self._parse_json_bom(ov.content)
                    data["aurora_now"] = ov_data.get("observation", {})
                return APIResult(category=self.category, source=self.source, label=self.label, data=data)
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class RainViewerAPI(BaseAPI):
    category = "environment"
    source = "rainviewer"
    label = "Global Radar"
    cache_ttl = 300

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://api.rainviewer.com/public/weather-maps.json")
                if r.status_code == 200:
                    data = r.json()
                    return APIResult(category=self.category, source=self.source, label=self.label, data={
                        "version": data.get("version"),
                        "radar_past_count": len(data.get("radar", {}).get("past", [])),
                        "radar_nowcast_count": len(data.get("radar", {}).get("nowcast", [])),
                        "satellite_infrared": data.get("satellite", {}).get("infrared", [])[:1],
                    })
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
