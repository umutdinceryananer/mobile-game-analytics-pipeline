-- ROAS is revenue / spend. ROI is (revenue - spend) / spend.
-- Revenue per install is revenue / users.

select *
from {{ ref('mart_channel_roi') }}
where abs(roas - revenue / ad_spend) > 1e-9
    or abs(roi - (revenue - ad_spend) / ad_spend) > 1e-9
    or abs(revenue_per_install - revenue / users) > 1e-9
