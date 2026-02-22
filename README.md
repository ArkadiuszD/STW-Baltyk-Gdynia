# STW Bałtyk Gdynia - System Zarządzania Stowarzyszeniem

Aplikacja webowa do zarządzania Stowarzyszeniem Turystyki Wodnej "Bałtyk Gdynia".

## Funkcjonalności

- **Członkowie** - rejestracja, edycja, statusy (aktywny/zawieszony/były)
- **Składki** - naliczanie, śledzenie, przypomnienia o zaległościach
- **Finanse** - ewidencja uproszczona, import wyciągów MT940/CSV (Santander)
- **Sprzęt wodny** - katalog kajaków/żaglówek/SUP, rezerwacje, przeglądy
- **Wydarzenia** - rejsy, spływy, szkolenia, zapisy uczestników
- **Raporty** - eksport CSV (składki, zaległości, członkowie, ewidencja)

## Technologie

### Backend
- Python 3.11+
- Flask 3.x
- PostgreSQL 15 (lub SQLite do developmentu)
- JWT (Flask-JWT-Extended)

### Frontend
- React 18 + TypeScript
- Vite 5
- Tailwind CSS
- React Query (TanStack Query)

## Uruchomienie (Development)

### Backend

```bash
cd backend

# Utwórz virtualenv
python3 -m venv venv
source venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt

# Skopiuj konfigurację
cp .env.example .env
# Edytuj .env według potrzeb

# Zainicjuj bazę danych
flask init-db

# Dodaj dane demo
flask seed-demo

# Uruchom serwer
flask run
# lub: python run.py
```

Backend będzie dostępny na http://localhost:5000

### Frontend

```bash
cd frontend

# Zainstaluj zależności
npm install

# Uruchom dev server
npm run dev
```

Frontend będzie dostępny na http://localhost:5173

### Dane logowania (demo)

- Email: `admin@baltyk.pl`
- Hasło: `admin123`

## Produkcja (Proxmox LXC)

### Utworzenie kontenera LXC

```bash
# Na hoście Proxmox
pct create 153 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname baltyk \
  --memory 2048 \
  --cores 2 \
  --rootfs ssd-storage:10 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 1 \
  --features nesting=1

pct start 153
pct enter 153
```

### Instalacja w LXC

```bash
# Aktualizacja systemu
apt update && apt upgrade -y

# Instalacja zależności
apt install -y python3 python3-pip python3-venv postgresql nginx nodejs npm git

# PostgreSQL
sudo -u postgres createuser baltyk
sudo -u postgres createdb baltyk -O baltyk
sudo -u postgres psql -c "ALTER USER baltyk WITH PASSWORD 'baltyk';"

# Aplikacja
cd /opt
git clone https://github.com/your-repo/stw-baltyk.git baltyk
cd baltyk

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

cp .env.example .env
# Edytuj .env - ustaw DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY

flask init-db
flask seed-demo

# Frontend build
cd ../frontend
npm install
npm run build

# Nginx config
cat > /etc/nginx/sites-available/baltyk << 'EOF'
server {
    listen 80;
    server_name baltyk.lan;

    location / {
        root /opt/baltyk/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/baltyk /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Gunicorn service
cat > /etc/systemd/system/baltyk.service << 'EOF'
[Unit]
Description=STW Baltyk Flask API
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/opt/baltyk/backend
Environment="PATH=/opt/baltyk/backend/venv/bin"
ExecStart=/opt/baltyk/backend/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable baltyk
systemctl start baltyk
```

### Konfiguracja NPM i AdGuard

Na hoście Proxmox:

```bash
# NPM (LXC 108) - dodaj proxy host:
# baltyk.lan -> 192.168.88.XX:80

# AdGuard (LXC 103) - DNS rewrite:
# baltyk.lan -> 192.168.88.29
```

## Struktura projektu

```
stw/
├── backend/
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── api/         # Flask blueprints (REST endpoints)
│   │   ├── schemas/     # Marshmallow schemas
│   │   └── services/    # Business logic (bank import, matching)
│   ├── migrations/      # Alembic migrations
│   ├── config.py        # Flask configuration
│   ├── requirements.txt
│   └── run.py           # Application entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── hooks/       # Custom React hooks (React Query)
│   │   ├── services/    # API client (Axios)
│   │   └── types/       # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## API Endpoints

### Auth
- `POST /api/auth/login` - logowanie
- `POST /api/auth/refresh` - odświeżenie tokenu
- `POST /api/auth/logout` - wylogowanie
- `GET /api/auth/me` - dane zalogowanego użytkownika

### Członkowie
- `GET /api/members` - lista członków
- `POST /api/members` - dodaj członka
- `GET /api/members/:id` - szczegóły członka
- `PUT /api/members/:id` - edytuj członka
- `DELETE /api/members/:id` - usuń (soft delete)

### Składki
- `GET /api/fees` - lista składek
- `POST /api/fees` - dodaj składkę
- `POST /api/fees/generate` - wygeneruj składki dla wszystkich
- `POST /api/fees/:id/mark-paid` - oznacz jako opłaconą
- `GET /api/fees/types` - typy składek

### Finanse
- `GET /api/finance/transactions` - lista transakcji
- `POST /api/finance/transactions` - dodaj transakcję
- `POST /api/finance/import` - import wyciągu (upload file)
- `POST /api/finance/import/confirm` - potwierdź import
- `POST /api/finance/transactions/:id/match` - sparuj z członkiem
- `GET /api/finance/balance` - saldo

### Sprzęt
- `GET /api/equipment` - lista sprzętu
- `POST /api/equipment` - dodaj sprzęt
- `GET /api/equipment/reservations` - rezerwacje
- `POST /api/equipment/reservations` - nowa rezerwacja

### Wydarzenia
- `GET /api/events` - lista wydarzeń
- `POST /api/events` - dodaj wydarzenie
- `POST /api/events/:id/participants` - zapisz uczestnika
- `POST /api/events/:id/open-registration` - otwórz zapisy

### Raporty
- `GET /api/reports/dashboard` - dane dashboardu
- `GET /api/reports/fees?format=csv` - raport składek
- `GET /api/reports/overdue?format=csv` - raport zaległości
- `GET /api/reports/members?format=csv` - lista członków
- `GET /api/reports/finance?format=csv` - ewidencja finansowa

## Licencja

MIT License - użytek wewnętrzny STW Bałtyk Gdynia.
