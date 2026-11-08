with funnel as (

    select * from {{ ref('int_user_funnel') }}

),

totals as (

    select
        acquisition_channel,
        count(*) as users,
        sum(revenue) as revenue,
        sum(ad_spend) as ad_spend

    from funnel
    group by acquisition_channel

),

final as (

    select
        acquisition_channel,
        users,
        revenue,
        ad_spend,
        case when ad_spend > 0 then (revenue - ad_spend) / ad_spend end as roi,
        case when ad_spend > 0 then revenue / ad_spend end as roas

    from totals

)

select * from final
