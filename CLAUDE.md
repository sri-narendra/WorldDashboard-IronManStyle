## Bluesky live throttling

- Server: `watch_bluesky_push()` in `main.py:119` — broadcasts every 1.5s (not per-post), buffer capped at 10 items
- Frontend: `frontend/index.html` — `.widget-body` has `max-height: 300px; overflow-y: auto` to prevent column reflow
