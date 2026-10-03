import os

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()  # local runs read .env; in CI, variables come from GitHub secrets

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
    role="TRANSFORMER", warehouse="ENERGY_WH",
    database="ENERGY", schema="GOLD",
)
cur = conn.cursor()

# Most recent day available in Gold
day = cur.execute("SELECT MAX(day_local) FROM fct_daily_generation").fetchone()[0]

# Generation by source group for that day
generation = cur.execute(
    """
    SELECT source_group, energy_gwh, is_renewable
    FROM fct_daily_generation
    WHERE day_local = %s
    ORDER BY energy_gwh DESC
    """,
    (day,),
).fetchall()

# Market KPIs for the same German local day
avg_price, min_price, max_price, negative_hours = cur.execute(
    """
    SELECT ROUND(AVG(price_eur_mwh), 1), ROUND(MIN(price_eur_mwh), 1),
           ROUND(MAX(price_eur_mwh), 1), COUNT_IF(is_negative_price)
    FROM fct_hourly_market
    WHERE DATE(CONVERT_TIMEZONE('UTC', 'Europe/Berlin', hour_utc)) = %s
    """,
    (day,),
).fetchone()
conn.close()

total = sum(gwh for _, gwh, _ in generation)
renewable = sum(gwh for _, gwh, is_ren in generation if is_ren)

lines = [
    f"## ⚡ German electricity market — {day}",
    "",
    "| KPI | Value |",
    "|---|---|",
    f"| Total generation | {total:,.1f} GWh |",
    f"| Renewable share | {renewable / total * 100:.1f} % |",
    f"| Average day-ahead price | {avg_price} EUR/MWh |",
    f"| Price range | {min_price} → {max_price} EUR/MWh |",
    f"| Hours with negative prices | {negative_hours} |",
    "",
    "### Generation by source group",
    "",
    "| Source group | GWh | Share |",
    "|---|---|---|",
]
lines += [f"| {group} | {gwh:,.1f} | {gwh / total * 100:.1f} % |" for group, gwh, _ in generation]
summary = "\n".join(lines) + "\n"

# On GitHub Actions, write to the run summary page; locally, just print
summary_path = os.getenv("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(summary)
print(summary)
