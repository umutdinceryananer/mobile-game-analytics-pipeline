{% docs roas %}
Return on ad spend: revenue earned per unit of acquisition spend, calculated as `revenue / ad_spend`.
{% enddocs %}

{% docs roi %}
Return on investment: net return per unit of acquisition spend, calculated as `(revenue - ad_spend) / ad_spend`.
{% enddocs %}

{% docs funnel_step_rate %}
Funnel step rate: the total of one stage relative to the stage before it, calculated as `later stage total / earlier stage total`; the generated flags are not nested per player, so it is a ratio of totals and not a conversion rate.
{% enddocs %}

{% docs d1_retention %}
D1 retention: whether players returned on the first day after install, calculated across players as `players who returned on D1 / all players`.
{% enddocs %}

{% docs d7_retention %}
D7 retention: whether players returned on the seventh day after install, calculated across players as `players who returned on D7 / all players`.
{% enddocs %}
