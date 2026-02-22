"""Transaction matching service for pairing bank transactions with members/fees."""

import re
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from app.models import Member, Fee
from app.config.finance_config import MATCHING


def match_transactions(
    transactions: List[Dict[str, Any]],
    members: List[Member],
    pending_fees: List[Fee]
) -> List[Dict[str, Any]]:
    """Match imported transactions to members and fees.

    Matching algorithm:
    1. Look for member number in transaction description
    2. Look for member last name in description
    3. Match amount to pending fee

    Args:
        transactions: List of parsed transactions
        members: List of active members
        pending_fees: List of unpaid fees

    Returns:
        Transactions with matching suggestions
    """
    # Create lookup structures
    members_by_number = {m.member_number: m for m in members if m.member_number}
    members_by_lastname = {}
    for m in members:
        lastname_lower = m.last_name.lower()
        if lastname_lower not in members_by_lastname:
            members_by_lastname[lastname_lower] = []
        members_by_lastname[lastname_lower].append(m)

    # Group fees by member
    fees_by_member = {}
    for fee in pending_fees:
        if fee.member_id not in fees_by_member:
            fees_by_member[fee.member_id] = []
        fees_by_member[fee.member_id].append(fee)

    results = []
    for tx in transactions:
        result = tx.copy()
        amount = Decimal(str(tx.get('amount', 0)))

        # Only match positive amounts (income)
        if amount <= 0:
            results.append(result)
            continue

        description = tx.get('description', '').lower()
        counterparty = tx.get('counterparty', '').lower()
        combined_text = f"{description} {counterparty}"

        # Try to find member
        member, confidence = _find_member(
            combined_text,
            amount,
            members_by_number,
            members_by_lastname,
            fees_by_member
        )

        if member:
            result['suggested_member_id'] = member.id
            result['suggested_member_name'] = member.full_name
            result['match_confidence'] = confidence

            # Try to find matching fee
            if member.id in fees_by_member:
                fee = _find_matching_fee(amount, fees_by_member[member.id])
                if fee:
                    result['suggested_fee_id'] = fee.id
                    result['suggested_fee_type'] = fee.fee_type.name if fee.fee_type else ''

        results.append(result)

    return results


def _find_member(
    text: str,
    amount: Decimal,
    members_by_number: Dict[str, Member],
    members_by_lastname: Dict[str, List[Member]],
    fees_by_member: Dict[int, List[Fee]]
) -> Tuple[Optional[Member], str]:
    """Find member by analyzing transaction text and amount.

    Returns:
        Tuple of (member, confidence) where confidence is 'high', 'medium', or 'low'
    """

    # 1. Look for member number pattern using configurable patterns
    member_number_patterns = MATCHING.get('member_id_patterns', [
        r'(?:nr|numer|czlonek|czł|m)[:\s]*(\d+)',
        r'(\d+)/20\d{2}',
    ])

    for pattern in member_number_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            member_num = match.group(1)
            if member_num in members_by_number:
                return members_by_number[member_num], 'high'

    # 2. Look for full name pattern
    for lastname, members_list in members_by_lastname.items():
        if len(lastname) < 3:  # Skip very short names
            continue

        if lastname in text:
            # Found lastname, check for matching fee amount
            for member in members_list:
                if member.id in fees_by_member:
                    for fee in fees_by_member[member.id]:
                        if abs(fee.amount - amount) < Decimal('0.01'):
                            return member, 'high'

            # No exact fee match, but lastname found
            if len(members_list) == 1:
                return members_list[0], 'medium'
            else:
                # Multiple members with same lastname
                # Try to match by first name
                for member in members_list:
                    if member.first_name.lower() in text:
                        return member, 'medium'
                # Return first match with low confidence
                return members_list[0], 'low'

    # 3. Try amount-only matching (low confidence)
    # Only if amount matches exactly one pending fee
    matching_fees = []
    for member_id, fees in fees_by_member.items():
        for fee in fees:
            if abs(fee.amount - amount) < Decimal('0.01'):
                matching_fees.append((fee.member, fee))

    if len(matching_fees) == 1:
        return matching_fees[0][0], 'low'

    return None, ''


def _find_matching_fee(amount: Decimal, fees: List[Fee]) -> Optional[Fee]:
    """Find fee matching the transaction amount.

    Prioritizes:
    1. Exact amount match
    2. Oldest due date first
    """
    # Sort by due date (oldest first)
    sorted_fees = sorted(fees, key=lambda f: f.due_date)

    # First, look for exact match
    for fee in sorted_fees:
        if abs(fee.amount - amount) < Decimal('0.01'):
            return fee

    return None


def is_likely_fee_payment(text: str) -> bool:
    """Check if transaction description suggests a fee payment."""
    text_lower = text.lower()
    fee_keywords = MATCHING.get('fee_keywords', [])
    return any(keyword in text_lower for keyword in fee_keywords)


def is_likely_donation(text: str) -> bool:
    """Check if transaction description suggests a donation."""
    text_lower = text.lower()
    donation_keywords = MATCHING.get('donation_keywords', [])
    return any(keyword in text_lower for keyword in donation_keywords)


def get_match_confidence_value(confidence: str) -> float:
    """Get numeric confidence value for match level."""
    levels = MATCHING.get('confidence_levels', {
        'high': 0.9,
        'medium': 0.7,
        'low': 0.5,
    })
    return levels.get(confidence, 0.0)


def should_auto_match(confidence: str) -> bool:
    """Check if confidence level is high enough for automatic matching."""
    threshold = MATCHING.get('auto_match_threshold', 0.7)
    return get_match_confidence_value(confidence) >= threshold


def suggest_member_for_transaction(
    transaction: Dict[str, Any],
    members: List[Member]
) -> Optional[Dict[str, Any]]:
    """Suggest a member for a single transaction.

    Used for UI autocomplete when manually matching.
    """
    description = transaction.get('description', '').lower()
    counterparty = transaction.get('counterparty', '').lower()
    combined = f"{description} {counterparty}"

    suggestions = []

    for member in members:
        score = 0
        reasons = []

        # Check for member number
        if member.member_number and member.member_number in combined:
            score += 100
            reasons.append('numer członkowski')

        # Check for last name
        if member.last_name.lower() in combined:
            score += 50
            reasons.append('nazwisko')

        # Check for first name
        if member.first_name.lower() in combined:
            score += 20
            reasons.append('imię')

        if score > 0:
            suggestions.append({
                'member_id': member.id,
                'member_name': member.full_name,
                'score': score,
                'reasons': reasons
            })

    # Sort by score descending
    suggestions.sort(key=lambda x: x['score'], reverse=True)

    return suggestions[:5] if suggestions else None
