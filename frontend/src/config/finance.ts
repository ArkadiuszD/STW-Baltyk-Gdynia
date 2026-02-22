/**
 * Konfiguracja modułu finansowego STW Bałtyk Gdynia - Frontend
 */

// =============================================================================
// FORMATOWANIE WALUTOWE
// =============================================================================

export const CURRENCY = {
  code: 'PLN',
  symbol: 'zł',
  locale: 'pl-PL',
};

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat(CURRENCY.locale, {
    style: 'currency',
    currency: CURRENCY.code,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatNumber(amount: number, decimals: number = 2): string {
  return new Intl.NumberFormat(CURRENCY.locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount);
}

// =============================================================================
// FORMATOWANIE DAT
// =============================================================================

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// =============================================================================
// POLSKIE MIESIĄCE
// =============================================================================

export const MONTHS_PL: Record<number, string> = {
  1: 'Styczeń',
  2: 'Luty',
  3: 'Marzec',
  4: 'Kwiecień',
  5: 'Maj',
  6: 'Czerwiec',
  7: 'Lipiec',
  8: 'Sierpień',
  9: 'Wrzesień',
  10: 'Październik',
  11: 'Listopad',
  12: 'Grudzień',
};

export const MONTHS_PL_GENITIVE: Record<number, string> = {
  1: 'stycznia',
  2: 'lutego',
  3: 'marca',
  4: 'kwietnia',
  5: 'maja',
  6: 'czerwca',
  7: 'lipca',
  8: 'sierpnia',
  9: 'września',
  10: 'października',
  11: 'listopada',
  12: 'grudnia',
};

export function getMonthName(month: number): string {
  return MONTHS_PL[month] || '';
}

export function getMonthGenitive(month: number): string {
  return MONTHS_PL_GENITIVE[month] || '';
}

// =============================================================================
// STATUSY SKŁADEK
// =============================================================================

export type FeeStatus = 'pending' | 'paid' | 'overdue' | 'cancelled';

export const FEE_STATUS_LABELS: Record<FeeStatus, string> = {
  pending: 'Oczekująca',
  paid: 'Opłacona',
  overdue: 'Zaległa',
  cancelled: 'Anulowana',
};

export const FEE_STATUS_COLORS: Record<FeeStatus, string> = {
  pending: 'yellow',
  paid: 'green',
  overdue: 'red',
  cancelled: 'gray',
};

export const FEE_STATUS_BADGE_VARIANTS: Record<FeeStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  paid: 'default',
  overdue: 'destructive',
  cancelled: 'outline',
};

// =============================================================================
// STATUSY CZŁONKÓW
// =============================================================================

export type MemberStatus = 'active' | 'suspended' | 'former';

export const MEMBER_STATUS_LABELS: Record<MemberStatus, string> = {
  active: 'Aktywny',
  suspended: 'Zawieszony',
  former: 'Były członek',
};

export const MEMBER_STATUS_COLORS: Record<MemberStatus, string> = {
  active: 'green',
  suspended: 'yellow',
  former: 'gray',
};

// =============================================================================
// TYPY TRANSAKCJI
// =============================================================================

export type TransactionType = 'income' | 'expense';

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  income: 'Przychód',
  expense: 'Wydatek',
};

export const TRANSACTION_TYPE_COLORS: Record<TransactionType, string> = {
  income: 'green',
  expense: 'red',
};

// =============================================================================
// KATEGORIE TRANSAKCJI
// =============================================================================

export interface TransactionCategoryInfo {
  name: string;
  description: string;
  icon: string;
}

export const INCOME_CATEGORIES: Record<string, TransactionCategoryInfo> = {
  fees: {
    name: 'Składki członkowskie',
    description: 'Wpłaty składek rocznych, miesięcznych, wpisowe',
    icon: 'CreditCard',
  },
  donations: {
    name: 'Darowizny',
    description: 'Darowizny od osób fizycznych i prawnych',
    icon: 'Heart',
  },
  grants: {
    name: 'Dotacje',
    description: 'Dotacje z urzędu miasta, programów, sponsoring',
    icon: 'FileText',
  },
  events_income: {
    name: 'Przychody z wydarzeń',
    description: 'Opłaty za uczestnictwo w rejsach, spływach',
    icon: 'Calendar',
  },
  equipment_rental: {
    name: 'Wynajem sprzętu',
    description: 'Opłaty za wynajem kajaków, SUP, żaglówek',
    icon: 'Anchor',
  },
  other_income: {
    name: 'Inne przychody',
    description: 'Pozostałe przychody niepasujące do kategorii',
    icon: 'Plus',
  },
};

export const EXPENSE_CATEGORIES: Record<string, TransactionCategoryInfo> = {
  administration: {
    name: 'Administracja',
    description: 'Opłaty bankowe, ubezpieczenia, biuro',
    icon: 'Building',
  },
  statutory_activities: {
    name: 'Działalność statutowa',
    description: 'Bezpośrednie koszty działalności stowarzyszenia',
    icon: 'Flag',
  },
  equipment_purchase: {
    name: 'Zakup sprzętu',
    description: 'Zakup kajaków, SUP, żaglówek, akcesoriów',
    icon: 'ShoppingCart',
  },
  equipment_maintenance: {
    name: 'Konserwacja sprzętu',
    description: 'Naprawy, przeglądy, części zamienne',
    icon: 'Wrench',
  },
  events_expense: {
    name: 'Organizacja wydarzeń',
    description: 'Koszty rejsów, spływów, szkoleń',
    icon: 'Calendar',
  },
  training: {
    name: 'Szkolenia',
    description: 'Kursy instruktorskie, patenty, certyfikaty',
    icon: 'GraduationCap',
  },
  rent: {
    name: 'Czynsz i media',
    description: 'Wynajem przystani, magazynu, media',
    icon: 'Home',
  },
  other_expense: {
    name: 'Inne wydatki',
    description: 'Pozostałe wydatki niepasujące do kategorii',
    icon: 'Minus',
  },
};

export function getCategoryInfo(type: TransactionType, category: string): TransactionCategoryInfo | undefined {
  if (type === 'income') {
    return INCOME_CATEGORIES[category];
  }
  return EXPENSE_CATEGORIES[category];
}

export function getCategoryName(type: TransactionType, category: string): string {
  const info = getCategoryInfo(type, category);
  return info?.name || category;
}

// =============================================================================
// STATUSY SPRZĘTU
// =============================================================================

export type EquipmentStatus = 'available' | 'reserved' | 'maintenance' | 'retired';

export const EQUIPMENT_STATUS_LABELS: Record<EquipmentStatus, string> = {
  available: 'Dostępny',
  reserved: 'Zarezerwowany',
  maintenance: 'W naprawie',
  retired: 'Wycofany',
};

export const EQUIPMENT_STATUS_COLORS: Record<EquipmentStatus, string> = {
  available: 'green',
  reserved: 'blue',
  maintenance: 'yellow',
  retired: 'gray',
};

// =============================================================================
// STATUSY WYDARZEŃ
// =============================================================================

export type EventStatus = 'planned' | 'registration_open' | 'full' | 'ongoing' | 'completed' | 'cancelled';

export const EVENT_STATUS_LABELS: Record<EventStatus, string> = {
  planned: 'Planowany',
  registration_open: 'Zapisy otwarte',
  full: 'Brak miejsc',
  ongoing: 'W trakcie',
  completed: 'Zakończony',
  cancelled: 'Odwołany',
};

export const EVENT_STATUS_COLORS: Record<EventStatus, string> = {
  planned: 'gray',
  registration_open: 'green',
  full: 'yellow',
  ongoing: 'blue',
  completed: 'gray',
  cancelled: 'red',
};

// =============================================================================
// TYPY SPRZĘTU
// =============================================================================

export type EquipmentType = 'kayak' | 'sailboat' | 'sup' | 'motorboat' | 'other';

export const EQUIPMENT_TYPE_LABELS: Record<EquipmentType, string> = {
  kayak: 'Kajak',
  sailboat: 'Żaglówka',
  sup: 'SUP',
  motorboat: 'Łódź motorowa',
  other: 'Inny',
};

export const EQUIPMENT_TYPE_ICONS: Record<EquipmentType, string> = {
  kayak: 'Waves',
  sailboat: 'Sailboat',
  sup: 'User',
  motorboat: 'Ship',
  other: 'HelpCircle',
};

// =============================================================================
// TYPY WYDARZEŃ
// =============================================================================

export type EventType = 'cruise' | 'kayak_trip' | 'training' | 'meeting' | 'other';

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  cruise: 'Rejs',
  kayak_trip: 'Spływ kajakowy',
  training: 'Szkolenie',
  meeting: 'Spotkanie',
  other: 'Inne',
};

// =============================================================================
// DOMYŚLNE SKŁADKI (cache z API)
// =============================================================================

export interface DefaultFeeConfig {
  name: string;
  amount: number;
  frequency: 'yearly' | 'monthly' | 'one_time';
  due_month?: number;
  due_day?: number;
}

export const DEFAULT_FEES: Record<string, DefaultFeeConfig> = {
  annual: {
    name: 'Składka roczna',
    amount: 120.00,
    frequency: 'yearly',
    due_month: 1,
    due_day: 31,
  },
  entry: {
    name: 'Wpisowe',
    amount: 50.00,
    frequency: 'one_time',
  },
  monthly: {
    name: 'Składka miesięczna',
    amount: 15.00,
    frequency: 'monthly',
    due_day: 10,
  },
  junior: {
    name: 'Składka młodzieżowa (do 18 lat)',
    amount: 60.00,
    frequency: 'yearly',
    due_month: 1,
    due_day: 31,
  },
  family: {
    name: 'Składka rodzinna (dodatkowa osoba)',
    amount: 80.00,
    frequency: 'yearly',
    due_month: 1,
    due_day: 31,
  },
};

// =============================================================================
// ALERTY I PRZYPOMNIENIA
// =============================================================================

export const ALERT_THRESHOLDS = {
  feeReminderDaysBefore: 7,
  feeFirstWarningDays: 14,
  feeSecondWarningDays: 30,
  feeSuspensionDays: 60,
  lowBalanceWarning: 500,
  highOverdueWarning: 1000,
  maxOverdueCount: 10,
};

// =============================================================================
// EXPORT GŁÓWNY
// =============================================================================

export const FINANCE_CONFIG = {
  currency: CURRENCY,
  formatCurrency,
  formatNumber,
  formatDate,
  formatDateTime,
  months: MONTHS_PL,
  monthsGenitive: MONTHS_PL_GENITIVE,
  getMonthName,
  getMonthGenitive,
  feeStatusLabels: FEE_STATUS_LABELS,
  feeStatusColors: FEE_STATUS_COLORS,
  memberStatusLabels: MEMBER_STATUS_LABELS,
  transactionTypeLabels: TRANSACTION_TYPE_LABELS,
  incomeCategories: INCOME_CATEGORIES,
  expenseCategories: EXPENSE_CATEGORIES,
  equipmentStatusLabels: EQUIPMENT_STATUS_LABELS,
  equipmentTypeLabels: EQUIPMENT_TYPE_LABELS,
  eventStatusLabels: EVENT_STATUS_LABELS,
  eventTypeLabels: EVENT_TYPE_LABELS,
  defaultFees: DEFAULT_FEES,
  alertThresholds: ALERT_THRESHOLDS,
};

export default FINANCE_CONFIG;
