with users as (

    select * from {{ ref('stg_game__users') }}

),

final as (

    select
        user_id,
        acquisition_channel,
        1 as install_flag,
        case when is_retained_d1 then 1 else 0 end as d1_flag,
        case when is_retained_d7 then 1 else 0 end as d7_flag,
        case when has_purchased then 1 else 0 end as purchase_flag,
        coalesce(revenue, 0.0) as revenue,
        coalesce(cac, 0.0) as ad_spend

    from users

)

select * from final
