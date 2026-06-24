import React, { useEffect, useState } from 'react'
import { PartyPopper, Calendar, MapPin, Loader2 } from 'lucide-react'
import { routerAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import { formatDate } from '../utils/helpers'

export default function EventsPage() {
  useTitle('Events')
  const [loading, setLoading] = useState(true)
  const [events, setEvents] = useState([])

  useEffect(() => {
    routerAPI.ask({ query: 'What upcoming events are there?', context: { collection: 'events' } })
      .then(({ data }) => setEvents(data.data?.data?.upcoming_events || []))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Campus Events</h1>
        <p className="page-subtitle">Upcoming fests, seminars, and workshops</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>
      ) : events.length === 0 ? (
        <div className="card p-12 flex flex-col items-center text-center gap-3">
          <PartyPopper className="w-10 h-10 text-gray-300" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">No upcoming events scheduled</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {events.map(e => (
            <div key={e._id} className="card-hover p-5">
              <span className="badge-primary capitalize mb-2 inline-block">{e.event_type}</span>
              <h3 className="font-semibold text-gray-900 dark:text-white">{e.title}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{e.description}</p>
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-3">
                <Calendar className="w-3.5 h-3.5" /> {formatDate(e.event_date)}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-1">
                <MapPin className="w-3.5 h-3.5" /> {e.venue}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
