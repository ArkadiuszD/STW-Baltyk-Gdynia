import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users, CreditCard, Wallet, Calendar, Anchor, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { reportsApi } from '@/services/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { DashboardData } from '@/types'

export function DashboardPage() {
  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => reportsApi.getDashboard(),
  })

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-gray-500">Ładowanie...</div>
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Przegląd stanu stowarzyszenia</p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Aktywni członkowie</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.members.active}</div>
            <Link to="/members" className="text-xs text-primary hover:underline">
              Zobacz wszystkich
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Zaległe składki</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {data.fees.overdue_count}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(data.fees.overdue_amount)} zaległości
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Saldo {data.finance.year}</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                data.finance.balance >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {formatCurrency(data.finance.balance)}
            </div>
            <p className="text-xs text-muted-foreground">
              +{formatCurrency(data.finance.income)} / -{formatCurrency(data.finance.expense)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Sprzęt do przeglądu</CardTitle>
            <Anchor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                data.maintenance_due > 0 ? 'text-orange-600' : 'text-green-600'
              }`}
            >
              {data.maintenance_due}
            </div>
            <Link to="/equipment" className="text-xs text-primary hover:underline">
              Zarządzaj sprzętem
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming events & Alerts */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Nadchodzące wydarzenia
            </CardTitle>
            <CardDescription>Najbliższe 30 dni</CardDescription>
          </CardHeader>
          <CardContent>
            {data.upcoming_events.length === 0 ? (
              <p className="text-sm text-muted-foreground">Brak zaplanowanych wydarzeń</p>
            ) : (
              <div className="space-y-3">
                {data.upcoming_events.map((event) => (
                  <Link
                    key={event.id}
                    to={`/events/${event.id}`}
                    className="flex items-center justify-between rounded-md border p-3 hover:bg-gray-50"
                  >
                    <div>
                      <p className="font-medium">{event.name}</p>
                      <p className="text-sm text-muted-foreground">{formatDate(event.date)}</p>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {event.registered} zapisanych
                    </div>
                  </Link>
                ))}
              </div>
            )}
            <Button asChild variant="outline" className="mt-4 w-full">
              <Link to="/events">Wszystkie wydarzenia</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Wymagające uwagi
            </CardTitle>
            <CardDescription>Pilne sprawy do załatwienia</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.fees.overdue_count > 0 && (
                <Link
                  to="/fees?status=overdue"
                  className="flex items-center justify-between rounded-md border border-red-200 bg-red-50 p-3 hover:bg-red-100"
                >
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-red-600" />
                    <span className="text-sm font-medium text-red-800">Zaległe składki</span>
                  </div>
                  <span className="text-sm font-bold text-red-600">
                    {data.fees.overdue_count}
                  </span>
                </Link>
              )}

              {data.maintenance_due > 0 && (
                <Link
                  to="/equipment?maintenance=true"
                  className="flex items-center justify-between rounded-md border border-orange-200 bg-orange-50 p-3 hover:bg-orange-100"
                >
                  <div className="flex items-center gap-2">
                    <Anchor className="h-4 w-4 text-orange-600" />
                    <span className="text-sm font-medium text-orange-800">
                      Sprzęt do przeglądu
                    </span>
                  </div>
                  <span className="text-sm font-bold text-orange-600">
                    {data.maintenance_due}
                  </span>
                </Link>
              )}

              {data.fees.overdue_count === 0 && data.maintenance_due === 0 && (
                <p className="text-center text-sm text-green-600">
                  Wszystko w porządku!
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <Card>
        <CardHeader>
          <CardTitle>Szybkie akcje</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button asChild>
              <Link to="/members/new">Dodaj członka</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/finance/import">Import wyciągu</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/equipment/reservations/new">Nowa rezerwacja</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/events/new">Nowe wydarzenie</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
