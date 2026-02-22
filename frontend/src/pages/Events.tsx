import { Link } from 'react-router-dom'
import { Plus, Calendar, Users, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useEvents } from '@/hooks/useEvents'
import { formatDate, formatDateTime, formatCurrency, getStatusColor, getStatusLabel, cn } from '@/lib/utils'

export function EventsPage() {
  const { data, isLoading } = useEvents({ upcoming: true })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Wydarzenia</h1>
          <p className="text-gray-500">Rejsy, spływy, szkolenia i spotkania</p>
        </div>
        <Button asChild>
          <Link to="/events/new">
            <Plus className="mr-2 h-4 w-4" />
            Nowe wydarzenie
          </Link>
        </Button>
      </div>

      {/* Events list */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="text-gray-500">Ładowanie...</div>
        </div>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Calendar className="h-12 w-12 text-gray-300" />
            <p className="mt-4 text-lg font-medium text-gray-500">Brak nadchodzących wydarzeń</p>
            <Button asChild className="mt-4">
              <Link to="/events/new">Utwórz pierwsze wydarzenie</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data?.items.map((event) => (
            <Card key={event.id} className="overflow-hidden">
              <div className="flex flex-col md:flex-row">
                {/* Date badge */}
                <div className="flex items-center justify-center bg-primary px-6 py-4 text-white md:flex-col">
                  <span className="text-3xl font-bold">
                    {new Date(event.start_date).getDate()}
                  </span>
                  <span className="ml-2 text-sm uppercase md:ml-0">
                    {new Date(event.start_date).toLocaleDateString('pl-PL', { month: 'short' })}
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1 p-6">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/events/${event.id}`}
                          className="text-xl font-semibold hover:text-primary"
                        >
                          {event.name}
                        </Link>
                        <Badge className={cn('font-normal', getStatusColor(event.status))}>
                          {getStatusLabel(event.status)}
                        </Badge>
                        <Badge variant="outline">{getStatusLabel(event.type)}</Badge>
                      </div>

                      <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDateTime(event.start_date)}
                          {event.end_date !== event.start_date && (
                            <> - {formatDateTime(event.end_date)}</>
                          )}
                        </span>
                        {event.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-4 w-4" />
                            {event.location}
                          </span>
                        )}
                      </div>

                      {event.description && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                          {event.description}
                        </p>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Users className="h-4 w-4 text-gray-400" />
                        <span>
                          {event.registered_count}
                          {event.max_participants && ` / ${event.max_participants}`}
                        </span>
                        {event.waitlist_count > 0 && (
                          <span className="text-yellow-600">
                            (+{event.waitlist_count} oczekuje)
                          </span>
                        )}
                      </div>

                      {event.cost && (
                        <div className="text-sm font-medium">
                          {formatCurrency(event.cost)} / osoba
                        </div>
                      )}

                      <div className="flex gap-2">
                        {event.is_registration_open && !event.is_full && (
                          <Button asChild size="sm">
                            <Link to={`/events/${event.id}/register`}>Zapisz się</Link>
                          </Button>
                        )}
                        <Button asChild variant="outline" size="sm">
                          <Link to={`/events/${event.id}`}>Szczegóły</Link>
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Past events link */}
      <div className="text-center">
        <Button asChild variant="link">
          <Link to="/events/archive">Zobacz przeszłe wydarzenia</Link>
        </Button>
      </div>
    </div>
  )
}
