import { Routes, Route, Navigate } from 'react-router-dom'
import { ReactNode } from 'react'
import { Layout } from '@/components/Layout'
import { LoginPage } from '@/pages/Login'
import { DashboardPage } from '@/pages/Dashboard'
import { MembersPage } from '@/pages/Members'
import { FeesPage } from '@/pages/Fees'
import { FinancePage } from '@/pages/Finance'
import { EquipmentPage } from '@/pages/Equipment'
import { EventsPage } from '@/pages/Events'
import { ReportsPage } from '@/pages/Reports'
import { useAuth, useAuthProvider, AuthContext } from '@/hooks/useAuth'

function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuthProvider()

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const auth = useAuth()

  if (auth.isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-gray-500">Ładowanie...</div>
      </div>
    )
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <DashboardPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/members"
        element={
          <ProtectedRoute>
            <Layout>
              <MembersPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/fees"
        element={
          <ProtectedRoute>
            <Layout>
              <FeesPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/finance"
        element={
          <ProtectedRoute>
            <Layout>
              <FinancePage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/equipment"
        element={
          <ProtectedRoute>
            <Layout>
              <EquipmentPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/events"
        element={
          <ProtectedRoute>
            <Layout>
              <EventsPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <Layout>
              <ReportsPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to dashboard */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
