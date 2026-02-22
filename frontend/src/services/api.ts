import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For refresh token cookies
})

// Token storage
let accessToken: string | null = null

export const setAccessToken = (token: string | null) => {
  accessToken = token
}

export const getAccessToken = () => accessToken

// Request interceptor - add auth header
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Skip refresh logic for auth endpoints (login, refresh, logout)
    const isAuthEndpoint = originalRequest.url?.includes('/auth/')

    // If 401 and not already retried and not an auth endpoint, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true

      try {
        const response = await api.post('/auth/refresh')
        const newToken = response.data.access_token
        setAccessToken(newToken)

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, clear token
        setAccessToken(null)
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })
    setAccessToken(response.data.access_token)
    return response.data
  },

  logout: async () => {
    await api.post('/auth/logout')
    setAccessToken(null)
  },

  refresh: async () => {
    const response = await api.post('/auth/refresh')
    setAccessToken(response.data.access_token)
    return response.data
  },

  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return response.data
  },
}

// Members API
export const membersApi = {
  getAll: async (params?: {
    status?: string
    search?: string
    page?: number
    per_page?: number
  }) => {
    const response = await api.get('/members', { params })
    return response.data
  },

  getById: async (id: number) => {
    const response = await api.get(`/members/${id}`)
    return response.data
  },

  create: async <T extends object>(data: T) => {
    const response = await api.post('/members', data)
    return response.data
  },

  update: async <T extends object>(id: number, data: T) => {
    const response = await api.put(`/members/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    const response = await api.delete(`/members/${id}`)
    return response.data
  },

  getFees: async (id: number) => {
    const response = await api.get(`/members/${id}/fees`)
    return response.data
  },

  getStats: async () => {
    const response = await api.get('/members/stats')
    return response.data
  },
}

// Fees API
export const feesApi = {
  getAll: async (params?: {
    status?: string
    member_id?: number
    year?: number
    page?: number
    per_page?: number
  }) => {
    const response = await api.get('/fees', { params })
    return response.data
  },

  getOverdue: async () => {
    const response = await api.get('/fees/overdue')
    return response.data
  },

  create: async (data: object) => {
    const response = await api.post('/fees', data)
    return response.data
  },

  update: async (id: number, data: object) => {
    const response = await api.put(`/fees/${id}`, data)
    return response.data
  },

  markPaid: async (id: number, data?: { paid_date?: string; transaction_id?: number }) => {
    const response = await api.post(`/fees/${id}/mark-paid`, data || {})
    return response.data
  },

  generate: async (feeTypeId: number, dueDate: string) => {
    const response = await api.post('/fees/generate', {
      fee_type_id: feeTypeId,
      due_date: dueDate,
    })
    return response.data
  },

  getTypes: async (activeOnly = true) => {
    const response = await api.get('/fees/types', { params: { active: activeOnly } })
    return response.data
  },

  createType: async (data: object) => {
    const response = await api.post('/fees/types', data)
    return response.data
  },

  getStats: async (year?: number) => {
    const response = await api.get('/fees/stats', { params: { year } })
    return response.data
  },
}

// Finance API
export const financeApi = {
  getTransactions: async (params?: {
    type?: string
    category?: string
    start_date?: string
    end_date?: string
    unmatched?: boolean
    page?: number
    per_page?: number
  }) => {
    const response = await api.get('/finance/transactions', { params })
    return response.data
  },

  createTransaction: async (data: object) => {
    const response = await api.post('/finance/transactions', data)
    return response.data
  },

  updateTransaction: async (id: number, data: object) => {
    const response = await api.put(`/finance/transactions/${id}`, data)
    return response.data
  },

  matchTransaction: async (id: number, memberId: number, feeId?: number) => {
    const response = await api.post(`/finance/transactions/${id}/match`, {
      member_id: memberId,
      fee_id: feeId,
    })
    return response.data
  },

  unmatchTransaction: async (id: number) => {
    const response = await api.post(`/finance/transactions/${id}/unmatch`)
    return response.data
  },

  importFile: async (file: File, fileType?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (fileType) {
      formData.append('type', fileType)
    }
    const response = await api.post('/finance/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  confirmImport: async (transactions: object[]) => {
    const response = await api.post('/finance/import/confirm', { transactions })
    return response.data
  },

  getBalance: async () => {
    const response = await api.get('/finance/balance')
    return response.data
  },

  getStats: async (year?: number) => {
    const response = await api.get('/finance/stats', { params: { year } })
    return response.data
  },
}

// Equipment API
export const equipmentApi = {
  getAll: async (params?: { type?: string; status?: string; available?: boolean }) => {
    const response = await api.get('/equipment', { params })
    return response.data
  },

  getById: async (id: number) => {
    const response = await api.get(`/equipment/${id}`)
    return response.data
  },

  create: async (data: object) => {
    const response = await api.post('/equipment', data)
    return response.data
  },

  update: async (id: number, data: object) => {
    const response = await api.put(`/equipment/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    const response = await api.delete(`/equipment/${id}`)
    return response.data
  },

  getReservations: async (id: number, startFrom?: string) => {
    const response = await api.get(`/equipment/${id}/reservations`, {
      params: { start_from: startFrom },
    })
    return response.data
  },

  getMaintenanceDue: async () => {
    const response = await api.get('/equipment/maintenance-due')
    return response.data
  },

  getStats: async () => {
    const response = await api.get('/equipment/stats')
    return response.data
  },

  // Reservations
  getAllReservations: async (params?: {
    equipment_id?: number
    member_id?: number
    status?: string
    start_date?: string
    end_date?: string
  }) => {
    const response = await api.get('/equipment/reservations', { params })
    return response.data
  },

  createReservation: async (data: object) => {
    const response = await api.post('/equipment/reservations', data)
    return response.data
  },

  updateReservation: async (id: number, data: object) => {
    const response = await api.put(`/equipment/reservations/${id}`, data)
    return response.data
  },

  confirmReservation: async (id: number) => {
    const response = await api.post(`/equipment/reservations/${id}/confirm`)
    return response.data
  },

  cancelReservation: async (id: number) => {
    const response = await api.post(`/equipment/reservations/${id}/cancel`)
    return response.data
  },

  completeReservation: async (id: number) => {
    const response = await api.post(`/equipment/reservations/${id}/complete`)
    return response.data
  },
}

// Events API
export const eventsApi = {
  getAll: async (params?: {
    type?: string
    status?: string
    upcoming?: boolean
    page?: number
    per_page?: number
  }) => {
    const response = await api.get('/events', { params })
    return response.data
  },

  getById: async (id: number) => {
    const response = await api.get(`/events/${id}`)
    return response.data
  },

  create: async (data: object) => {
    const response = await api.post('/events', data)
    return response.data
  },

  update: async (id: number, data: object) => {
    const response = await api.put(`/events/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    const response = await api.delete(`/events/${id}`)
    return response.data
  },

  getParticipants: async (eventId: number, status?: string) => {
    const response = await api.get(`/events/${eventId}/participants`, { params: { status } })
    return response.data
  },

  registerParticipant: async (eventId: number, memberId: number, notes?: string) => {
    const response = await api.post(`/events/${eventId}/participants`, {
      member_id: memberId,
      notes,
    })
    return response.data
  },

  updateParticipant: async (
    eventId: number,
    participantId: number,
    data: object
  ) => {
    const response = await api.put(`/events/${eventId}/participants/${participantId}`, data)
    return response.data
  },

  cancelParticipation: async (eventId: number, participantId: number) => {
    const response = await api.delete(`/events/${eventId}/participants/${participantId}`)
    return response.data
  },

  openRegistration: async (id: number) => {
    const response = await api.post(`/events/${id}/open-registration`)
    return response.data
  },

  closeRegistration: async (id: number) => {
    const response = await api.post(`/events/${id}/close-registration`)
    return response.data
  },

  getStats: async (year?: number) => {
    const response = await api.get('/events/stats', { params: { year } })
    return response.data
  },
}

// Reports API
export const reportsApi = {
  getDashboard: async () => {
    const response = await api.get('/reports/dashboard')
    return response.data
  },

  getFeesReport: async (year?: number, format?: 'json' | 'csv') => {
    const response = await api.get('/reports/fees', { params: { year, format } })
    return response.data
  },

  getOverdueReport: async (format?: 'json' | 'csv') => {
    const response = await api.get('/reports/overdue', { params: { format } })
    return response.data
  },

  getMembersReport: async (status?: string, format?: 'json' | 'csv') => {
    const response = await api.get('/reports/members', { params: { status, format } })
    return response.data
  },

  getFinanceReport: async (year?: number, format?: 'json' | 'csv') => {
    const response = await api.get('/reports/finance', { params: { year, format } })
    return response.data
  },

  getEventsReport: async (year?: number, format?: 'json' | 'csv') => {
    const response = await api.get('/reports/events', { params: { year, format } })
    return response.data
  },
}

export default api
