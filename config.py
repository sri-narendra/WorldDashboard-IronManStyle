import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    reddit_client_id: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")
    producthunt_key: Optional[str] = os.getenv("PRODUCTHUNT_KEY")
    bluesky_identifier: Optional[str] = os.getenv("BLUESKY_IDENTIFIER")
    bluesky_password: Optional[str] = os.getenv("BLUESKY_PASSWORD")

    poll_interval: int = 120
    host: str = "0.0.0.0"
    port: int = 8000

config = Config()
