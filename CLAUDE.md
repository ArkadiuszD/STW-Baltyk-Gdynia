# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Język / Language

**Odpowiadaj użytkownikowi po polsku** - plany, wyjaśnienia, opisy commitów, komunikaty.
Kod, komentarze w kodzie, nazwy zmiennych/funkcji i dokumentacja techniczna (README, docstrings) - po angielsku (clean code).

## Project Overview

**STW Bałtyk Gdynia** - Association management system for "Stowarzyszenie Turystyki Wodnej Bałtyk Gdynia" (Water Tourism Association).

### Stack
- **Backend:** Python 3.11, Flask 3.x, SQLAlchemy, PostgreSQL 15
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Auth:** JWT (Flask-JWT-Extended)
- **Server:** Gunicorn + Nginx

## Project Structure

```
stw/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── api/                 # REST API blueprints
│   │   │   ├── auth.py          # /api/auth (login, refresh)
│   │   │   ├── members.py       # /api/members (CRUD)
│   │   │   ├── fees.py          # /api/fees (CRUD + config)
│   │   │   ├── finance.py       # /api/transactions
│   │   │   ├── equipment.py     # /api/equipment
│   │   │   ├── events.py        # /api/events
│   │   │   └── reports.py       # /api/reports
│   │   ├── config/
│   │   │   └── finance_config.py  # Central finance configuration
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Marshmallow schemas
│   │   └── services/            # Business logic
│   ├── migrations/              # Alembic migrations
│   ├── scripts/
│   │   └── create_admin.py      # Admin user creation
│   ├── config.py                # Flask config (dev/prod/test)
│   ├── run.py                   # Application entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API client
│   │   ├── config/
│   │   │   └── finance.ts       # Frontend finance config
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
└── CLAUDE.md
```

## Common Commands

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Create admin user
python scripts/create_admin.py

# Run development server
FLASK_ENV=development python run.py
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev        # Development server
npm run build      # Production build
npm run lint       # ESLint
```

### Database
```bash
# PostgreSQL
psql -U stw_user -d stw_baltyk

# Flask-Migrate
flask db migrate -m "description"
flask db upgrade
flask db downgrade
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | JWT login |
| `/api/auth/refresh` | POST | Refresh token |
| `/api/members` | GET/POST | Members CRUD |
| `/api/members/<id>` | GET/PUT/DELETE | Single member |
| `/api/fees` | GET/POST | Fees management |
| `/api/fees/config/defaults` | GET | Default fee config |
| `/api/transactions` | GET/POST | Transactions |
| `/api/equipment` | GET/POST | Equipment catalog |
| `/api/events` | GET/POST | Events management |

## Configuration

### Environment Variables (.env)
```env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=<random-key>
JWT_SECRET_KEY=<random-key>
DATABASE_URL=postgresql://stw_user:password@localhost:5432/stw_baltyk
NTFY_SERVER=http://192.168.88.32
NTFY_TOPIC=baltyk-stw
CORS_ORIGINS=http://192.168.88.200,http://baltyk.lan
```

### Finance Configuration
All financial parameters are centralized in:
- Backend: `backend/app/config/finance_config.py`
- Frontend: `frontend/src/config/finance.ts`

Includes: default fees, transaction categories, Polish labels, alerts thresholds.

## Deployment (LXC 200)

### Production Location
```
/opt/stw/
├── backend/          # Flask app
│   └── venv/         # Python virtual environment
└── frontend/
    └── dist/         # Built React app (served by Nginx)
```

### Services
```bash
systemctl status stw-baltyk    # Flask/Gunicorn
systemctl status nginx         # Nginx reverse proxy
systemctl status postgresql    # Database
```

### Logs
```bash
# Flask logs
tail -f /var/log/stw-baltyk/error.log
tail -f /var/log/stw-baltyk/access.log

# Nginx logs
tail -f /var/log/nginx/error.log
```

### Deploy Script
```bash
# From Proxmox host
pct exec 200 -- bash /opt/stw/deploy.sh
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `ADMIN` | Administrator | Full access |
| `TREASURER` | Skarbnik | Finance, fees, members |
| `BOARD` | Zarząd | Read-only |

## Polish Labels

All user-facing labels are in Polish:
- Fee statuses: Oczekująca, Opłacona, Zaległa, Anulowana
- Member statuses: Aktywny, Zawieszony, Były członek
- Transaction types: Przychód, Wydatek
- Months: Styczeń, Luty, ...

See `finance_config.py` for complete label mappings.

## LXC 200 Deployment Details

### Container Info
| Property | Value |
|----------|-------|
| LXC ID | 200 |
| Hostname | stw-baltyk |
| IP | 192.168.88.200 |
| RAM | 2GB |
| Disk | 10GB (ssd-storage) |
| OS | Debian 12 |

### Installed Software
- Python 3.11 + venv
- Node.js 20.x
- PostgreSQL 15
- Nginx 1.22
- Git

### Database
- **Name:** stw_baltyk
- **User:** stw_user
- **Password:** STWBaltyk2026

### Admin User
- **Email:** admin@stwbaltyk.pl
- **Password:** Admin2026!

### Paths
```
/opt/stw/
├── backend/
│   ├── venv/
│   ├── app/
│   ├── migrations/
│   ├── scripts/
│   ├── .env
│   └── run.py
└── frontend/
    └── dist/           # Built production files
```

### Systemd Services
```bash
# Flask backend
systemctl status stw-baltyk
# Config: /etc/systemd/system/stw-baltyk.service

# Nginx
systemctl status nginx
# Config: /etc/nginx/sites-available/stw-baltyk
```

### Monitoring
- **Node Exporter:** http://192.168.88.200:9100/metrics
- **Promtail:** Logs → Loki (192.168.88.23:3100)
- **Grafana Labels:** `container="stw-baltyk"`, `lxc_id="200"`
- **Blackbox:** Health check at `/api/health`

### Access URLs
| URL | Description |
|-----|-------------|
| http://192.168.88.200 | Direct access |
| http://baltyk.lan | Via NPM proxy |

### Useful Commands
```bash
# On Proxmox host
pct exec 200 -- systemctl restart stw-baltyk   # Restart backend
pct exec 200 -- systemctl restart nginx        # Restart nginx
pct exec 200 -- journalctl -u stw-baltyk -f    # Follow logs
pct exec 200 -- tail -f /var/log/stw-baltyk/error.log

# In container
cd /opt/stw/backend
source venv/bin/activate
flask db upgrade                               # Run migrations
python scripts/create_admin.py                 # Create admin

# Frontend rebuild
cd /opt/stw/frontend
npm run build
```

### Deploy Updates
```bash
# On Proxmox host
pct exec 200 -- bash -c "cd /opt/stw && git pull"
pct exec 200 -- bash -c "cd /opt/stw/backend && source venv/bin/activate && flask db upgrade"
pct exec 200 -- bash -c "cd /opt/stw/frontend && npm install && npm run build"
pct exec 200 -- systemctl restart stw-baltyk
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL
pct exec 200 -- systemctl status postgresql
pct exec 200 -- su - postgres -c "psql -c '\\du'"

# Test connection
pct exec 200 -- PGPASSWORD='STWBaltyk2026' psql -h localhost -U stw_user -d stw_baltyk -c "SELECT 1;"
```

### Backend Issues
```bash
# Check logs
pct exec 200 -- tail -50 /var/log/stw-baltyk/error.log

# Test API directly
pct exec 200 -- curl http://127.0.0.1:5000/api/health
```

### Frontend Issues
```bash
# Rebuild
pct exec 200 -- bash -c "cd /opt/stw/frontend && npm run build"

# Check Nginx
pct exec 200 -- nginx -t
pct exec 200 -- systemctl reload nginx
```
