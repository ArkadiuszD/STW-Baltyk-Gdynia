"""Bank statement import parsers for MT940 and CSV formats."""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any
import re
import csv
import io

import mt940


def parse_mt940(content: bytes) -> List[Dict[str, Any]]:
    """Parse MT940 bank statement file.

    MT940 is a standard format used by banks (including Santander).

    Args:
        content: Raw file content as bytes

    Returns:
        List of parsed transactions
    """
    try:
        # Try UTF-8 first, then Windows-1250 (common in Polish banks)
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('windows-1250')

        transactions = []

        # Parse MT940 using the mt940 library
        parsed = mt940.parse(io.StringIO(text))

        for statement in parsed:
            for transaction in statement.transactions:
                tx_data = {
                    'date': transaction.data.get('date', statement.data.get('date')),
                    'amount': str(transaction.data.get('amount', Decimal('0'))),
                    'description': _clean_description(
                        transaction.data.get('transaction_details', '') or
                        transaction.data.get('extra_details', '')
                    ),
                    'counterparty': _extract_counterparty(
                        transaction.data.get('transaction_details', '')
                    ),
                    'bank_reference': transaction.data.get('bank_reference', '') or
                                      transaction.data.get('customer_reference', ''),
                    'import_source': 'mt940'
                }

                # Convert date if needed
                if isinstance(tx_data['date'], date):
                    tx_data['date'] = tx_data['date'].isoformat()

                transactions.append(tx_data)

        return transactions

    except Exception as e:
        raise ValueError(f"Błąd parsowania MT940: {str(e)}")


def parse_csv(content: bytes) -> List[Dict[str, Any]]:
    """Parse CSV bank statement file (Santander format).

    Santander iBiznes24 exports CSV with Polish headers.

    Expected columns:
    - Data operacji / Data księgowania
    - Kwota
    - Opis operacji / Tytuł
    - Nadawca/Odbiorca

    Args:
        content: Raw file content as bytes

    Returns:
        List of parsed transactions
    """
    try:
        # Try common encodings
        for encoding in ['utf-8', 'windows-1250', 'iso-8859-2']:
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Nie można odczytać pliku - nieznane kodowanie")

        transactions = []

        # Try different delimiters
        for delimiter in [';', ',', '\t']:
            try:
                reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
                # Check if we got valid headers
                if reader.fieldnames and len(reader.fieldnames) > 1:
                    break
            except Exception:
                continue

        # Map common column names (Santander variations)
        date_columns = ['Data operacji', 'Data księgowania', 'Data', 'Data waluty']
        amount_columns = ['Kwota', 'Kwota operacji', 'Wartość']
        description_columns = ['Opis operacji', 'Tytuł', 'Szczegóły', 'Opis']
        counterparty_columns = ['Nadawca/Odbiorca', 'Kontrahent', 'Nazwa kontrahenta']
        reference_columns = ['Numer referencyjny', 'Referencja', 'Nr referencyjny']

        for row in reader:
            if not row:
                continue

            # Find values by trying different column names
            tx_date = _find_column_value(row, date_columns)
            amount = _find_column_value(row, amount_columns)
            description = _find_column_value(row, description_columns)
            counterparty = _find_column_value(row, counterparty_columns)
            reference = _find_column_value(row, reference_columns)

            if not tx_date or not amount:
                continue

            # Parse date (various formats)
            parsed_date = _parse_date(tx_date)
            if not parsed_date:
                continue

            # Parse amount (handle Polish format: 1 234,56)
            parsed_amount = _parse_amount(amount)
            if parsed_amount is None:
                continue

            transactions.append({
                'date': parsed_date,
                'amount': str(parsed_amount),
                'description': _clean_description(description or ''),
                'counterparty': counterparty or '',
                'bank_reference': reference or '',
                'import_source': 'csv'
            })

        return transactions

    except Exception as e:
        raise ValueError(f"Błąd parsowania CSV: {str(e)}")


def _find_column_value(row: Dict, column_names: List[str]) -> str:
    """Find value by trying multiple possible column names."""
    for col in column_names:
        if col in row and row[col]:
            return row[col].strip()
    return ''


def _parse_date(date_str: str) -> str:
    """Parse date string to ISO format."""
    date_str = date_str.strip()

    # Common formats
    formats = [
        '%Y-%m-%d',       # ISO
        '%d-%m-%Y',       # DD-MM-YYYY
        '%d.%m.%Y',       # DD.MM.YYYY (Polish)
        '%d/%m/%Y',       # DD/MM/YYYY
        '%Y.%m.%d',       # YYYY.MM.DD
    ]

    from datetime import datetime
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.date().isoformat()
        except ValueError:
            continue

    return ''


def _parse_amount(amount_str: str) -> Decimal:
    """Parse amount string to Decimal."""
    amount_str = amount_str.strip()

    # Remove currency symbol and spaces
    amount_str = re.sub(r'[PLN\sZŁ]+', '', amount_str, flags=re.IGNORECASE)

    # Handle Polish format (space as thousands separator, comma as decimal)
    amount_str = amount_str.replace(' ', '').replace(',', '.')

    try:
        return Decimal(amount_str)
    except Exception:
        return None


def _clean_description(description: str) -> str:
    """Clean and normalize transaction description."""
    if not description:
        return ''

    # Remove extra whitespace
    description = ' '.join(description.split())

    # Remove common MT940 prefixes
    prefixes_to_remove = ['/ROC/', '/RFB/', '/ID/', '/BNF/', '/ORD/']
    for prefix in prefixes_to_remove:
        description = description.replace(prefix, ' ')

    return description.strip()


def _extract_counterparty(details: str) -> str:
    """Extract counterparty name from transaction details."""
    if not details:
        return ''

    # Look for common patterns
    patterns = [
        r'/ORD/(.+?)(?:/|$)',     # Ordering customer
        r'/BNF/(.+?)(?:/|$)',     # Beneficiary
        r'OD:\s*(.+?)(?:\s|$)',   # Polish "OD:" prefix
        r'NA RZECZ:\s*(.+?)(?:\s|$)',  # Polish "NA RZECZ:" prefix
    ]

    for pattern in patterns:
        match = re.search(pattern, details, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # If no pattern matched, try to get first meaningful part
    parts = details.split('/')
    for part in parts:
        part = part.strip()
        # Skip short parts and known codes
        if len(part) > 5 and not part.isupper():
            return part

    return ''
