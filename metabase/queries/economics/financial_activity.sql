-- Posted captures, refunds, and reversals by financial-event date.
select
    (occurred_at at time zone 'America/New_York')::date as financial_event_date,
    event_type,
    sum(amount) as amount
from core.fct_payment
group by 1, 2
order by 1, 2
