import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatCurrency(amount: number | string): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('pl-PL', {
    style: 'currency',
    currency: 'PLN',
  }).format(num)
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    // Member status
    active: 'bg-green-100 text-green-800',
    suspended: 'bg-yellow-100 text-yellow-800',
    former: 'bg-gray-100 text-gray-800',

    // Fee status
    pending: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-green-100 text-green-800',
    overdue: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',

    // Equipment status
    available: 'bg-green-100 text-green-800',
    reserved: 'bg-blue-100 text-blue-800',
    maintenance: 'bg-orange-100 text-orange-800',
    retired: 'bg-gray-100 text-gray-800',

    // Reservation status
    confirmed: 'bg-green-100 text-green-800',
    completed: 'bg-blue-100 text-blue-800',

    // Event status
    planned: 'bg-blue-100 text-blue-800',
    registration_open: 'bg-green-100 text-green-800',
    full: 'bg-purple-100 text-purple-800',
    ongoing: 'bg-yellow-100 text-yellow-800',

    // Participant status
    registered: 'bg-green-100 text-green-800',
    waitlist: 'bg-yellow-100 text-yellow-800',
  }

  return colors[status] || 'bg-gray-100 text-gray-800'
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    // Member status
    active: 'Aktywny',
    suspended: 'Zawieszony',
    former: 'Były członek',

    // Fee status
    pending: 'Oczekuje',
    paid: 'Opłacona',
    overdue: 'Zaległa',
    cancelled: 'Anulowana',

    // Equipment status
    available: 'Dostępny',
    reserved: 'Zarezerwowany',
    maintenance: 'W naprawie',
    retired: 'Wycofany',

    // Equipment type
    kayak: 'Kajak',
    sailboat: 'Żaglówka',
    sup: 'SUP',
    motorboat: 'Łódź motorowa',
    other: 'Inny',

    // Reservation status
    confirmed: 'Potwierdzona',
    completed: 'Zakończona',

    // Event status
    planned: 'Planowane',
    registration_open: 'Zapisy otwarte',
    full: 'Komplet',
    ongoing: 'W trakcie',

    // Event type
    cruise: 'Rejs',
    kayak_trip: 'Spływ kajakowy',
    training: 'Szkolenie',
    meeting: 'Spotkanie',

    // Participant status
    registered: 'Zapisany',
    waitlist: 'Lista oczekujących',
  }

  return labels[status] || status
}
