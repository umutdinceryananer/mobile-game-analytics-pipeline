-- Compares stage totals, overall and per channel. The generated flags are not
-- nested per player, so a per-player version of this check would not hold.

with channel_totals as (

    select
        acquisition_channel,
        sum(install_flag) as installs,
        sum(d1_flag) as d1_returns,
        sum(d7_flag) as d7_returns,
        sum(purchase_flag) as purchases

    from {{ ref('int_user_funnel') }}
    group by acquisition_channel

),

overall_totals as (

    select
        'all channels' as acquisition_channel,
        sum(installs) as installs,
        sum(d1_returns) as d1_returns,
        sum(d7_returns) as d7_returns,
        sum(purchases) as purchases

    from channel_totals

),

totals as (

    select * from channel_totals
    union all
    select * from overall_totals

)

select *
from totals
where d1_returns > installs
    or d7_returns > d1_returns
    or purchases > d7_returns
