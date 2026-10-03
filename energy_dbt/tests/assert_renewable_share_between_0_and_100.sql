-- A share must always be between 0 and 100 %
select *
from {{ ref('fct_hourly_market') }}
where renewable_share_pct < 0 or renewable_share_pct > 100