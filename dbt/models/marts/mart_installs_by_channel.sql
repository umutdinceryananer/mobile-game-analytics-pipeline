with funnel as (

    select * from {{ ref('int_user_funnel') }}

),

final as (

    select
        acquisition_channel,
        count(*) as users

    from funnel
    group by acquisition_channel

)

select * from final
