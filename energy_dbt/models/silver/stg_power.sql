-- Cleaned and classified power generation and grid indicators
with source as (
    select *
    from {{ source('bronze', 'raw_power') }}
    where value_mw is not null
    qualify row_number() over (
        partition by unix_seconds, production_type order by _loaded_at desc
    ) = 1
),

classified as (
    select
        to_timestamp_ntz(unix_seconds) as power_ts_utc,
        production_type,
        value_mw as value,

        case
            when production_type ilike 'Renewable share%' then 'share'
            when production_type in ('Load', 'Residual load') then 'load'
            when production_type ilike '%consumption%'
              or production_type ilike 'Cross border%' then 'balance'
            else 'generation'
        end as series_type,

        case
            when production_type ilike 'Solar%' then 'Solar'
            when production_type ilike 'Wind%' then 'Wind'
            when production_type ilike 'Hydro pumped storage%' then 'Storage'
            when production_type ilike 'Hydro%'
              or production_type in ('Biomass', 'Geothermal') then 'Other renewable'
            when production_type ilike 'Fossil%' then 'Fossil'
            else 'Other'
        end as source_group,

        _loaded_at
    from source
)

select
    *,
    iff(series_type = 'share', '%', 'MW') as unit,
    source_group in ('Solar', 'Wind', 'Other renewable') as is_renewable
from classified