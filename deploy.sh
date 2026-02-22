#!/bin/bash
# =============================================================================
# STW Baltyk Gdynia - Git-based Deployment Script
# =============================================================================
# Usage: ./deploy.sh [LXC_ID] [--setup|--quick|--db]
#
# Workflow:
#   1. Commits & pushes local changes to bare repo
#   2. LXC pulls latest changes from bare repo
#   3. Installs/updates Python dependencies
#   4. Restarts service
#
# Modes:
#   (default)     - Full deploy: push, pull, pip install, restart
#   --setup       - First-time setup (install deps, clone, configure services)
#   --quick       - Quick deploy: push, pull, restart (skip pip install)
#   --db          - Run Liquibase database migrations
#   --db-drop     - Drop and recreate database with Liquibase
#
# Examples:
#   ./deploy.sh              # Deploy to LXC 200 (default)
#   ./deploy.sh 200          # Deploy to specific LXC
#   ./deploy.sh 200 --setup  # First-time setup
#   ./deploy.sh --quick      # Quick restart without pip install
#   ./deploy.sh --db         # Run database migrations
# =============================================================================

set -e

# Configuration
LXC_ID="${1:-200}"
MODE="${2:-}"
TARGET_DIR="/opt/stw"
GIT_REPO="/mnt/git-repos/stw-baltyk.git"
LOCAL_REMOTE="local"

# Handle mode as first argument
if [[ "$LXC_ID" == "--"* ]]; then
    MODE="$LXC_ID"
    LXC_ID="200"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
log_step() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

# Header
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   STW Baltyk Gdynia - Git Deployment     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check if LXC exists
if ! pct status $LXC_ID &>/dev/null; then
    log_error "LXC $LXC_ID does not exist. Create it first."
fi

# Start LXC if not running
if [ "$(pct status $LXC_ID | grep -c running)" -eq 0 ]; then
    log_info "Starting LXC $LXC_ID..."
    pct start $LXC_ID
    sleep 5
fi

# Get LXC IP
IP=$(pct exec $LXC_ID -- hostname -I | awk '{print $1}')
log_info "Target: LXC $LXC_ID ($IP)"
log_info "Mode: ${MODE:-default}"

# ─────────────────────────────────────────────────────────────────────────────
# Ensure bare repo exists
# ─────────────────────────────────────────────────────────────────────────────
if [ ! -d "$GIT_REPO" ]; then
    log_step "Creating bare git repo"
    mkdir -p "$(dirname $GIT_REPO)"
    git init --bare "$GIT_REPO"
    log_success "Created $GIT_REPO"
fi

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Push local changes to bare repo
# ─────────────────────────────────────────────────────────────────────────────
log_step "Step 1: Push to bare repo"

cd /root/stw

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    git add -A
    git commit -m "Initial commit"
fi

# Add local remote if needed
if ! git remote get-url $LOCAL_REMOTE &>/dev/null; then
    git remote add $LOCAL_REMOTE "$GIT_REPO"
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    log_warn "Uncommitted changes detected. Committing..."
    git add -A
    git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')" --quiet || true
fi

# Push to local bare repo
git push $LOCAL_REMOTE main --quiet 2>/dev/null || git push $LOCAL_REMOTE main --force --quiet
log_success "Pushed to $LOCAL_REMOTE"

# ─────────────────────────────────────────────────────────────────────────────
# Database migrations (if --db or --db-drop)
# ─────────────────────────────────────────────────────────────────────────────
if [ "$MODE" = "--db" ] || [ "$MODE" = "--db-drop" ]; then
    log_step "Database migrations"

    # Pull latest code first
    pct exec $LXC_ID -- bash -c "
        cd $TARGET_DIR
        git config --global --add safe.directory $TARGET_DIR 2>/dev/null || true
        git fetch origin --quiet
        git reset --hard origin/main --quiet
    "

    if [ "$MODE" = "--db-drop" ]; then
        log_warn "Dropping and recreating database..."
        pct exec $LXC_ID -- bash -c "cd $TARGET_DIR/backend/db && ./install-db.sh --drop"
    else
        pct exec $LXC_ID -- bash -c "cd $TARGET_DIR/backend/db && ./install-db.sh"
    fi

    log_success "Database migrations complete!"
    exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: First-time setup (if --setup)
# ─────────────────────────────────────────────────────────────────────────────
if [ "$MODE" = "--setup" ]; then
    log_step "Step 2: First-time setup"

    # Ensure DNS works
    log_info "Configuring DNS..."
    pct exec $LXC_ID -- bash -c "grep -q '8.8.8.8' /etc/resolv.conf || echo 'nameserver 8.8.8.8' >> /etc/resolv.conf"

    # Install system dependencies
    log_info "Installing system packages..."
    pct exec $LXC_ID -- apt-get update -qq
    pct exec $LXC_ID -- apt-get install -y -qq \
        python3 python3-pip python3-venv git \
        postgresql postgresql-contrib \
        nginx curl default-jre-headless \
        > /dev/null

    # Configure git safe directory
    pct exec $LXC_ID -- git config --global --add safe.directory $GIT_REPO

    # Clone repository
    log_info "Cloning repository..."
    pct exec $LXC_ID -- rm -rf $TARGET_DIR
    pct exec $LXC_ID -- git clone $GIT_REPO $TARGET_DIR --quiet

    # Setup Python virtual environment
    log_info "Setting up Python environment..."
    pct exec $LXC_ID -- bash -c "
        cd $TARGET_DIR/backend
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip -q
        pip install -r requirements.txt -q
    "

    # Create PostgreSQL database
    log_info "Setting up PostgreSQL..."
    pct exec $LXC_ID -- bash -c "
        sudo -u postgres psql -c \"CREATE USER stw_user WITH PASSWORD 'STWBaltyk2026';\" 2>/dev/null || true
        sudo -u postgres psql -c \"CREATE DATABASE stw_baltyk OWNER stw_user;\" 2>/dev/null || true
        sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE stw_baltyk TO stw_user;\"
    "

    # Run Liquibase migrations
    log_info "Running database migrations..."
    pct exec $LXC_ID -- bash -c "cd $TARGET_DIR/backend/db && chmod +x install-db.sh && ./install-db.sh"

    # Create systemd service for Flask
    log_info "Creating Flask systemd service..."
    pct exec $LXC_ID -- bash -c "cat > /etc/systemd/system/stw-baltyk.service << 'EOF'
[Unit]
Description=STW Baltyk Gdynia - Flask Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=root
Group=root
WorkingDirectory=/opt/stw/backend
Environment=\"PATH=/opt/stw/backend/venv/bin\"
EnvironmentFile=-/opt/stw/backend/.env
ExecStart=/opt/stw/backend/venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/stw-baltyk/access.log \
    --error-logfile /var/log/stw-baltyk/error.log \
    --capture-output \
    \"run:create_app()\"

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

    # Create log directory
    pct exec $LXC_ID -- mkdir -p /var/log/stw-baltyk

    # Create nginx config
    log_info "Configuring nginx..."
    pct exec $LXC_ID -- bash -c "cat > /etc/nginx/sites-available/stw-baltyk << 'EOF'
server {
    listen 80;
    server_name baltyk.lan stw.lan;

    root /opt/stw/frontend/dist;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /assets {
        expires 1y;
        add_header Cache-Control \"public, immutable\";
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF"

    pct exec $LXC_ID -- ln -sf /etc/nginx/sites-available/stw-baltyk /etc/nginx/sites-enabled/
    pct exec $LXC_ID -- rm -f /etc/nginx/sites-enabled/default
    pct exec $LXC_ID -- nginx -t
    pct exec $LXC_ID -- systemctl restart nginx

    # Enable and start services
    pct exec $LXC_ID -- systemctl daemon-reload
    pct exec $LXC_ID -- systemctl enable stw-baltyk --quiet
    pct exec $LXC_ID -- systemctl start stw-baltyk

    log_success "First-time setup complete!"

else
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: Pull changes in LXC
    # ─────────────────────────────────────────────────────────────────────────
    log_step "Step 2: Pull changes"

    pct exec $LXC_ID -- bash -c "
        cd $TARGET_DIR
        git config --global --add safe.directory $TARGET_DIR 2>/dev/null || true
        git fetch origin --quiet
        git reset --hard origin/main --quiet
    "
    log_success "Code updated"

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: Install dependencies (unless --quick)
    # ─────────────────────────────────────────────────────────────────────────
    if [ "$MODE" != "--quick" ]; then
        log_step "Step 3: Install dependencies"

        pct exec $LXC_ID -- bash -c "
            cd $TARGET_DIR/backend
            source venv/bin/activate
            pip install -r requirements.txt -q 2>&1 | grep -v WARNING || true
        "
        log_success "Dependencies installed"
    fi

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4: Restart service
    # ─────────────────────────────────────────────────────────────────────────
    log_step "Step 4: Restart service"
    pct exec $LXC_ID -- systemctl restart stw-baltyk
    sleep 2

    # Check status
    if pct exec $LXC_ID -- systemctl is-active stw-baltyk &>/dev/null; then
        log_success "Service running"
    else
        log_error "Service failed! Check: pct exec $LXC_ID -- journalctl -u stw-baltyk -n 50"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Deployment Complete!              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Verify deployment
HEALTH=$(pct exec $LXC_ID -- curl -s http://localhost/api/health 2>/dev/null || echo "{}")
if echo "$HEALTH" | grep -q '"status"'; then
    echo -e "  ${GREEN}✓${NC} STW Baltyk API is running"
else
    echo -e "  ${YELLOW}⚠${NC} Health check pending..."
fi

echo ""
echo "  Web UI:  http://$IP or http://baltyk.lan"
echo ""
echo "  Commands:"
echo "    Logs:    pct exec $LXC_ID -- journalctl -u stw-baltyk -f"
echo "    Status:  pct exec $LXC_ID -- systemctl status stw-baltyk"
echo "    DB:      ./deploy.sh --db"
echo ""
