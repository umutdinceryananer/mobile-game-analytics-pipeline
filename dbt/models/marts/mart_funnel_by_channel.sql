with funnel as (

    select * from {{ ref('int_user_funnel') }}

),

steps as (

    select
        acquisition_channel,
        count(*) as n_users,
        sum(d1_flag) as s_d1,
        sum(d7_flag) as s_d7,
        sum(purchase_flag) as s_purchase

    from funnel
    group by acquisition_channel

),

final as (

    select
        acquisition_channel,
        n_users,
        {{ dbt_utils.safe_divide('s_d1', 'n_users') }} as rate_d1_from_install,
        {{ dbt_utils.safe_divide('s_d7', 's_d1') }} as rate_d7_from_d1,
        {{ dbt_utils.safe_divide('s_purchase', 'n_users') }} as rate_purchase_overall

    from steps

)

select * from final
