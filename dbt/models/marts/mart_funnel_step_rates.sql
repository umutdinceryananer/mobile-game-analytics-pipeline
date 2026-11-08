with funnel as (

    select * from {{ ref('int_user_funnel') }}

),

steps as (

    select
        count(*) as n_users,
        sum(install_flag) as s_install,
        sum(d1_flag) as s_d1,
        sum(d7_flag) as s_d7,
        sum(purchase_flag) as s_purchase

    from funnel

),

final as (

    select
        n_users,
        {{ dbt_utils.safe_divide('s_install', 'n_users') }} as rate_install,
        {{ dbt_utils.safe_divide('s_d1', 's_install') }} as rate_d1_from_install,
        {{ dbt_utils.safe_divide('s_d7', 's_d1') }} as rate_d7_from_d1,
        {{ dbt_utils.safe_divide('s_purchase', 's_d7') }} as rate_purchase_from_d7

    from steps

)

select * from final
