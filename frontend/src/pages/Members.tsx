import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, UserCheck, UserX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
import { useMembers, useMemberStats } from '@/hooks/useMembers'
import { formatDate, formatCurrency, getStatusColor, getStatusLabel, cn } from '@/lib/utils'

export function MembersPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string>('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useMembers({
    search: search || undefined,
    status: status || undefined,
    page,
    per_page: 20,
  })

  const { data: stats } = useMemberStats()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Członkowie</h1>
          <p className="text-gray-500">Zarządzaj członkami stowarzyszenia</p>
        </div>
        <Button asChild>
          <Link to="/members/new">
            <Plus className="mr-2 h-4 w-4" />
            Dodaj członka
          </Link>
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">Wszyscy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-green-600">
                <UserCheck className="h-4 w-4" />
                Aktywni
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-yellow-600">
                <UserX className="h-4 w-4" />
                Zawieszeni
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.suspended}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-red-600">Z zaległościami</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.with_debt}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Szukaj po nazwisku, emailu lub numerze..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={status === '' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatus('')}
              >
                Wszyscy
              </Button>
              <Button
                variant={status === 'active' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatus('active')}
              >
                Aktywni
              </Button>
              <Button
                variant={status === 'suspended' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatus('suspended')}
              >
                Zawieszeni
              </Button>
              <Button
                variant={status === 'former' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatus('former')}
              >
                Byli
              </Button>
            </div>
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
                    <TableHead>Nr</TableHead>
                    <TableHead>Imię i nazwisko</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Telefon</TableHead>
                    <TableHead>Data przystąpienia</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Zaległości</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((member) => (
                    <TableRow key={member.id}>
                      <TableCell className="font-mono text-sm">
                        {member.member_number || '-'}
                      </TableCell>
                      <TableCell>
                        <Link
                          to={`/members/${member.id}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {member.full_name}
                        </Link>
                      </TableCell>
                      <TableCell>{member.email}</TableCell>
                      <TableCell>{member.phone || '-'}</TableCell>
                      <TableCell>{formatDate(member.join_date)}</TableCell>
                      <TableCell>
                        <Badge className={cn('font-normal', getStatusColor(member.status))}>
                          {getStatusLabel(member.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {member.total_debt > 0 ? (
                          <span className="font-medium text-red-600">
                            {formatCurrency(member.total_debt)}
                          </span>
                        ) : (
                          <span className="text-green-600">-</span>
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
                    Strona {data.page} z {data.pages} ({data.total} członków)
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
