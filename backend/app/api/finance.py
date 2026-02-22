from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.models import Transaction, Member, Fee
from app.models.transaction import TransactionType, TransactionCategory
from app.models.fee import FeeStatus
from app.schemas import TransactionSchema, TransactionCreateSchema, TransactionMatchSchema
from app.services.bank_import import parse_mt940, parse_csv
from app.services.matching import match_transactions

finance_bp = Blueprint('finance', __name__)
transaction_schema = TransactionSchema()
transactions_schema = TransactionSchema(many=True)
transaction_create_schema = TransactionCreateSchema()
transaction_match_schema = TransactionMatchSchema()


def check_write_permission():
    """Check if user has write permission (admin or treasurer)."""
    claims = get_jwt()
    role = claims.get('role')
    return role in ['admin', 'treasurer']


@finance_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get all transactions with filtering."""
    transaction_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    unmatched_only = request.args.get('unmatched', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Transaction.query

    # Filter by type
    if transaction_type:
        try:
            query = query.filter(Transaction.type == TransactionType(transaction_type))
        except ValueError:
            pass

    # Filter by category
    if category:
        try:
            query = query.filter(Transaction.category == TransactionCategory(category))
        except ValueError:
            pass

    # Filter by date range
    if start_date:
        try:
            query = query.filter(Transaction.date >= date.fromisoformat(start_date))
        except ValueError:
            pass

    if end_date:
        try:
            query = query.filter(Transaction.date <= date.fromisoformat(end_date))
        except ValueError:
            pass

    # Filter unmatched transactions
    if unmatched_only:
        query = query.filter(
            Transaction.matched_member_id.is_(None),
            Transaction.type == TransactionType.INCOME,
            Transaction.category == TransactionCategory.FEES
        )

    # Order by date descending
    query = query.order_by(db.desc(Transaction.date))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': transactions_schema.dump(pagination.items),
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/transactions', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create a manual transaction."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    try:
        data = transaction_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    user_id = get_jwt_identity()

    transaction = Transaction(
        date=data['date'],
        amount=Decimal(str(data['amount'])),
        type=TransactionType(data['type']),
        category=TransactionCategory(data['category']),
        description=data['description'],
        counterparty=data.get('counterparty'),
        bank_reference=data.get('bank_reference'),
        matched_member_id=data.get('matched_member_id'),
        match_confidence='manual' if data.get('matched_member_id') else None,
        import_source='manual',
        created_by_id=user_id
    )

    db.session.add(transaction)
    db.session.commit()

    return jsonify(transaction_schema.dump(transaction)), 201


@finance_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def update_transaction(transaction_id):
    """Update a transaction."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    transaction = Transaction.query.get_or_404(transaction_id)
    data = request.json

    if 'date' in data:
        transaction.date = date.fromisoformat(data['date'])
    if 'amount' in data:
        transaction.amount = Decimal(str(data['amount']))
    if 'description' in data:
        transaction.description = data['description']
    if 'counterparty' in data:
        transaction.counterparty = data['counterparty']
    if 'category' in data:
        transaction.category = TransactionCategory(data['category'])

    db.session.commit()
    return jsonify(transaction_schema.dump(transaction)), 200


@finance_bp.route('/transactions/<int:transaction_id>/match', methods=['POST'])
@jwt_required()
def match_transaction(transaction_id):
    """Match transaction to a member and optionally a fee."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    transaction = Transaction.query.get_or_404(transaction_id)

    try:
        data = transaction_match_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    member = Member.query.get(data['member_id'])
    if not member:
        return jsonify({'error': 'Członek nie znaleziony'}), 404

    transaction.matched_member_id = member.id
    transaction.match_confidence = 'manual'

    # If fee_id provided, mark that fee as paid
    if 'fee_id' in data and data['fee_id']:
        fee = Fee.query.get(data['fee_id'])
        if fee and fee.member_id == member.id:
            fee.mark_as_paid(
                paid_date=transaction.date,
                transaction_id=transaction.id
            )

    db.session.commit()
    return jsonify(transaction_schema.dump(transaction)), 200


@finance_bp.route('/transactions/<int:transaction_id>/unmatch', methods=['POST'])
@jwt_required()
def unmatch_transaction(transaction_id):
    """Remove match from transaction."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    transaction = Transaction.query.get_or_404(transaction_id)

    # If linked to a fee, unlink it
    if transaction.matched_fee:
        transaction.matched_fee.transaction_id = None
        transaction.matched_fee.status = FeeStatus.PENDING
        transaction.matched_fee.paid_date = None

    transaction.matched_member_id = None
    transaction.match_confidence = None

    db.session.commit()
    return jsonify(transaction_schema.dump(transaction)), 200


@finance_bp.route('/import', methods=['POST'])
@jwt_required()
def import_bank_statement():
    """Import bank statement (MT940 or CSV)."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Pusta nazwa pliku'}), 400

    file_type = request.form.get('type', 'auto')
    content = file.read()

    try:
        # Detect file type
        if file_type == 'auto':
            if file.filename.endswith(('.sta', '.mt940', '.STA')):
                file_type = 'mt940'
            elif file.filename.endswith(('.csv', '.CSV')):
                file_type = 'csv'
            else:
                return jsonify({'error': 'Nieznany format pliku. Użyj MT940 lub CSV.'}), 400

        # Parse file
        if file_type == 'mt940':
            parsed_transactions = parse_mt940(content)
        else:
            parsed_transactions = parse_csv(content)

        if not parsed_transactions:
            return jsonify({'error': 'Nie znaleziono transakcji w pliku'}), 400

        # Get active members for matching
        from app.models.member import MemberStatus
        members = Member.query.filter_by(status=MemberStatus.ACTIVE).all()

        # Get pending fees
        pending_fees = Fee.query.filter(
            Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])
        ).all()

        # Match transactions
        matched_results = match_transactions(parsed_transactions, members, pending_fees)

        # Return preview (don't save yet)
        return jsonify({
            'transactions': matched_results,
            'total': len(matched_results),
            'matched': sum(1 for t in matched_results if t.get('suggested_member_id')),
            'unmatched': sum(1 for t in matched_results if not t.get('suggested_member_id'))
        }), 200

    except Exception as e:
        return jsonify({'error': f'Błąd parsowania pliku: {str(e)}'}), 400


@finance_bp.route('/import/confirm', methods=['POST'])
@jwt_required()
def confirm_import():
    """Confirm and save imported transactions."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    data = request.json
    transactions_data = data.get('transactions', [])
    user_id = get_jwt_identity()

    created_count = 0
    skipped_count = 0

    for tx_data in transactions_data:
        # Skip if bank_reference already exists
        if tx_data.get('bank_reference'):
            existing = Transaction.query.filter_by(
                bank_reference=tx_data['bank_reference']
            ).first()
            if existing:
                skipped_count += 1
                continue

        # Determine transaction type
        amount = Decimal(str(tx_data['amount']))
        tx_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE

        # Default category based on type
        if tx_type == TransactionType.INCOME:
            category = TransactionCategory.FEES  # Assume incoming = fees
        else:
            category = TransactionCategory.OTHER_EXPENSE

        transaction = Transaction(
            date=date.fromisoformat(tx_data['date']),
            amount=abs(amount),
            type=tx_type,
            category=category,
            description=tx_data.get('description', ''),
            counterparty=tx_data.get('counterparty'),
            bank_reference=tx_data.get('bank_reference'),
            matched_member_id=tx_data.get('member_id'),
            match_confidence=tx_data.get('match_confidence'),
            imported_at=datetime.utcnow(),
            import_source=tx_data.get('import_source', 'bank'),
            created_by_id=user_id
        )

        db.session.add(transaction)

        # If matched to a fee, mark it as paid
        if tx_data.get('fee_id') and tx_data.get('member_id'):
            fee = Fee.query.get(tx_data['fee_id'])
            if fee:
                db.session.flush()  # Get transaction.id
                fee.mark_as_paid(
                    paid_date=transaction.date,
                    transaction_id=transaction.id
                )

        created_count += 1

    db.session.commit()

    return jsonify({
        'message': f'Zaimportowano {created_count} transakcji',
        'created': created_count,
        'skipped': skipped_count
    }), 201


@finance_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    """Get current balance and summary."""
    # Total income
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.INCOME
    ).scalar() or 0

    # Total expenses
    total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE
    ).scalar() or 0

    # Current year summary
    current_year = date.today().year
    year_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.INCOME,
        db.extract('year', Transaction.date) == current_year
    ).scalar() or 0

    year_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        db.extract('year', Transaction.date) == current_year
    ).scalar() or 0

    return jsonify({
        'balance': float(total_income - total_expenses),
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'year': current_year,
        'year_income': float(year_income),
        'year_expenses': float(year_expenses),
        'year_balance': float(year_income - year_expenses)
    }), 200


@finance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_finance_stats():
    """Get finance statistics by category."""
    year = request.args.get('year', date.today().year, type=int)

    # Income by category
    income_by_category = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.type == TransactionType.INCOME,
        db.extract('year', Transaction.date) == year
    ).group_by(Transaction.category).all()

    # Expenses by category
    expenses_by_category = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.type == TransactionType.EXPENSE,
        db.extract('year', Transaction.date) == year
    ).group_by(Transaction.category).all()

    return jsonify({
        'year': year,
        'income': {cat.value: float(amount) for cat, amount in income_by_category},
        'expenses': {cat.value: float(amount) for cat, amount in expenses_by_category}
    }), 200
