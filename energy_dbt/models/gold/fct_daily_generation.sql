-- Daily generation by source group, in GWh (day in German local time)
select
    date(convert_timezone('UTC', 'Europe/Berlin', power_ts_utc)) as day_local,
    source_group,
    any_value(is_renewable)                    as is_renewable,
    round(sum(value) * 0.25 / 1000, 2)         as energy_gwh
from {{ ref('stg_power') }}
where series_type = 'generation'
group by 1, 2