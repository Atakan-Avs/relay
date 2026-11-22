WITH candidate AS (
    SELECT event_id, destination, attempt_count >= :max_attempts AS exhausted
    FROM event_deliveries
    WHERE destination = 'webhook'
        AND status = 'pending'
        AND next_attempt_at <= CURRENT_TIMESTAMP
    ORDER BY next_attempt_at, event_id
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE event_deliveries AS delivery
SET
    status = CASE WHEN candidate.exhausted THEN 'failed' ELSE 'pending' END,
    attempt_count = delivery.attempt_count + CASE WHEN candidate.exhausted THEN 0 ELSE 1 END,
    next_attempt_at = CASE
        WHEN candidate.exhausted THEN NULL
        ELSE CURRENT_TIMESTAMP + INTERVAL '30 seconds'
    END
FROM candidate
JOIN events AS event USING (event_id)
WHERE delivery.event_id = candidate.event_id
    AND delivery.destination = candidate.destination
RETURNING
    delivery.status,
    delivery.event_id,
    delivery.attempt_count,
    event.event_type,
    event.occurred_at,
    event.payload;
