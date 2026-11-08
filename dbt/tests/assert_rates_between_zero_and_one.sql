-- Checks every rate_* column of the funnel marts, including ones added later.
-- Missing values are covered by the not_null tests on those columns.

with step_rates as (

    unpivot {{ ref('mart_funnel_step_rates') }}
    on columns('^rate_')
    into name metric value rate

),

channel_rates as (

    unpivot {{ ref('mart_funnel_by_channel') }}
    on columns('^rate_')
    into name metric value rate

),

all_rates as (

    select metric, rate from step_rates
    union all
    select metric, rate from channel_rates

)

select *
from all_rates
where rate < 0 or rate > 1
