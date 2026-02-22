// User types
export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: 'admin' | 'treasurer' | 'board'
  is_active: boolean
  last_login: string | null
  created_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  user: User
}

// Member types
export type MemberStatus = 'active' | 'suspended' | 'former'

export interface Member {
  id: number
  member_number: string | null
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string | null
  address: string | null
  join_date: string
  status: MemberStatus
  notes: string | null
  data_consent: boolean
  consent_date: string | null
  total_debt: number
  created_at: string
  updated_at: string
}

export interface MemberCreate {
  member_number?: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  address?: string
  join_date?: string
  status?: MemberStatus
  notes?: string
  data_consent?: boolean
}

// Fee types
export type FeeStatus = 'pending' | 'paid' | 'overdue' | 'cancelled'
export type FeeFrequency = 'yearly' | 'monthly' | 'one_time'

export interface FeeType {
  id: number
  name: string
  amount: string
  frequency: FeeFrequency
  due_day: number | null
  due_month: number | null
  is_active: boolean
  description: string | null
  created_at: string
}

export interface Fee {
  id: number
  member_id: number
  member?: Pick<Member, 'id' | 'full_name' | 'email'>
  fee_type_id: number
  fee_type?: Pick<FeeType, 'id' | 'name'>
  amount: string
  due_date: string
  status: FeeStatus
  paid_date: string | null
  transaction_id: number | null
  notes: string | null
  is_overdue: boolean
  days_overdue: number
  created_at: string
}

export interface FeeCreate {
  member_id: number
  fee_type_id: number
  amount: string
  due_date: string
  status?: FeeStatus
  notes?: string
}

// Transaction types
export type TransactionType = 'income' | 'expense'
export type TransactionCategory =
  | 'fees'
  | 'donations'
  | 'grants'
  | 'other_income'
  | 'administration'
  | 'statutory_activities'
  | 'equipment'
  | 'events'
  | 'other_expense'

export interface Transaction {
  id: number
  date: string
  amount: string
  type: TransactionType
  category: TransactionCategory
  description: string
  counterparty: string | null
  bank_reference: string | null
  matched_member_id: number | null
  matched_member?: Pick<Member, 'id' | 'full_name'>
  match_confidence: 'auto' | 'manual' | null
  imported_at: string | null
  import_source: string | null
  created_at: string
}

export interface TransactionCreate {
  date: string
  amount: string
  type: TransactionType
  category: TransactionCategory
  description: string
  counterparty?: string
  bank_reference?: string
  matched_member_id?: number
}

// Equipment types
export type EquipmentType = 'kayak' | 'sailboat' | 'sup' | 'motorboat' | 'other'
export type EquipmentStatus = 'available' | 'reserved' | 'maintenance' | 'retired'
export type ReservationStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled'

export interface Equipment {
  id: number
  name: string
  type: EquipmentType
  status: EquipmentStatus
  description: string | null
  photo_url: string | null
  inventory_number: string | null
  purchase_date: string | null
  last_maintenance: string | null
  next_maintenance: string | null
  needs_maintenance: boolean
  is_available: boolean
  notes: string | null
  created_at: string
}

export interface EquipmentCreate {
  name: string
  type: EquipmentType
  status?: EquipmentStatus
  description?: string
  photo_url?: string
  inventory_number?: string
  purchase_date?: string
  last_maintenance?: string
  next_maintenance?: string
  notes?: string
}

export interface Reservation {
  id: number
  equipment_id: number
  equipment?: Pick<Equipment, 'id' | 'name' | 'type'>
  member_id: number
  member?: Pick<Member, 'id' | 'full_name' | 'phone'>
  start_date: string
  end_date: string
  status: ReservationStatus
  purpose: string | null
  notes: string | null
  is_active: boolean
  duration_days: number
  created_at: string
}

export interface ReservationCreate {
  equipment_id: number
  member_id: number
  start_date: string
  end_date: string
  status?: ReservationStatus
  purpose?: string
  notes?: string
}

// Event types
export type EventType = 'cruise' | 'kayak_trip' | 'training' | 'meeting' | 'other'
export type EventStatus =
  | 'planned'
  | 'registration_open'
  | 'full'
  | 'ongoing'
  | 'completed'
  | 'cancelled'
export type ParticipantStatus = 'registered' | 'waitlist' | 'confirmed' | 'cancelled'

export interface EventParticipant {
  id: number
  event_id: number
  member_id: number
  member?: Pick<Member, 'id' | 'full_name' | 'email' | 'phone'>
  status: ParticipantStatus
  registered_at: string
  notes: string | null
}

export interface Event {
  id: number
  name: string
  type: EventType
  description: string | null
  location: string | null
  start_date: string
  end_date: string
  registration_deadline: string | null
  max_participants: number | null
  status: EventStatus
  cost: string | null
  notes: string | null
  registered_count: number
  waitlist_count: number
  spots_available: number
  is_full: boolean
  is_registration_open: boolean
  created_at: string
  participants?: EventParticipant[]
}

export interface EventCreate {
  name: string
  type: EventType
  description?: string
  location?: string
  start_date: string
  end_date: string
  registration_deadline?: string
  max_participants?: number
  status?: EventStatus
  cost?: string
  notes?: string
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page?: number
}

// Dashboard
export interface DashboardData {
  members: {
    active: number
  }
  fees: {
    overdue_count: number
    overdue_amount: number
  }
  finance: {
    year: number
    income: number
    expense: number
    balance: number
  }
  upcoming_events: Array<{
    id: number
    name: string
    date: string
    registered: number
  }>
  maintenance_due: number
}

// Stats
export interface MemberStats {
  total: number
  active: number
  suspended: number
  former: number
  with_debt: number
}

export interface FeeStats {
  year: number
  total_count: number
  paid_count: number
  pending_count: number
  overdue_count: number
  total_amount: number
  paid_amount: number
  overdue_amount: number
  collection_rate: number
}
