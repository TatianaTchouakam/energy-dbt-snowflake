import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://api.energy-charts.info"

# Default: yesterday (German local day). Override with START_DATE / END_DATE (YYYY-MM-DD).
yesterday = (datetime.now(ZoneInfo("Europe/Berlin")) - timedelta(days=1)).date().isoformat()
START = os.getenv("START_DATE", yesterday)
END = os.getenv("END_DATE", START)

# Retry temporary API failures (429 and 5xx) with exponential backoff: waits of 10, 20, 40, 80 and 160 s
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5,
    backoff_factor=10,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)))

OUT = Path("data"); OUT.mkdir(exist_ok=True)

# Remove files from previous runs, so a failed download can never lead to reloading old data
for old_file in OUT.glob("*.csv"):
    old_file.unlink()

# 1. Day-ahead prices (DE-LU bidding zone)
r = session.get(f"{BASE}/price", params={"bzn": "DE-LU", "start": START, "end": END}, timeout=60)
r.raise_for_status(); j = r.json()
prices = pd.DataFrame({"unix_seconds": j["unix_seconds"], "price_eur_mwh": j["price"]})
prices.to_csv(OUT / "prices.csv", index=False)

# 2. Power series (long format: one row = timestamp + series)
r = session.get(f"{BASE}/public_power", params={"country": "de", "start": START, "end": END}, timeout=120)
r.raise_for_status(); j = r.json()
rows = [(ts, p["name"], v) for p in j["production_types"]
        for ts, v in zip(j["unix_seconds"], p["data"])]
power = pd.DataFrame(rows, columns=["unix_seconds", "production_type", "value_mw"])
power.to_csv(OUT / "power.csv", index=False)

print(f"Period {START} -> {END}: {len(prices)} prices, {len(power)} power rows")
