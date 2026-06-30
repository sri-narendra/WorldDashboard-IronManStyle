import httpx
from apis.base import BaseAPI, APIResult

class BlueskyAPI(BaseAPI):
    category = "social"
    source = "bluesky"
    label = "Bluesky Trending"
    cache_ttl = 120

    async def _auth_session(self) -> str | None:
        from config import config
        if not config.bluesky_identifier or not config.bluesky_password:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                    json={"identifier": config.bluesky_identifier, "password": config.bluesky_password})
                if r.status_code == 200:
                    return r.json().get("accessJwt")
        except Exception:
            pass
        return None

    async def _fetch(self) -> APIResult:
        token = await self._auth_session()
        if not token:
            return APIResult(category=self.category, source=self.source, label=self.label, error="No Bluesky credentials configured")
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://bsky.social/xrpc/app.bsky.feed.getTimeline", params={"limit": 10},
                    headers={"Authorization": f"Bearer {token}"})
                if r.status_code == 200:
                    items = []
                    for post in r.json().get("feed", []):
                        p = post.get("post", {})
                        author = p.get("author", {})
                        items.append({
                            "author": author.get("displayName", author.get("handle")),
                            "handle": author.get("handle"),
                            "text": p.get("record", {}).get("text", "")[:200],
                            "likes": p.get("likeCount"),
                            "reposts": p.get("repostCount"),
                            "replies": p.get("replyCount"),
                        })
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class GitHubTrendingAPI(BaseAPI):
    category = "social"
    source = "github"
    label = "GitHub Trending"
    cache_ttl = 300
    poll_interval = 300

    async def _fetch(self) -> APIResult:
        try:
            import re
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as c:
                r = await c.get("https://github.com/trending", follow_redirects=True)
                if r.status_code != 200:
                    return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
                items = []
                for article in re.findall(r'<article class="Box-row">(.*?)</article>', r.text, re.DOTALL)[:10]:
                    m = re.search(r'href="/([^"]+)"', article)
                    if not m:
                        continue
                    full_name = m.group(1)
                    desc_m = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', article, re.DOTALL)
                    desc = desc_m.group(1).strip() if desc_m else ""
                    stars_m = re.search(r'octicon-star.*?<span class="d-inline-block float-sm-right">\s*(\d[\d,]*)\s*</span>', article)
                    stars = stars_m.group(1).replace(",", "") if stars_m else "0"
                    forks_m = re.search(r'octicon-repo-forked.*?<span class="d-inline-block float-sm-right">\s*(\d[\d,]*)\s*</span>', article)
                    forks = forks_m.group(1).replace(",", "") if forks_m else "0"
                    today_m = re.search(r'class="d-inline-block float-sm-right">\s*(\d[\d,]*)\s*</span>\s*</span>\s*s tars\s+today', article, re.IGNORECASE)
                    today = today_m.group(1).replace(",", "") if today_m else "0"
                    items.append({"name": full_name, "url": f"https://github.com/{full_name}", "description": desc, "stars": int(stars), "forks": int(forks), "today_stars": int(today)})
                return APIResult(category=self.category, source=self.source, label=self.label, data=items)
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class ProductHuntAPI(BaseAPI):
    category = "social"
    source = "producthunt"
    label = "Product Hunt"
    cache_ttl = 600

    async def _fetch(self) -> APIResult:
        from config import config
        if not config.producthunt_key:
            return APIResult(category=self.category, source=self.source, label=self.label, error="No ProductHunt API key")
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                query = {"query": "{posts(first:10){nodes{name tagline url votesCount commentsCount createdAt}}}"}
                r = await c.post("https://api.producthunt.com/v2/api/graphql", json=query,
                    headers={"Authorization": f"Bearer {config.producthunt_key}"})
                if r.status_code == 200:
                    posts = r.json().get("data", {}).get("posts", {}).get("nodes", [])
                    items = [{"name": p["name"], "tagline": p["tagline"], "url": p["url"], "votes": p["votesCount"], "comments": p["commentsCount"]} for p in posts]
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
