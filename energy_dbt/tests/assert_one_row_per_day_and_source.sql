-- Each day must have exactly one row per source group
select day_local, source_group, count(*) as nb_rows
from {{ ref('fct_daily_generation') }}
group by 1, 2
having count(*) > 1