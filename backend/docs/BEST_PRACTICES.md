# Best Practices - STW Bałtyk Gdynia Backend

## Architektura

### Struktura warstw

```
API (Blueprints) → Services → Models → Database
     ↓                ↓          ↓
  Schemas         BaseService  BaseModel
  Decorators      Business     TimestampMixin
  Responses       Logic
```

### Zasady

1. **API Layer** - tylko routing, walidacja wejścia, formatowanie wyjścia
2. **Service Layer** - cała logika biznesowa
3. **Model Layer** - definicje danych, relacje, proste property

---

## Models

### Używaj BaseModel

```python
from app.models.base import BaseModel

class MyModel(BaseModel):
    __tablename__ = 'my_models'
    name = db.Column(db.String(100))
    # id, created_at, updated_at są dziedziczone
```

### Enumy - UPPERCASE w PostgreSQL

SQLAlchemy używa **nazw** enum (UPPERCASE), nie wartości:

```python
# Python
class MemberStatus(PyEnum):
    ACTIVE = 'active'      # value = 'active'
    SUSPENDED = 'suspended'

# PostgreSQL - używa NAZWY (ACTIVE), nie wartości (active)
CREATE TYPE memberstatus AS ENUM ('ACTIVE', 'SUSPENDED', 'FORMER');

# Filtrowanie - używaj enum, nie stringa
query.filter(Member.status == MemberStatus.ACTIVE)  # ✅
query.filter(Member.status == 'active')              # ❌
```

### Relacje

```python
# One-to-Many z cascade
fees = db.relationship('Fee', backref='member',
                       lazy='dynamic',
                       cascade='all, delete-orphan')

# lazy='dynamic' - zwraca Query, nie listę (lepsze dla dużych zbiorów)
member.fees.filter(...).count()  # nie ładuje wszystkich do pamięci
```

---

## Services

### Używaj BaseService

```python
from app.services.base import BaseService, SoftDeleteMixin

class MemberService(SoftDeleteMixin, BaseService[Member]):
    model = Member
    search_fields = ['first_name', 'last_name', 'email']
    default_order = 'last_name'
    deleted_status = MemberStatus.FORMER

# Singleton dla wygody
member_service = MemberService()
```

### Dostępne metody

```python
# CRUD
service.get_by_id(1)
service.get_or_404(1)
service.get_all(page=1, per_page=20, search='Jan', filters={'status': 'active'})
service.create({'name': 'Test'})
service.update(1, {'name': 'Updated'})
service.delete(1)

# Helpers
service.exists(email='test@test.pl')
service.find_by(email='test@test.pl')
service.find_all_by(status='active')
service.count(status='active')
```

### Walidacja w serwisie

```python
def create(self, data: Dict[str, Any]) -> Member:
    # Sprawdź duplikaty
    if self.exists(email=data['email']):
        raise ValueError('Email już istnieje')

    # Transformuj dane
    if 'status' in data and isinstance(data['status'], str):
        data['status'] = MemberStatus(data['status'])

    return super().create(data)
```

---

## API Endpoints

### Używaj dekoratorów

```python
from app.utils.decorators import admin_required, write_permission_required

@members_bp.route('', methods=['POST'])
@jwt_required()
@write_permission_required  # admin lub treasurer
def create_member():
    pass

@members_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required  # tylko admin
def delete_member(id):
    pass
```

### Używaj response helpers

```python
from app.utils.responses import success, created, error, validation_error, conflict, paginated

@members_bp.route('', methods=['GET'])
@jwt_required()
def get_members():
    result = member_service.get_all(page=1, per_page=50)
    return paginated(
        items=result.items,
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        schema=members_schema
    )

@members_bp.route('', methods=['POST'])
@jwt_required()
def create_member():
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return validation_error(err.messages)

    try:
        member = member_service.create(data)
    except ValueError as e:
        return conflict(str(e))

    return created(member_schema.dump(member))
```

### Standardowe odpowiedzi

| Funkcja | Status | Użycie |
|---------|--------|--------|
| `success(data)` | 200 | GET, PUT |
| `created(data)` | 201 | POST |
| `no_content()` | 204 | DELETE |
| `error(msg)` | 400 | Błąd ogólny |
| `validation_error(errors)` | 400 | Błędy walidacji |
| `forbidden(msg)` | 403 | Brak uprawnień |
| `not_found(msg)` | 404 | Nie znaleziono |
| `conflict(msg)` | 409 | Duplikat |

---

## Schemas (Marshmallow)

### Używaj enum_values

```python
from app.utils.enums import enum_values
from app.models.member import MemberStatus

class MemberSchema(ma.Schema):
    status = fields.Str(
        validate=validate.OneOf(enum_values(MemberStatus)),
        load_default=MemberStatus.ACTIVE.value
    )
```

### Oddzielne schematy dla Create/Update

```python
class MemberSchema(ma.Schema):
    """Schema do odczytu (GET)."""
    id = fields.Int(dump_only=True)
    full_name = fields.Str(dump_only=True)
    # ...

class MemberCreateSchema(ma.Schema):
    """Schema do tworzenia (POST)."""
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    # ...

class MemberUpdateSchema(ma.Schema):
    """Schema do aktualizacji (PUT) - wszystko opcjonalne."""
    email = fields.Email()
    first_name = fields.Str()
    # ...
```

---

## Liquibase (Migracje DB)

### Struktura changelogów

```
backend/db/liquibase/
├── changelog/
│   ├── db.changelog-master.yaml  # główny plik
│   └── v1.0.0/
│       ├── 001-create-enums.yaml
│       ├── 002-create-users.yaml
│       ├── 003-create-members.yaml
│       └── 008-seed-admin-user.yaml
```

### Konwencje nazewnictwa

- `XXX-opis.yaml` - numer porządkowy + krótki opis
- changeSet ID: `nazwa-NNN-opis` np. `users-001-create-table`
- Autor: `stw-baltyk`

### Enumy PostgreSQL

```yaml
- changeSet:
    id: enum-001-userrole
    author: stw-baltyk
    changes:
      - sql:
          sql: |
            CREATE TYPE userrole AS ENUM ('ADMIN', 'TREASURER', 'BOARD');
```

### Seed data z preConditions

```yaml
- changeSet:
    id: seed-001-admin-user
    author: stw-baltyk
    preConditions:
      - onFail: MARK_RAN
      - sqlCheck:
          expectedResult: 0
          sql: SELECT COUNT(*) FROM users WHERE email = 'admin@stwbaltyk.pl'
    changes:
      - insert:
          tableName: users
          columns:
            - column:
                name: email
                value: admin@stwbaltyk.pl
```

### Komendy

```bash
./install-db.sh           # Uruchom migracje
./install-db.sh --drop    # Usuń i odtwórz bazę
./install-db.sh --status  # Status migracji
./install-db.sh --rollback 1  # Cofnij 1 changeset
```

---

## Deployment

### Git-based workflow

```bash
./deploy.sh              # Pełny deploy (push, pull, pip, restart)
./deploy.sh --quick      # Szybki (bez pip install)
./deploy.sh --setup      # Pierwsza instalacja
./deploy.sh --db         # Tylko migracje Liquibase
./deploy.sh --db-drop    # Drop i odtwórz bazę
```

### Struktura w LXC

```
/opt/stw/
├── backend/
│   ├── venv/
│   ├── app/
│   ├── run.py
│   └── .env
└── frontend/
    └── dist/
```

### Serwisy

- `stw-baltyk.service` - Flask/Gunicorn na porcie 5000
- nginx - reverse proxy (`/api` → Flask, `/` → static)
- PostgreSQL - baza `stw_baltyk`

---

## JWT Authentication

### Konfiguracja

```python
# .env
JWT_SECRET_KEY=tajny-klucz
JWT_ACCESS_TOKEN_EXPIRES=900      # 15 minut
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 dni
```

### Identity jako string

```python
# ZAWSZE string, nie int
access_token = create_access_token(
    identity=str(user.id),  # ✅
    additional_claims={'role': user.role.value}
)
```

### Pobieranie aktualnego użytkownika

```python
from app.utils.decorators import get_current_user_id, get_current_user_role

@jwt_required()
def my_endpoint():
    user_id = get_current_user_id()  # int
    role = get_current_user_role()    # str
```

---

## Polskie komunikaty błędów

Wszystkie komunikaty błędów dla użytkownika po polsku:

```python
return error('Brak uprawnień do wykonania tej operacji')
return validation_error({'email': ['Nieprawidłowy format email']})
return conflict('Email już istnieje w systemie')
return not_found('Członek nie został znaleziony')
```

---

## Testowanie

### Uruchamianie testów

```bash
cd backend
source venv/bin/activate
pytest
pytest -v  # verbose
pytest tests/test_members.py  # konkretny plik
```

### Struktura testów

```
backend/tests/
├── conftest.py      # fixtures (app, db, client)
├── test_auth.py
├── test_members.py
└── test_services/
    └── test_member_service.py
```

---

## Checklist przed PR

- [ ] Kod działa lokalnie (`pytest`)
- [ ] Enumy używają UPPERCASE w PostgreSQL
- [ ] Walidacja w serwisie, nie w API
- [ ] Dekoratory uprawnień na endpointach
- [ ] Response helpers zamiast ręcznych jsonify
- [ ] Polskie komunikaty błędów
- [ ] Liquibase changeset dla zmian w DB
- [ ] Deploy testowy na LXC 200
