import os
from datetime import datetime, timezone
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()  # local runs read .env; in CI, variables come from GitHub secrets

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
    role="TRANSFORMER", warehouse="ENERGY_WH",
    database="ENERGY", schema="BRONZE",
)
cur = conn.cursor()

# One stage folder per run, so each load is traceable and never overwrites a previous one
run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

for name in ["prices.csv", "power.csv"]:
    path = Path("data", name).resolve()
    # Quotes required: the local path may contain spaces
    cur.execute(f"PUT 'file://{path}' @RAW_STAGE/{run_id}/ OVERWRITE = TRUE")
    print(f"{name} uploaded to RAW_STAGE/{run_id}/")

copies = {
    "RAW_PRICES": f"SELECT $1, $2, METADATA$FILENAME, CURRENT_TIMESTAMP() FROM @RAW_STAGE/{run_id}/prices.csv",
    "RAW_POWER": f"SELECT $1, $2, $3, METADATA$FILENAME, CURRENT_TIMESTAMP() FROM @RAW_STAGE/{run_id}/power.csv",
}
for table, select in copies.items():
    for row in cur.execute(f"COPY INTO {table} FROM ({select})"):
        print(f"{table}: {row[1]}, {row[3]} rows loaded")

conn.close()
