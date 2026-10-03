-- Cleaned day-ahead prices: readable timestamp, no duplicates or null values
select
    to_timestamp_ntz(unix_seconds) as price_ts_utc,
    price_eur_mwh,
    _loaded_at
from {{ source('bronze', 'raw_prices') }}
where price_eur_mwh is not null
qualify row_number() over (partition by unix_seconds order by _loaded_at desc) = 1