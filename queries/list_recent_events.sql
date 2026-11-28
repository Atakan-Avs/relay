SELECT
    event.event_id,
    event.event_type,
    event.occurred_at,
    event.received_at,
    delivery.status AS delivery_status,
    delivery.attempt_count,
    delivery.next_attempt_at
FROM events AS event
LEFT JOIN event_deliveries AS delivery
    ON delivery.event_id = event.event_id
    AND delivery.destination = 'webhook'
ORDER BY event.received_at DESC, event.event_id DESC
LIMIT :limit;
