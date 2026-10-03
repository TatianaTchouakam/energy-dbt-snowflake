import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

BASE = "https://api.energy-charts.info"

# Default: yesterday (German local day). Override with START_DATE / END_DATE (YYYY-MM-DD).
yesterday = (datetime.now(ZoneInfo("Europe/Berlin")) - timedelta(days=1)).date().isoformat()
START = os.getenv("START_DATE", yesterday)
END = os.getenv("END_DATE", START)

OUT = Path("data"); OUT.mkdir(exist_ok=True)

# 1. Day-ahead prices (DE-LU bidding zone)
r = requests.get(f"{BASE}/price", params={"bzn": "DE-LU", "start": START, "end": END}, timeout=60)
r.raise_for_status(); j = r.json()
prices = pd.DataFrame({"unix_seconds": j["unix_seconds"], "price_eur_mwh": j["price"]})
prices.to_csv(OUT / "prices.csv", index=False)

# 2. Power series (long format: one row = timestamp + series)
r = requests.get(f"{BASE}/public_power", params={"country": "de", "start": START, "end": END}, timeout=120)
r.raise_for_status(); j = r.json()
rows = [(ts, p["name"], v) for p in j["production_types"]
        for ts, v in zip(j["unix_seconds"], p["data"])]
power = pd.DataFrame(rows, columns=["unix_seconds", "production_type", "value_mw"])
power.to_csv(OUT / "power.csv", index=False)

print(f"Period {START} -> {END}: {len(prices)} prices, {len(power)} power rows")
