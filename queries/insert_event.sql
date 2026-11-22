WITH new_event AS (
    INSERT INTO events (event_id, event_type, occurred_at, payload)
    VALUES (:event_id, :event_type, :occurred_at, :payload)
    ON CONFLICT (event_id) DO NOTHING
    RETURNING event_id
)
INSERT INTO event_deliveries (event_id, destination)
SELECT event_id, 'webhook'
FROM new_event;
