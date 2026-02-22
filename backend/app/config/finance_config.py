"""
Konfiguracja modułu finansowego STW Bałtyk Gdynia.
Wszystkie parametry księgowe w jednym miejscu.
"""
from decimal import Decimal
from datetime import date
from typing import Dict, Any

# =============================================================================
# DANE STOWARZYSZENIA
# =============================================================================
ORGANIZATION: Dict[str, str] = {
    'name': 'Stowarzyszenie Turystyki Wodnej "Bałtyk Gdynia"',
    'short_name': 'STW Bałtyk Gdynia',
    'nip': '',  # Do uzupełnienia
    'regon': '',
    'krs': '',
    'address': 'ul. Przebendowskich, 81-506 Gdynia',
    'email': 'kontakt@stwbaltyk.pl',
    'phone': '',
}

# =============================================================================
# KONTO BANKOWE (Santander)
# =============================================================================
BANK: Dict[str, Any] = {
    'name': 'Santander Bank Polska',
    'account_number': '',  # IBAN do uzupełnienia
    'swift': 'WBKPPLPP',
    'import_formats': ['mt940', 'csv'],
    'default_encoding': 'windows-1250',
}

# =============================================================================
# ROK OBRACHUNKOWY
# =============================================================================
FISCAL_YEAR: Dict[str, int] = {
    'start_month': 1,  # Styczeń
    'start_day': 1,
    'end_month': 12,
    'end_day': 31,
}


def get_current_fiscal_year() -> int:
    """Zwraca bieżący rok obrachunkowy."""
    today = date.today()
    if today.month < FISCAL_YEAR['start_month']:
        return today.year - 1
    return today.year


# =============================================================================
# DOMYŚLNE SKŁADKI
# =============================================================================
DEFAULT_FEES: Dict[str, Dict[str, Any]] = {
    'annual': {
        'name': 'Składka roczna',
        'amount': Decimal('120.00'),
        'frequency': 'yearly',
        'due_month': 1,  # Styczeń
        'due_day': 31,
    },
    'entry': {
        'name': 'Wpisowe',
        'amount': Decimal('50.00'),
        'frequency': 'one_time',
    },
    'monthly': {
        'name': 'Składka miesięczna',
        'amount': Decimal('15.00'),
        'frequency': 'monthly',
        'due_day': 10,  # 10. dzień miesiąca
    },
    'junior': {
        'name': 'Składka młodzieżowa (do 18 lat)',
        'amount': Decimal('60.00'),
        'frequency': 'yearly',
        'due_month': 1,
        'due_day': 31,
    },
    'family': {
        'name': 'Składka rodzinna (dodatkowa osoba)',
        'amount': Decimal('80.00'),
        'frequency': 'yearly',
        'due_month': 1,
        'due_day': 31,
    },
}

# =============================================================================
# KATEGORIE TRANSAKCJI (z polskimi nazwami)
# =============================================================================
TRANSACTION_CATEGORIES: Dict[str, Dict[str, Dict[str, str]]] = {
    # Przychody
    'income': {
        'fees': {
            'name': 'Składki członkowskie',
            'description': 'Wpłaty składek rocznych, miesięcznych, wpisowe',
        },
        'donations': {
            'name': 'Darowizny',
            'description': 'Darowizny od osób fizycznych i prawnych',
        },
        'grants': {
            'name': 'Dotacje',
            'description': 'Dotacje z urzędu miasta, programów, sponsoring',
        },
        'events': {
            'name': 'Przychody z wydarzeń',
            'description': 'Opłaty za uczestnictwo w rejsach, spływach',
        },
        'equipment_rental': {
            'name': 'Wynajem sprzętu',
            'description': 'Opłaty za wynajem kajaków, SUP, żaglówek',
        },
        'other_income': {
            'name': 'Inne przychody',
            'description': 'Pozostałe przychody niepasujące do kategorii',
        },
    },
    # Wydatki
    'expense': {
        'administration': {
            'name': 'Administracja',
            'description': 'Opłaty bankowe, ubezpieczenia, biuro',
        },
        'statutory_activities': {
            'name': 'Działalność statutowa',
            'description': 'Bezpośrednie koszty działalności stowarzyszenia',
        },
        'equipment_purchase': {
            'name': 'Zakup sprzętu',
            'description': 'Zakup kajaków, SUP, żaglówek, akcesoriów',
        },
        'equipment_maintenance': {
            'name': 'Konserwacja sprzętu',
            'description': 'Naprawy, przeglądy, części zamienne',
        },
        'events': {
            'name': 'Organizacja wydarzeń',
            'description': 'Koszty rejsów, spływów, szkoleń',
        },
        'training': {
            'name': 'Szkolenia',
            'description': 'Kursy instruktorskie, patenty, certyfikaty',
        },
        'rent': {
            'name': 'Czynsz i media',
            'description': 'Wynajem przystani, magazynu, media',
        },
        'other_expense': {
            'name': 'Inne wydatki',
            'description': 'Pozostałe wydatki niepasujące do kategorii',
        },
    },
}

# =============================================================================
# PROGI I ALERTY
# =============================================================================
ALERTS: Dict[str, Any] = {
    # Przypomnienia o składkach
    'fee_reminder_days_before': 7,       # Przypomnienie X dni przed terminem
    'fee_first_warning_days': 14,        # Pierwsze ostrzeżenie po X dniach
    'fee_second_warning_days': 30,       # Drugie ostrzeżenie (priorytet)
    'fee_suspension_days': 60,           # Propozycja zawieszenia członkostwa

    # Progi finansowe
    'low_balance_warning': Decimal('500.00'),  # Alert gdy saldo < X
    'high_overdue_warning': Decimal('1000.00'),  # Alert gdy zaległości > X

    # Limity
    'max_overdue_count': 10,  # Alert gdy > X osób zalega
}

# =============================================================================
# PAROWANIE TRANSAKCJI
# =============================================================================
MATCHING: Dict[str, Any] = {
    # Pewność dopasowania (confidence levels)
    'confidence_levels': {
        'high': 0.9,     # Numer członkowski znaleziony
        'medium': 0.7,   # Nazwisko + kwota pasuje
        'low': 0.5,      # Tylko nazwisko lub kwota
    },

    # Minimalna pewność do auto-parowania
    'auto_match_threshold': 0.7,

    # Wzorce do wyszukiwania numeru członkowskiego
    'member_id_patterns': [
        r'(?:nr|numer|czlonek|czł|m)[:\s]*(\d+)',
        r'(?:członek|członka)[:\s]*(\d+)',
        r'(\d+)/20\d{2}',  # Format: 123/2025
        r'STW[:\s]*(\d+)',
    ],

    # Słowa kluczowe sugerujące składkę
    'fee_keywords': [
        'składka', 'skladka', 'czlonkowska', 'członkowska',
        'roczna', 'wpisowe', 'opłata', 'oplata', 'stw',
        'bałtyk', 'baltyk', 'członek', 'czlonek',
    ],

    # Słowa kluczowe dla darowizn
    'donation_keywords': [
        'darowizna', 'dar', 'wsparcie', 'dotacja', 'sponsor',
    ],
}

# =============================================================================
# FORMATOWANIE
# =============================================================================
FORMATTING: Dict[str, Any] = {
    'currency': 'PLN',
    'currency_symbol': 'zł',
    'decimal_places': 2,
    'thousand_separator': ' ',
    'decimal_separator': ',',
    'date_format': '%d.%m.%Y',
    'datetime_format': '%d.%m.%Y %H:%M',
}


def format_currency(amount: Decimal) -> str:
    """Formatuje kwotę zgodnie z polskim standardem."""
    formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    return f"{formatted} {FORMATTING['currency_symbol']}"


def format_date(d: date) -> str:
    """Formatuje datę zgodnie z polskim standardem."""
    return d.strftime(FORMATTING['date_format'])


# =============================================================================
# POLSKIE NAZWY MIESIĘCY
# =============================================================================
MONTHS_PL: Dict[int, str] = {
    1: 'Styczeń', 2: 'Luty', 3: 'Marzec', 4: 'Kwiecień',
    5: 'Maj', 6: 'Czerwiec', 7: 'Lipiec', 8: 'Sierpień',
    9: 'Wrzesień', 10: 'Październik', 11: 'Listopad', 12: 'Grudzień',
}

MONTHS_PL_GENITIVE: Dict[int, str] = {
    1: 'stycznia', 2: 'lutego', 3: 'marca', 4: 'kwietnia',
    5: 'maja', 6: 'czerwca', 7: 'lipca', 8: 'sierpnia',
    9: 'września', 10: 'października', 11: 'listopada', 12: 'grudnia',
}

# =============================================================================
# STATUSY (polskie etykiety)
# =============================================================================
STATUS_LABELS: Dict[str, Dict[str, str]] = {
    'fee': {
        'pending': 'Oczekująca',
        'paid': 'Opłacona',
        'overdue': 'Zaległa',
        'cancelled': 'Anulowana',
    },
    'member': {
        'active': 'Aktywny',
        'suspended': 'Zawieszony',
        'former': 'Były członek',
    },
    'transaction': {
        'income': 'Przychód',
        'expense': 'Wydatek',
    },
    'equipment': {
        'available': 'Dostępny',
        'reserved': 'Zarezerwowany',
        'maintenance': 'W naprawie',
        'retired': 'Wycofany',
    },
    'event': {
        'planned': 'Planowany',
        'registration_open': 'Zapisy otwarte',
        'full': 'Brak miejsc',
        'ongoing': 'W trakcie',
        'completed': 'Zakończony',
        'cancelled': 'Odwołany',
    },
}

# =============================================================================
# RAPORTOWANIE
# =============================================================================
REPORTS: Dict[str, Any] = {
    # Rok sprawozdawczy
    'reporting_year': get_current_fiscal_year(),

    # Próg przychodu dla uproszczonej ewidencji (ustawa o rachunkowości)
    'simplified_accounting_threshold': Decimal('150000.00'),

    # Kolumny eksportu CSV
    'csv_columns': {
        'fees': ['member_id', 'member_name', 'fee_type', 'amount', 'due_date', 'status', 'paid_date'],
        'transactions': ['date', 'type', 'category', 'amount', 'description', 'counterparty'],
        'overdue': ['member_id', 'member_name', 'email', 'phone', 'amount', 'days_overdue'],
        'members': ['member_number', 'first_name', 'last_name', 'email', 'phone', 'join_date', 'status'],
    },
}

# =============================================================================
# POWIADOMIENIA
# =============================================================================
NOTIFICATIONS: Dict[str, Dict[str, Any]] = {
    'email': {
        'enabled': True,
        'fee_reminder_subject': 'Przypomnienie o składce - STW Bałtyk Gdynia',
        'fee_overdue_subject': 'Zaległa składka - STW Bałtyk Gdynia',
        'event_reminder_subject': 'Przypomnienie o wydarzeniu - STW Bałtyk Gdynia',
        'from_name': 'STW Bałtyk Gdynia',
    },
    'ntfy': {
        'enabled': True,
        'server': 'http://192.168.88.32',
        'topic': 'baltyk-stw',
        'priority_normal': 3,
        'priority_high': 4,
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_category_name(category_type: str, category_key: str) -> str:
    """Get Polish name for transaction category."""
    categories = TRANSACTION_CATEGORIES.get(category_type, {})
    category = categories.get(category_key, {})
    return category.get('name', category_key)


def get_status_label(entity_type: str, status: str) -> str:
    """Get Polish label for status."""
    labels = STATUS_LABELS.get(entity_type, {})
    return labels.get(status, status)


def get_default_fee_config(fee_key: str) -> Dict[str, Any]:
    """Get default fee configuration by key."""
    return DEFAULT_FEES.get(fee_key, {})


def get_all_default_fees() -> Dict[str, Dict[str, Any]]:
    """Get all default fees as serializable dict (for API)."""
    result = {}
    for key, fee in DEFAULT_FEES.items():
        result[key] = {
            'name': fee['name'],
            'amount': float(fee['amount']),
            'frequency': fee.get('frequency', 'one_time'),
            'due_month': fee.get('due_month'),
            'due_day': fee.get('due_day'),
        }
    return result
