INSERT INTO events (event_id, event_type, occurred_at, payload)
VALUES (:event_id, :event_type, :occurred_at, :payload)
ON CONFLICT (event_id) DO NOTHING;
