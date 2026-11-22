UPDATE event_deliveries
SET
    status = CASE WHEN CAST(:retry_seconds AS integer) IS NULL THEN 'failed' ELSE 'pending' END,
    next_attempt_at = CURRENT_TIMESTAMP + CAST(:retry_seconds AS integer) * INTERVAL '1 second'
WHERE event_id = :event_id
    AND destination = 'webhook'
    AND status = 'pending'
    AND attempt_count = :attempt_count
RETURNING status;
