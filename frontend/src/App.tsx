import { useEffect, useState } from 'react'

const statusLabels = {
  pending: 'Bekliyor',
  delivered: 'Teslim edildi',
  failed: 'Başarısız',
}

type EventSummary = {
  event_id: string
  event_type: string
  received_at: string
  delivery_status: keyof typeof statusLabels | null
  attempt_count: number | null
  next_attempt_at: string | null
}

const dateTime = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'short',
  timeStyle: 'medium',
})

function formatTime(value: string | null) {
  return value === null ? '—' : dateTime.format(new Date(value))
}

export default function App() {
  const [events, setEvents] = useState<EventSummary[] | null>(null)
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    async function loadEvents() {
      try {
        const response = await fetch('/v1/events', { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`Request failed with HTTP ${response.status}`)
        }
        const rows: EventSummary[] = await response.json()
        if (!controller.signal.aborted) setEvents(rows)
      } catch {
        if (!controller.signal.aborted) setHasError(true)
      }
    }

    void loadEvents()
    return () => controller.abort()
  }, [])

  return (
    <main>
      <h1>Relay · Son event’ler</h1>

      {hasError && (
        <p role="alert">Event’ler yüklenemedi. API bağlantısını kontrol et.</p>
      )}
      {!hasError && events === null && <p role="status">Event’ler yükleniyor…</p>}
      {events?.length === 0 && <p>Henüz event kaydı yok.</p>}

      {events && events.length > 0 && (
        <div className="table-wrap">
          <table aria-label="Son event’ler">
            <thead>
              <tr>
                <th scope="col">Event</th>
                <th scope="col">Alınma zamanı</th>
                <th scope="col">Webhook durumu</th>
                <th scope="col">Deneme</th>
                <th scope="col">Sonraki deneme</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.event_id}>
                  <td>{event.event_type}</td>
                  <td>{formatTime(event.received_at)}</td>
                  <td data-status={event.delivery_status}>
                    {event.delivery_status === null
                      ? 'Teslimat kaydı yok'
                      : statusLabels[event.delivery_status]}
                  </td>
                  <td>{event.attempt_count ?? '—'}</td>
                  <td>{formatTime(event.next_attempt_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
