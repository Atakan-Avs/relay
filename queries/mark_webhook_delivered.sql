UPDATE event_deliveries
SET status = 'delivered', next_attempt_at = NULL
WHERE event_id = :event_id
    AND destination = 'webhook'
    AND status = 'pending'
    AND attempt_count = :attempt_count
RETURNING event_id;
