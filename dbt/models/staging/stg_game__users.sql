with source as (

    select * from {{ source('game', 'events') }}

),

renamed as (

    select
        cast(userid as bigint) as user_id,
        cast(version as varchar) as version,
        cast(acquisition_channel as varchar) as acquisition_channel,
        cast(country as varchar) as country,
        cast(platform as varchar) as platform,
        cast(session_count as bigint) as session_count,
        cast(retention_1 as boolean) as is_retained_d1,
        cast(retention_7 as boolean) as is_retained_d7,
        cast(purchase as boolean) as has_purchased,
        cast(cac as double) as cac,
        cast(revenue as double) as revenue,
        cast(roi as double) as roi

    from source

)

select * from renamed
