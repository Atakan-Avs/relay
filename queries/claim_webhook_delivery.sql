WITH candidate AS (
    SELECT event_id, destination
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
    attempt_count = delivery.attempt_count + 1,
    next_attempt_at = CURRENT_TIMESTAMP + INTERVAL '30 seconds'
FROM candidate
JOIN events AS event USING (event_id)
WHERE delivery.event_id = candidate.event_id
    AND delivery.destination = candidate.destination
RETURNING
    delivery.event_id,
    delivery.attempt_count,
    event.event_type,
    event.occurred_at,
    event.payload;
