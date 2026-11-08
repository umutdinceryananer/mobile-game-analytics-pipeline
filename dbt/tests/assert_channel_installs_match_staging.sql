-- The channel install counts must add up to the distinct players in staging.

with channel_installs as (

    select sum(users) as total_users
    from {{ ref('mart_installs_by_channel') }}

),

staging_users as (

    select count(distinct user_id) as total_users
    from {{ ref('stg_game__users') }}

)

select
    channel_installs.total_users as channel_total,
    staging_users.total_users as staging_total

from channel_installs
cross join staging_users
where channel_installs.total_users <> staging_users.total_users
