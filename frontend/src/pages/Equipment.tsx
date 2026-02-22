import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Anchor, AlertTriangle, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useEquipment, useEquipmentStats, useMaintenanceDue } from '@/hooks/useEquipment'
import { formatDate, getStatusColor, getStatusLabel, cn } from '@/lib/utils'

export function EquipmentPage() {
  const [typeFilter, setTypeFilter] = useState<string>('')
  const { data: equipment, isLoading } = useEquipment({
    type: typeFilter || undefined,
  })
  const { data: stats } = useEquipmentStats()
  const { data: maintenanceDue } = useMaintenanceDue()

  const equipmentTypes = [
    { value: '', label: 'Wszystkie' },
    { value: 'kayak', label: 'Kajaki' },
    { value: 'sailboat', label: 'Żaglówki' },
    { value: 'sup', label: 'SUP' },
    { value: 'motorboat', label: 'Motorówki' },
    { value: 'other', label: 'Inne' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sprzęt wodny</h1>
          <p className="text-gray-500">Zarządzaj sprzętem i rezerwacjami</p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/equipment/reservations">
              <Calendar className="mr-2 h-4 w-4" />
              Rezerwacje
            </Link>
          </Button>
          <Button asChild>
            <Link to="/equipment/new">
              <Plus className="mr-2 h-4 w-4" />
              Dodaj sprzęt
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">Łącznie</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">jednostek sprzętu</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-green-600">Dostępne</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.by_status?.available || 0}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-blue-600">Zarezerwowane</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {stats.active_reservations || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                +{stats.upcoming_reservations || 0} nadchodzących
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-orange-600">W naprawie</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {stats.by_status?.maintenance || 0}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Maintenance alerts */}
      {maintenanceDue && maintenanceDue.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Sprzęt wymagający przeglądu
            </CardTitle>
            <CardDescription className="text-orange-700">
              {maintenanceDue.length} jednostek do przeglądu
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {maintenanceDue.map((item) => (
                <Link
                  key={item.id}
                  to={`/equipment/${item.id}`}
                  className="rounded-md bg-orange-100 px-3 py-1 text-sm text-orange-800 hover:bg-orange-200"
                >
                  {item.name} (do: {formatDate(item.next_maintenance!)})
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2 overflow-x-auto">
            {equipmentTypes.map((type) => (
              <Button
                key={type.value}
                variant={typeFilter === type.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTypeFilter(type.value)}
              >
                {type.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Equipment grid */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="text-gray-500">Ładowanie...</div>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {equipment?.map((item) => (
            <Card key={item.id} className="overflow-hidden">
              {item.photo_url && (
                <div className="aspect-video overflow-hidden bg-gray-100">
                  <img
                    src={item.photo_url}
                    alt={item.name}
                    className="h-full w-full object-cover"
                  />
                </div>
              )}
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">
                      <Link to={`/equipment/${item.id}`} className="hover:text-primary">
                        {item.name}
                      </Link>
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <Anchor className="h-3 w-3" />
                      {getStatusLabel(item.type)}
                      {item.inventory_number && (
                        <span className="font-mono text-xs">({item.inventory_number})</span>
                      )}
                    </CardDescription>
                  </div>
                  <Badge className={cn('font-normal', getStatusColor(item.status))}>
                    {getStatusLabel(item.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {item.description && (
                  <p className="mb-3 text-sm text-gray-600 line-clamp-2">{item.description}</p>
                )}
                <div className="flex items-center justify-between text-sm">
                  {item.needs_maintenance && (
                    <span className="flex items-center gap-1 text-orange-600">
                      <AlertTriangle className="h-4 w-4" />
                      Wymaga przeglądu
                    </span>
                  )}
                  {item.is_available && (
                    <Button asChild size="sm" variant="outline">
                      <Link to={`/equipment/reservations/new?equipment=${item.id}`}>
                        Zarezerwuj
                      </Link>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
