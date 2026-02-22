import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, FileText, Users, CreditCard, Wallet, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { reportsApi } from '@/services/api'

const currentYear = new Date().getFullYear()

export function ReportsPage() {
  const [selectedYear, setSelectedYear] = useState(currentYear)

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i)

  const reports = [
    {
      id: 'fees',
      title: 'Raport składek',
      description: 'Lista wszystkich składek z podziałem na status (opłacone/zaległe)',
      icon: CreditCard,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      fetchFn: () => reportsApi.getFeesReport(selectedYear, 'csv'),
      filename: `skladki_${selectedYear}.csv`,
    },
    {
      id: 'overdue',
      title: 'Raport zaległości',
      description: 'Lista członków z zaległymi składkami',
      icon: CreditCard,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      fetchFn: () => reportsApi.getOverdueReport('csv'),
      filename: `zaleglosci_${new Date().toISOString().split('T')[0]}.csv`,
    },
    {
      id: 'members',
      title: 'Lista członków',
      description: 'Eksport listy aktywnych członków z danymi kontaktowymi',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      fetchFn: () => reportsApi.getMembersReport('active', 'csv'),
      filename: 'czlonkowie_aktywni.csv',
    },
    {
      id: 'finance',
      title: 'Ewidencja finansowa',
      description: 'Uproszczona ewidencja przychodów i kosztów (zgodna z ustawą o NGO)',
      icon: Wallet,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      fetchFn: () => reportsApi.getFinanceReport(selectedYear, 'csv'),
      filename: `ewidencja_${selectedYear}.csv`,
    },
    {
      id: 'events',
      title: 'Raport wydarzeń',
      description: 'Zestawienie wydarzeń z liczbą uczestników',
      icon: Calendar,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      fetchFn: () => reportsApi.getEventsReport(selectedYear, 'csv'),
      filename: `wydarzenia_${selectedYear}.csv`,
    },
  ]

  const downloadReport = async (report: (typeof reports)[0]) => {
    try {
      const response = await fetch(`/api/reports/${report.id}?year=${selectedYear}&format=csv`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) throw new Error('Błąd pobierania raportu')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = report.filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading report:', error)
      alert('Błąd pobierania raportu')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Raporty</h1>
          <p className="text-gray-500">Generuj i pobieraj raporty</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Rok:</span>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {reports.map((report) => (
          <Card key={report.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`rounded-lg p-2 ${report.bgColor}`}>
                  <report.icon className={`h-6 w-6 ${report.color}`} />
                </div>
                <div>
                  <CardTitle className="text-lg">{report.title}</CardTitle>
                </div>
              </div>
              <CardDescription>{report.description}</CardDescription>
            </CardHeader>
            <CardContent className="mt-auto">
              <Button
                onClick={() => downloadReport(report)}
                variant="outline"
                className="w-full"
              >
                <Download className="mr-2 h-4 w-4" />
                Pobierz CSV
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Help section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Informacje o raportach
          </CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <ul className="space-y-2 text-gray-600">
            <li>
              <strong>Raport składek</strong> - zawiera wszystkie składki naliczone w danym roku
              wraz ze statusem płatności
            </li>
            <li>
              <strong>Raport zaległości</strong> - aktualny stan zaległości (tylko nieopłacone
              składki po terminie)
            </li>
            <li>
              <strong>Lista członków</strong> - eksport do kontaktu lub sprawozdań
            </li>
            <li>
              <strong>Ewidencja finansowa</strong> - uproszczona ewidencja zgodna z wymogami dla
              organizacji o przychodach poniżej 150 000 zł
            </li>
            <li>
              <strong>Raport wydarzeń</strong> - zestawienie organizowanych wydarzeń z frekwencją
            </li>
          </ul>
          <p className="mt-4 text-sm text-gray-500">
            Wszystkie raporty są generowane w formacie CSV, który można otworzyć w programach
            takich jak Microsoft Excel, LibreOffice Calc lub Google Sheets.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
