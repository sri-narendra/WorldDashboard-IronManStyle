import asyncio
import httpx
from apis.base import BaseAPI, APIResult

class HackerNewsAPI(BaseAPI):
    category = "news"
    source = "hackernews"
    label = "Hacker News"
    cache_ttl = 60

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                ids = (await c.get("https://hacker-news.firebaseio.com/v0/topstories.json")).json()[:20]

                async def get_item(i):
                    r = await c.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json")
                    return r.json()

                raw = await asyncio.gather(*(get_item(i) for i in ids))
                items = [
                    {"title": item.get("title"), "url": item.get("url"), "score": item.get("score"), "by": item.get("by"), "descendants": item.get("descendants")}
                    for item in raw if item
                ]
                return APIResult(category=self.category, source=self.source, label=self.label, data=items)
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class RedditAPI(BaseAPI):
    category = "news"
    source = "reddit"
    label = "Reddit Hot"
    cache_ttl = 60
    poll_interval = 60

    async def _fetch(self) -> APIResult:
        try:
            import xml.etree.ElementTree as ET
            subs = [("worldnews", 5), ("news", 5), ("science", 3), ("technology", 3), ("UpliftingNews", 2), ("EverythingScience", 2)]
            items = []
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as c:
                for sub, lim in subs:
                    r = await c.get(f"https://www.reddit.com/r/{sub}/hot/.rss?limit={lim}", follow_redirects=True)
                    if r.status_code == 200:
                        root = ET.fromstring(r.text)
                        ns = {"atom": "http://www.w3.org/2005/Atom"}
                        for entry in list(root.findall(".//atom:entry", ns))[:lim]:
                            title = entry.find("atom:title", ns)
                            link = entry.find("atom:link", ns)
                            items.append({"subreddit": sub, "title": title.text if title is not None else "", "url": link.get("href") if link is not None else ""})
            if items:
                return APIResult(category=self.category, source=self.source, label=self.label, data=items)
            return APIResult(category=self.category, source=self.source, label=self.label, error="No Reddit data")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class GNewsAPI(BaseAPI):
    category = "news"
    source = "gnews"
    label = "Google News Top"
    cache_ttl = 120
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            import xml.etree.ElementTree as ET
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as c:
                r = await c.get("https://news.google.com/rss/search?q=top+headlines&hl=en-US&gl=US&ceid=US:en", follow_redirects=True)
                if r.status_code == 200:
                    root = ET.fromstring(r.text)
                    items = []
                    for entry in root.findall(".//item")[:10]:
                        title = entry.findtext("title")
                        link = entry.findtext("link")
                        source = entry.findtext("source")
                        if title:
                            items.append({"title": title, "url": link or "", "source": source or "Google News"})
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class SpaceflightNewsAPI(BaseAPI):
    category = "news"
    source = "spaceflightnews"
    label = "Spaceflight News"
    cache_ttl = 120
    poll_interval = 30

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://api.spaceflightnewsapi.net/v4/articles/?limit=10")
                if r.status_code == 200:
                    articles = [{"title": a["title"], "url": a["url"], "news_site": a["news_site"], "published": a["published_at"]} for a in r.json()["results"]]
                    return APIResult(category=self.category, source=self.source, label=self.label, data=articles)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class GoogleNewsRSSAPI(BaseAPI):
    category = "news"
    source = "googlenews"
    label = "Google News"
    cache_ttl = 120
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            import xml.etree.ElementTree as ET
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as c:
                r = await c.get("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", follow_redirects=True)
                if r.status_code == 200:
                    root = ET.fromstring(r.text)
                    items = []
                    for entry in root.findall(".//item")[:10]:
                        title = entry.findtext("title")
                        link = entry.findtext("link")
                        pubdate = entry.findtext("pubDate")
                        if title:
                            items.append({"title": title, "url": link or "", "date": (pubdate or "")[:10]})
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class WikimediaOnThisDayAPI(BaseAPI):
    category = "news"
    source = "wikimedia"
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
