import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CreditCard, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useFees, useFeeStats, useMarkFeePaid } from '@/hooks/useFees'
import { formatDate, formatCurrency, getStatusColor, getStatusLabel, cn } from '@/lib/utils'

export function FeesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const status = searchParams.get('status') || ''
  const [page, setPage] = useState(1)
  const currentYear = new Date().getFullYear()

  const { data, isLoading } = useFees({
    status: status || undefined,
    year: currentYear,
    page,
    per_page: 20,
  })

  const { data: stats } = useFeeStats(currentYear)
  const markPaid = useMarkFeePaid()

  const setStatus = (newStatus: string) => {
    if (newStatus) {
      searchParams.set('status', newStatus)
    } else {
      searchParams.delete('status')
    }
    setSearchParams(searchParams)
    setPage(1)
  }

  const handleMarkPaid = async (feeId: number) => {
    if (confirm('Oznaczyć składkę jako opłaconą?')) {
      await markPaid.mutateAsync({ id: feeId })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Składki {currentYear}</h1>
          <p className="text-gray-500">Zarządzaj składkami członkowskimi</p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/fees/types">Typy składek</Link>
          </Button>
          <Button asChild>
            <Link to="/fees/generate">Wygeneruj składki</Link>
          </Button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-gray-500">
                <CreditCard className="h-4 w-4" />
                Łącznie
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats.total_amount)}</div>
              <p className="text-xs text-muted-foreground">{stats.total_count} składek</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-green-600">
                <CheckCircle className="h-4 w-4" />
                Opłacone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(stats.paid_amount)}
              </div>
              <p className="text-xs text-muted-foreground">{stats.paid_count} składek</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-yellow-600">
                <Clock className="h-4 w-4" />
                Oczekujące
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.pending_count}</div>
              <p className="text-xs text-muted-foreground">do zapłaty</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-red-600">
                <AlertCircle className="h-4 w-4" />
                Zaległe
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(stats.overdue_amount)}
              </div>
              <p className="text-xs text-muted-foreground">{stats.overdue_count} składek</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Collection rate */}
      {stats && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Wskaźnik ściągalności</span>
              <span className="text-lg font-bold">{stats.collection_rate}%</span>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
              <div
                className="h-2 rounded-full bg-green-500"
                style={{ width: `${stats.collection_rate}%` }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <Button
              variant={status === '' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatus('')}
            >
              Wszystkie
            </Button>
            <Button
              variant={status === 'pending' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatus('pending')}
            >
              Oczekujące
            </Button>
            <Button
              variant={status === 'paid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatus('paid')}
            >
              Opłacone
            </Button>
            <Button
              variant={status === 'overdue' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatus('overdue')}
            >
              Zaległe
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-gray-500">Ładowanie...</div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Członek</TableHead>
                    <TableHead>Typ składki</TableHead>
                    <TableHead>Kwota</TableHead>
                    <TableHead>Termin</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Data wpłaty</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((fee) => (
                    <TableRow key={fee.id}>
                      <TableCell>
                        <Link
                          to={`/members/${fee.member_id}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {fee.member?.full_name || `Członek #${fee.member_id}`}
                        </Link>
                      </TableCell>
                      <TableCell>{fee.fee_type?.name || '-'}</TableCell>
                      <TableCell className="font-medium">{formatCurrency(fee.amount)}</TableCell>
                      <TableCell>
                        {formatDate(fee.due_date)}
                        {fee.days_overdue > 0 && (
                          <span className="ml-2 text-xs text-red-500">
                            ({fee.days_overdue} dni)
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={cn('font-normal', getStatusColor(fee.status))}>
                          {getStatusLabel(fee.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>{fee.paid_date ? formatDate(fee.paid_date) : '-'}</TableCell>
                      <TableCell>
                        {(fee.status === 'pending' || fee.status === 'overdue') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleMarkPaid(fee.id)}
                            disabled={markPaid.isPending}
                          >
                            <CheckCircle className="mr-1 h-4 w-4" />
                            Opłacona
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {data && data.pages > 1 && (
                <div className="flex items-center justify-between border-t px-4 py-3">
                  <div className="text-sm text-gray-500">
                    Strona {data.page} z {data.pages} ({data.total} składek)
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Poprzednia
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                      disabled={page === data.pages}
                    >
                      Następna
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
