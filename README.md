# WORLD DASHBOARD // J.A.R.V.I.S.

Multi-source real-time world dashboard with an Iron Man JARVIS/HUD-themed interface. Aggregates 25+ data sources across news, weather, finance, science, space, sports, health, government, and more — all updating continuously.

![Theme](https://img.shields.io/badge/THEME-JARVIS-00d4ff?style=flat)
![Python](https://img.shields.io/badge/Python-3.10+-00d4ff?style=flat)
![License](https://img.shields.io/badge/License-MIT-00d4ff?style=flat)

## Features

- **25+ live data sources** — no API key required for most
- **Iron Man JARVIS UI** — cyan holographic HUD, scanlines, radar sweep, arc reactor
- **Real-time WebSocket** push — cards update live as data arrives
- **Masonry card layout** — responsive, category-filterable
- **Clickable news links** — all articles open in new tabs
- **Dark theme** — deep navy background, cyan glow accents

## Data Sources

| Category | Sources |
|---|---|
| **News** | Google News RSS, GNews, Hacker News, Product Hunt, Reddit, Bluesky, The Guardian, Wikipedia Current Events, Space News |
| **Weather** | Open-Meteo (forecast), Air Quality, USGS Earthquakes, Marine Weather |
| **Finance** | CoinGecko (crypto), Frankfurter (forex), Fear & Greed Index, Mempool (Bitcoin fees) |
| **Science** | NASA APOD, ISS Tracking, Launch Library, arXiv, Wikipedia Featured, Wikipedia On This Day |
| **Environment** | Marine Weather, NOAA Aurora Forecast (Kp-index) |
| **Government** | US Treasury Debt, Rest Countries |
| **Sports** | NBA Live, OpenF1 |
| **Social** | GitHub Trending |
| **Health** | Disease.sh (COVID-19) |
| **Transport** | OpenSky (live flights) |
| **Calendar** | Wikipedia On This Day |

## Setup

```bash
# Clone
git clone https://github.com/sri-narendra/WorldDashboard-IronManStyle.git
cd WorldDashboard-IronManStyle

# Install deps
pip install -r requirements.txt

# Optional: set API keys in environment for Reddit, Product Hunt, Bluesky
# (most sources work without any keys)

# Run
python main.py
```

Then open `http://localhost:5000` in your browser.

### Environment Variables (optional)

| Variable | Source |
|---|---|
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit API |
| `PRODUCTHUNT_KEY` | Product Hunt API |
| `BLUESKY_IDENTIFIER` / `BLUESKY_PASSWORD` | Bluesky |

## Tech

- **Backend**: Python, asyncio, WebSockets (Flask-SocketIO)
- **Frontend**: Single-file HTML+CSS+JS, CSS Grid masonry, Canvas starfield
- **Fonts**: Orbitron (HUD display), Rajdhani (body)
- **Color**: `#00d4ff` cyan primary, `#0a0e17` deep navy background

## License

MIT
