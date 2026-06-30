import httpx
from apis.base import BaseAPI, APIResult

class CoinGeckoAPI(BaseAPI):
    category = "finance"
    source = "coingecko"
    label = "Crypto Market"
    cache_ttl = 120
    poll_interval = 15

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=15&page=1&sparkline=false")
                if r.status_code == 200:
                    items = [{"name": c["name"], "symbol": c["symbol"].upper(), "price": c["current_price"], "change_24h": c["price_change_percentage_24h"], "market_cap": c["market_cap"], "volume": c["total_volume"]} for c in r.json()]
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class FrankfurterFXAPI(BaseAPI):
    category = "finance"
    source = "frankfurter"
    label = "Forex Rates"
    cache_ttl = 3600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://api.frankfurter.app/latest?from=USD", follow_redirects=True)
                if r.status_code == 200:
                    rates = r.json().get("rates", {})
                    major = {k: rates[k] for k in ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "INR", "BRL", "MXN", "KRW", "SGD", "NZD"] if k in rates}
                    return APIResult(category=self.category, source=self.source, label=self.label, data={"base": "USD", "rates": major, "date": r.json().get("date")})
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class AlternativeFearGreedAPI(BaseAPI):
    category = "finance"
    source = "fear_greed"
    label = "Crypto Fear & Greed"
    cache_ttl = 3600

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://api.alternative.me/fng/?limit=7")
                if r.status_code == 200:
                    items = [{"value": d["value"], "classification": d["value_classification"], "timestamp": d["timestamp"]} for d in r.json().get("data", [])]
                    return APIResult(category=self.category, source=self.source, label=self.label, data=items)
                return APIResult(category=self.category, source=self.source, label=self.label, error=f"HTTP {r.status_code}")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))

class MempoolSpaceAPI(BaseAPI):
    category = "finance"
    source = "mempool"
    label = "Bitcoin Mempool"
    cache_ttl = 60
    poll_interval = 1.5

    async def _fetch(self) -> APIResult:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                fees = await c.get("https://mempool.space/api/v1/fees/recommended")
                blocks = await c.get("https://mempool.space/api/blocks?limit=5")
                if fees.status_code == 200 and blocks.status_code == 200:
                    return APIResult(category=self.category, source=self.source, label=self.label, data={
                        "fees": fees.json(),
                        "latest_blocks": [{"height": b["height"], "time": b["timestamp"], "tx_count": b["tx_count"], "size": b["size"]} for b in blocks.json()]
                    })
                return APIResult(category=self.category, source=self.source, label=self.label, error="Mempool fetch failed")
        except Exception as e:
            return APIResult(category=self.category, source=self.source, label=self.label, error=str(e))
