import os
from pathlib import Path
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()
conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
    role="TRANSFORMER", warehouse="ENERGY_WH",
    database="ENERGY", schema="BRONZE",
)
cur = conn.cursor()

for name in ["prices.csv", "power.csv"]:
    path = Path("data", name).resolve()
    # Quotes required: the local path contains a space ("projects ")
    cur.execute(f"PUT 'file://{path}' @RAW_STAGE OVERWRITE = TRUE")
    print(f"{name} uploaded to RAW_STAGE")

for row in cur.execute("LIST @RAW_STAGE"):
    print(row[0], row[1], "bytes")
conn.close()