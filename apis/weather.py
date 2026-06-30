import asyncio
import httpx
from apis.base import BaseAPI, APIResult

CITIES = [
    ("New York", 40.71, -74.01),
    ("London", 51.51, -0.13),
    ("Tokyo", 35.68, 139.69),
    ("Sydney", -33.87, 151.21),
    ("Cairo", 30.04, 31.24),
    ("Mumbai", 19.08, 72.88),
    ("Sao Paulo", -23.55, -46.63),
    ("Berlin", 52.52, 13.41),
    ("Shanghai", 31.23, 121.47),
    ("Dubai", 25.20, 55.27),
    ("Moscow", 55.76, 37.62),
    ("Paris", 48.86, 2.35),
    ("Cape Town", -33.92, 18.42),
    ("Singapore", 1.35, 103.82),
    ("Mexico City", 19.43, -99.13),
]
AIR_CITIES = [
    ("New York", 40.71, -74.01),
    ("London", 51.51, -0.13),
    ("Tokyo", 35.68, 139.69),
    ("Beijing", 39.91, 116.40),
    ("Delhi", 28.65, 77.23),
]

class OpenMeteoAPI(BaseAPI):
    category = "weather"
    source = "openmeteo"
    label = "Global Weather"
    cache_ttl = 300
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                async def fetch_city(name, lat, lon):
                    r = await c.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,pressure_msl&timezone=auto")
                    if r.status_code != 200:
                        return None
                    cur = r.json().get("current", {})
                    return {"city": name, "lat": lat, "lon": lon, "temp": cur.get("temperature_2m"), "feels_like": cur.get("apparent_temperature"), "humidity": cur.get("relative_humidity_2m"), "precipitation": cur.get("precipitation"), "weather_code": cur.get("weather_code"), "wind_speed": cur.get("wind_speed_10m"), "pressure": cur.get("pressure_msl")}

                raw = await asyncio.gather(*(fetch_city(n, la, lo) for n, la, lo in CITIES))
                return APIResult(category=self.category, source=self.source, label=self.label, data=[it for it in raw if it is not None])
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class OpenMeteoAirQualityAPI(BaseAPI):
    category = "weather"
    source = "airquality"
    label = "Air Quality"
    cache_ttl = 600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                async def fetch_city(name, lat, lon):
                    r = await c.get(f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=european_aqi,us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone")
                    if r.status_code != 200:
                        return None
                    cur = r.json().get("current", {})
                    return {"city": name, "european_aqi": cur.get("european_aqi"), "us_aqi": cur.get("us_aqi"), "pm2_5": cur.get("pm2_5"), "pm10": cur.get("pm10"), "no2": cur.get("nitrogen_dioxide"), "ozone": cur.get("ozone")}

                raw = await asyncio.gather(*(fetch_city(n, la, lo) for n, la, lo in AIR_CITIES))
                return APIResult(category=self.category, source=self.source, label=self.label, data=[it for it in raw if it is not None])
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class USGSEarthquakeAPI(BaseAPI):
    category = "weather"
    source = "usgs_earthquake"
    label = "Earthquakes"
    cache_ttl = 120
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson")
                if r.status_code == 200:
                    features = r.json().get("features", [])[:20]
                    items = []
                    for f in features:
                        props = f["properties"]
                        coords = f["geometry"]["coordinates"]
                        items.append({
                            "magnitude": props.get("mag"),
                            "place": props.get("place"),
                            "time": props.get("time"),
                            "lat": coords[1],
                            "lon": coords[0],
                            "depth": coords[2],
                            "url": props.get("url"),
                            "tsunami": props.get("tsunami"),
                        })
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
