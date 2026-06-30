import asyncio
import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import httpx

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apis.base import APIResult
from apis.news import HackerNewsAPI, RedditAPI, GNewsAPI, SpaceflightNewsAPI, GoogleNewsRSSAPI, WikimediaOnThisDayAPI
from apis.weather import OpenMeteoAPI, OpenMeteoAirQualityAPI, USGSEarthquakeAPI
from apis.finance import CoinGeckoAPI, FrankfurterFXAPI, AlternativeFearGreedAPI, MempoolSpaceAPI
from apis.environment import GDACSAPI, OpenMeteoMarineAPI, RainViewerAPI, AuroraForecastAPI
from apis.science import NASAAPODAPI, OpenNotifyISSAPI, LaunchLibraryAPI, WikipediaOnThisDayAPI, WikipediaFeaturedAPI, arXivAPI
from apis.sports import OpenF1API, NBALiveAPI
from apis.social import BlueskyAPI, ProductHuntAPI, GitHubTrendingAPI
from apis.government import RestCountriesAPI, NagerHolidaysAPI, USDebtAPI
from apis.transport import OpenSkyAPI
from apis.health import OpenDiseaseAPI, GlobalHealthAPI
from apis.calendar import NagerDateAPI

from config import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worlddashboard")

SOURCES: list[Any] = [
    HackerNewsAPI(), RedditAPI(), GNewsAPI(), SpaceflightNewsAPI(), GoogleNewsRSSAPI(), WikimediaOnThisDayAPI(),
    OpenMeteoAPI(), OpenMeteoAirQualityAPI(), USGSEarthquakeAPI(),
    CoinGeckoAPI(), FrankfurterFXAPI(), AlternativeFearGreedAPI(), MempoolSpaceAPI(),
    GDACSAPI(), OpenMeteoMarineAPI(), RainViewerAPI(), AuroraForecastAPI(),
    NASAAPODAPI(), OpenNotifyISSAPI(), LaunchLibraryAPI(), WikipediaOnThisDayAPI(), WikipediaFeaturedAPI(), arXivAPI(),
    OpenF1API(), NBALiveAPI(),
    BlueskyAPI(), ProductHuntAPI(), GitHubTrendingAPI(),
    RestCountriesAPI(), NagerHolidaysAPI(), USDebtAPI(),
    OpenSkyAPI(),
    OpenDiseaseAPI(), GlobalHealthAPI(),
    NagerDateAPI(),
]

SRC_MAP = {(s.category, s.source): s for s in SOURCES}
CATEGORIES: dict[str, list[Any]] = {}
for s in SOURCES:
    CATEGORIES.setdefault(s.category, []).append(s)

results: dict[str, APIResult] = {}
ws_clients: set[WebSocket] = set()


async def broadcast_update(key: str, result: APIResult):
    msg = json.dumps({"type": "source_update", "key": key, "data": result.dict()})
    dead = set()
    for ws in list(ws_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    ws_clients.difference_update(dead)


async def poll_source(src):
    key = f"{src.category}/{src.source}"
    interval = getattr(src, 'poll_interval', None) or (15 if src.cache_ttl <= 60 else src.cache_ttl)
    while True:
        try:
            result = await src._fetch()
            result.updated_at = time.time()
            src._save_cache(result)
            results[key] = result
            await broadcast_update(key, result)
            log.info("OK %s", key)
        except Exception as e:
            log.error("FAIL %s: %s", key, e)
        await asyncio.sleep(interval)


async def watch_hn_push():
    key = "news/hackernews"
    seen: set[int] = set()
    headers = {"Accept": "text/event-stream"}
    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as c:
                async with c.stream("GET", "https://hacker-news.firebaseio.com/v0/topstories.json", headers=headers) as resp:
                    event_type = None
                    async for line in resp.aiter_lines():
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            if event_type in ("put", "patch"):
                                try:
                                    all_ids = json.loads(line.split(":", 1)[1].strip()).get("data", [])
                                except Exception:
                                    continue
                                if isinstance(all_ids, list):
                                    new_ids = [i for i in all_ids[:20] if i not in seen]
                                    if new_ids:
                                        seen.update(new_ids)
                                        async with httpx.AsyncClient(timeout=15) as c2:
                                            async def get_item(i):
                                                r = await c2.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json")
                                                return r.json()
                                            raw = await asyncio.gather(*(get_item(i) for i in new_ids))
                                        items = [{"title": item.get("title"), "url": item.get("url"), "score": item.get("score"), "by": item.get("by"), "descendants": item.get("descendants")} for item in raw if item]
                                        result = APIResult(category="news", source="hackernews", label="Hacker News", data=items)
                                        results[key] = result
                                        await broadcast_update(key, result)
                                        log.info("PUSH %s: %d new", key, len(new_ids))
                        elif line.strip() == "":
                            event_type = None
        except Exception as e:
            log.error("HN push reconnect (%s)", e)
            await asyncio.sleep(10)


async def watch_bluesky_push():
    key = "social/bluesky"
    buffer: list[dict] = []
    last_broadcast = 0.0
    while True:
        try:
            import websockets
            url = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
            async with websockets.connect(url) as ws:
                async for message in ws:
                    event = json.loads(message)
                    commit = event.get("commit", {})
                    if event.get("kind") == "commit" and commit.get("operation") == "create":
                        record = commit.get("record", {})
                        if record.get("$type") == "app.bsky.feed.post":
                            text = (record.get("text") or "")[:200]
                            author = event.get("did", "")
                            buffer.insert(0, {"author": author, "text": text, "likes": 0, "reposts": 0, "replies": 0})
                            if len(buffer) > 10:
                                buffer.pop()
                            now = asyncio.get_event_loop().time()
                            if now - last_broadcast >= 1.5:
                                last_broadcast = now
                                result = APIResult(category="social", source="bluesky", label="Bluesky Live", data=list(buffer))
                                results[key] = result
                                await broadcast_update(key, result)
        except Exception as e:
            log.error("Bluesky push reconnect (%s)", e)
            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [asyncio.create_task(poll_source(src)) for src in SOURCES]
    tasks.append(asyncio.create_task(watch_hn_push()))
    tasks.append(asyncio.create_task(watch_bluesky_push()))
    yield
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FRONTEND = Path("frontend")


@app.get("/api/all")
async def get_all():
    return {k: v.dict() for k, v in results.items()}


@app.get("/api/categories")
async def get_categories():
    return {cat: [{"source": s.source, "label": s.label} for s in srcs] for cat, srcs in CATEGORIES.items()}


@app.get("/api/{category}/{source}")
async def get_source(category: str, source: str):
    key = f"{category}/{source}"
    if key in results:
        return results[key].dict()
    src = SRC_MAP.get((category, source))
    if src:
        r = await src.fetch()
        results[key] = r
        await broadcast_update(key, r)
        return r.dict()
    return {"error": "not found"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    if results:
        await ws.send_text(json.dumps({"type": "update", "data": {k: v.dict() for k, v in results.items()}}))

    async def heartbeat():
        while True:
            await asyncio.sleep(25)
            try:
                await ws.send_text(json.dumps({"type": "heartbeat"}))
            except Exception:
                break
    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        hb_task.cancel()
        ws_clients.discard(ws)


if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/")
    async def index():
        return FileResponse(FRONTEND / "index.html")

    @app.get("/{path:path}")
    async def catch_all(path: str):
        f = FRONTEND / path
        if f.is_file():
            return FileResponse(f)
        return FileResponse(FRONTEND / "index.html")
else:
    log.warning("No frontend/ directory — API-only mode")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
