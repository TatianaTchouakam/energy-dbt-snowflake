-- Hourly price versus generation and load for the same hour
with prices_hourly as (
    -- Day-ahead prices are hourly before Oct 2025 and quarter-hourly after: average per hour
    select
        date_trunc('hour', price_ts_utc) as hour_utc,
        avg(price_eur_mwh)               as price_eur_mwh
    from {{ ref('stg_prices') }}
    group by 1
),

hourly_by_type as (
    -- Generation data is quarter-hourly: average per hour and per series
    select
        date_trunc('hour', power_ts_utc) as hour_utc,
        production_type,
        series_type,
        is_renewable,
        avg(value) as avg_mw
    from {{ ref('stg_power') }}
    group by all
),

hourly as (
    select
        hour_utc,
        sum(iff(series_type = 'generation', avg_mw, 0))                  as generation_mw,
        sum(iff(series_type = 'generation' and is_renewable, avg_mw, 0)) as renewable_mw,
        sum(iff(production_type = 'Load', avg_mw, 0))                    as load_mw
    from hourly_by_type
    group by hour_utc
)

select
    p.hour_utc,
    round(p.price_eur_mwh, 2)                                   as price_eur_mwh,
    round(h.generation_mw)                                      as generation_mw,
    round(h.renewable_mw)                                       as renewable_mw,
    round(h.load_mw)                                            as load_mw,
    round(h.renewable_mw / nullif(h.generation_mw, 0) * 100, 1) as renewable_share_pct,
    p.price_eur_mwh < 0                                         as is_negative_price
from prices_hourly p
left join hourly h on p.hour_utc = h.hour_utc
