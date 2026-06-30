import httpx
from apis.base import BaseAPI, APIResult

class NASAAPODAPI(BaseAPI):
    category = "science"
    source = "nasa_apod"
    label = "NASA Astronomy Picture"
    cache_ttl = 3600
    poll_interval = 7200

    def _extract_full_image(self, page_html: str, base_url: str = "https://apod.nasa.gov/apod/") -> str:
        import re
        m = re.search(r'<a\s+href="(image/\d{4}/[^"]+)"', page_html, re.IGNORECASE)
        if m:
            return base_url.rstrip("/") + "/" + m.group(1)
        m = re.search(r'<img\s+src="(image/\d{4}/[^"]+)"', page_html, re.IGNORECASE)
        if m:
            return base_url.rstrip("/") + "/" + m.group(1)
        return ""

    async def _fetch(self) -> APIResult:
        try:
            import xml.etree.ElementTree as ET
            import html as html_mod
            import re
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://apod.nasa.gov/apod.rss")
                if r.status_code != 200:
                    return APIResult(category=self.category, source=self.source, label=self.label, error=f"RSS HTTP {r.status_code}")
                root = ET.fromstring(r.text)
                item = root.findall(".//item")[0]
                desc = html_mod.unescape(item.findtext("description") or "")
                title = ""
                m = re.search(r'alt="([^"]*)"', desc)
                if m:
                    title = m.group(1).strip()
                link = (item.findtext("link") or "").strip()
                if not link:
                    return APIResult(category=self.category, source=self.source, label=self.label, error="No link in RSS item")
                page = await c.get(link, follow_redirects=True)
                img_url = self._extract_full_image(page.text) if page.status_code == 200 else ""
                return APIResult(category=self.category, source=self.source, label=self.label, data={"title": title, "url": img_url, "image": img_url, "page_url": link, "media_type": "image"})
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class OpenNotifyISSAPI(BaseAPI):
    category = "science"
    source = "iss"
    label = "ISS Location"
    cache_ttl = 30
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("http://api.open-notify.org/iss-now.json")
                people = await c.get("http://api.open-notify.org/astros.json")
                if r.status_code == 200:
                    pos = r.json()["iss_position"]
                    astros = []
                    if people.status_code == 200:
                        astros = [{"name": p["name"], "craft": p["craft"]} for p in people.json().get("people", [])]
                    return APIResult(category=self.category, source=self.source, label=self.label, data={
                        "latitude": pos["latitude"], "longitude": pos["longitude"], "astronauts": astros, "astronaut_count": len(astros)
                    })
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class LaunchLibraryAPI(BaseAPI):
    category = "science"
    source = "launchlibrary"
    label = "Upcoming Launches"
    cache_ttl = 600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=10")
                if r.status_code == 200:
                    items = []
                    for la in r.json()["results"]:
                        items.append({
                            "name": la["name"], "net": la.get("net"),
                            "provider": la.get("launch_service_provider", {}).get("name") if la.get("launch_service_provider") else None,
                            "rocket": la.get("rocket", {}).get("configuration", {}).get("name") if la.get("rocket") else None,
                            "mission": la.get("mission", {}).get("description") if la.get("mission") else None,
                            "pad": la.get("pad", {}).get("location", {}).get("name") if la.get("pad") else None,
                        })
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class WikipediaOnThisDayAPI(BaseAPI):
    category = "science"
    source = "wikimedia_otd"
    label = "On This Day"
    cache_ttl = 3600

    async def _fetch(self) -> APIResult:
        try:
            from datetime import datetime
            now = datetime.utcnow()
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "WorldDashboard/1.0"}) as c:
                r = await c.get(f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month:02d}/{now.day:02d}", follow_redirects=True)
                if r.status_code == 200:
                    data = r.json()
                    births = [{"text": e["text"], "year": e.get("year")} for e in data.get("births", [])[:5]]
                    deaths = [{"text": e["text"], "year": e.get("year")} for e in data.get("deaths", [])[:5]]
                    events = [{"text": e["text"], "year": e.get("year")} for e in data.get("events", [])[:5]]
                    return APIResult(category=self.category, source=self.source, label=self.label, data={"births": births, "deaths": deaths, "events": events})
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class WikipediaFeaturedAPI(BaseAPI):
    category = "science"
    source = "wikifeatured"
    label = "Wikipedia Featured"
    cache_ttl = 3600
    poll_interval = 3600

    async def _fetch(self) -> APIResult:
        try:
            from datetime import datetime
            now = datetime.utcnow()
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "WorldDashboard/1.0"}) as c:
                r = await c.get(f"https://en.wikipedia.org/api/rest_v1/feed/featured/{now.year}/{now.month:02d}/{now.day:02d}", follow_redirects=True)
                if r.status_code == 200:
                    data = r.json()
                    items = []
                    if data.get("tfa"):
                        tfa = data["tfa"]
                        items.append({"title": tfa.get("titles", {}).get("normalized", ""), "description": tfa.get("description", ""), "type": "featured_article", "url": tfa.get("content_urls", {}).get("desktop", {}).get("page", "")})
                    if data.get("mostread", {}).get("articles"):
                        for art in data["mostread"]["articles"][:5]:
                            items.append({"title": art.get("title", ""), "description": art.get("description", ""), "type": "most_read", "views": art.get("views"), "url": art.get("content_urls", {}).get("desktop", {}).get("page", "")})
                    if data.get("news"):
                        for news in data["news"][:3]:
                            items.append({"title": news.get("story", ""), "type": "news", "url": news.get("links", [{}])[0].get("url", "") if news.get("links") else ""})
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class arXivAPI(BaseAPI):
    category = "science"
    source = "arxiv"
    label = "arXiv New Papers"
    cache_ttl = 600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get("https://export.arxiv.org/api/query?search_query=all:quantum&sortBy=submittedDate&sortOrder=descending&max_results=10", follow_redirects=True)
                if r.status_code == 200:
                    import xml.etree.ElementTree as ET
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    root = ET.fromstring(r.text)
                    items = []
                    for entry in root.findall("atom:entry", ns)[:10]:
                        title_el = entry.find("atom:title", ns)
                        if title_el is not None and title_el.text:
                            items.append({"title": " ".join(title_el.text.split())})
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
