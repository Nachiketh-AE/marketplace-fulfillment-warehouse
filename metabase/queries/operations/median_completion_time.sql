-- Median service execution time (IN_PROGRESS -> COMPLETED), minutes.
select
    service_category_name,
    percentile_cont(0.5) within group (order by in_progress_to_completed_minutes)
        as median_completion_minutes
from marts.mart_booking_lifecycle
where is_eligible_booking and final_status = 'COMPLETED'
group by 1
order by 2
