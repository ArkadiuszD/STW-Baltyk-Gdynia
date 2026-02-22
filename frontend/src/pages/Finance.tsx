import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Upload, TrendingUp, TrendingDown, Wallet, ArrowUpRight, ArrowDownRight } from 'lucide-react'
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
import { financeApi } from '@/services/api'
import { formatDate, formatCurrency, cn } from '@/lib/utils'
import { Transaction, PaginatedResponse } from '@/types'

export function FinancePage() {
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  const { data: balance } = useQuery({
    queryKey: ['finance', 'balance'],
    queryFn: () => financeApi.getBalance(),
  })

  const { data: transactions, isLoading } = useQuery<PaginatedResponse<Transaction>>({
    queryKey: ['transactions', { type: typeFilter, page }],
    queryFn: () =>
      financeApi.getTransactions({
        type: typeFilter || undefined,
        page,
        per_page: 20,
      }),
  })

  const { data: unmatchedCount } = useQuery({
    queryKey: ['transactions', 'unmatched', 'count'],
    queryFn: async () => {
      const result = await financeApi.getTransactions({ unmatched: true, per_page: 1 })
      return result.total
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Finanse</h1>
          <p className="text-gray-500">Ewidencja przychodów i kosztów</p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/finance/transaction/new">Dodaj transakcję</Link>
          </Button>
          <Button asChild>
            <Link to="/finance/import">
              <Upload className="mr-2 h-4 w-4" />
              Import wyciągu
            </Link>
          </Button>
        </div>
      </div>

      {/* Balance cards */}
      {balance && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-gray-500">
                <Wallet className="h-4 w-4" />
                Saldo
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                className={cn(
                  'text-2xl font-bold',
                  balance.balance >= 0 ? 'text-green-600' : 'text-red-600'
                )}
              >
                {formatCurrency(balance.balance)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-green-600">
                <TrendingUp className="h-4 w-4" />
                Przychody {balance.year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(balance.year_income)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-red-600">
                <TrendingDown className="h-4 w-4" />
                Koszty {balance.year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(balance.year_expense)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Bilans {balance.year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                className={cn(
                  'text-2xl font-bold',
                  balance.year_balance >= 0 ? 'text-green-600' : 'text-red-600'
                )}
              >
                {formatCurrency(balance.year_balance)}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Unmatched transactions alert */}
      {unmatchedCount !== undefined && unmatchedCount > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-2">
              <Badge className="bg-yellow-500">{unmatchedCount}</Badge>
              <span className="text-sm font-medium text-yellow-800">
                transakcji do sparowania z członkami
              </span>
            </div>
            <Button asChild size="sm" variant="outline">
              <Link to="/finance/matching">Paruj transakcje</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <Button
              variant={typeFilter === '' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTypeFilter('')}
            >
              Wszystkie
            </Button>
            <Button
              variant={typeFilter === 'income' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTypeFilter('income')}
            >
              <ArrowUpRight className="mr-1 h-4 w-4 text-green-500" />
              Przychody
            </Button>
            <Button
              variant={typeFilter === 'expense' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTypeFilter('expense')}
            >
              <ArrowDownRight className="mr-1 h-4 w-4 text-red-500" />
              Koszty
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Transactions table */}
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
                    <TableHead>Data</TableHead>
                    <TableHead>Opis</TableHead>
                    <TableHead>Kontrahent</TableHead>
                    <TableHead>Kategoria</TableHead>
                    <TableHead>Członek</TableHead>
                    <TableHead className="text-right">Kwota</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions?.items.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell>{formatDate(tx.date)}</TableCell>
                      <TableCell className="max-w-xs truncate">{tx.description}</TableCell>
                      <TableCell>{tx.counterparty || '-'}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{tx.category}</Badge>
                      </TableCell>
                      <TableCell>
                        {tx.matched_member ? (
                          <Link
                            to={`/members/${tx.matched_member.id}`}
                            className="text-primary hover:underline"
                          >
                            {tx.matched_member.full_name}
                          </Link>
                        ) : tx.type === 'income' ? (
                          <span className="text-yellow-600">do sparowania</span>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            'font-medium',
                            tx.type === 'income' ? 'text-green-600' : 'text-red-600'
                          )}
                        >
                          {tx.type === 'income' ? '+' : '-'}
                          {formatCurrency(tx.amount)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {transactions && transactions.pages > 1 && (
                <div className="flex items-center justify-between border-t px-4 py-3">
                  <div className="text-sm text-gray-500">
                    Strona {transactions.page} z {transactions.pages} ({transactions.total}{' '}
                    transakcji)
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
                      onClick={() => setPage((p) => Math.min(transactions.pages, p + 1))}
                      disabled={page === transactions.pages}
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
