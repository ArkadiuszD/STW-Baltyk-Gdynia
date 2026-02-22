#!/bin/bash
# =============================================================================
# STW Baltyk Gdynia - Database Installation Script
# =============================================================================
# This script installs Liquibase and sets up the database schema.
#
# Usage:
#   ./install-db.sh              # Install/update database
#   ./install-db.sh --drop       # Drop and recreate database (DESTRUCTIVE!)
#   ./install-db.sh --status     # Show migration status
#   ./install-db.sh --rollback N # Rollback N changesets
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIQUIBASE_VERSION="4.25.1"
LIQUIBASE_DIR="/opt/liquibase"
POSTGRES_JDBC_VERSION="42.7.1"

# Database settings (can be overridden by environment variables)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-stw_baltyk}"
DB_USER="${DB_USER:-stw_user}"
DB_PASSWORD="${DB_PASSWORD:-STWBaltyk2026}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Liquibase is installed
install_liquibase() {
    if [[ -f "${LIQUIBASE_DIR}/liquibase" ]]; then
        log_info "Liquibase already installed at ${LIQUIBASE_DIR}"
        return 0
    fi

    log_info "Installing Liquibase ${LIQUIBASE_VERSION}..."

    # Install Java if not present
    if ! command -v java &> /dev/null; then
        log_info "Installing Java..."
        apt-get update && apt-get install -y default-jre-headless
    fi

    # Download and extract Liquibase
    mkdir -p "${LIQUIBASE_DIR}"
    cd /tmp
    wget -q "https://github.com/liquibase/liquibase/releases/download/v${LIQUIBASE_VERSION}/liquibase-${LIQUIBASE_VERSION}.tar.gz"
    tar -xzf "liquibase-${LIQUIBASE_VERSION}.tar.gz" -C "${LIQUIBASE_DIR}"
    rm "liquibase-${LIQUIBASE_VERSION}.tar.gz"

    # Download PostgreSQL JDBC driver
    log_info "Downloading PostgreSQL JDBC driver..."
    wget -q -O "${LIQUIBASE_DIR}/lib/postgresql-${POSTGRES_JDBC_VERSION}.jar" \
        "https://jdbc.postgresql.org/download/postgresql-${POSTGRES_JDBC_VERSION}.jar"

    # Make executable
    chmod +x "${LIQUIBASE_DIR}/liquibase"

    log_info "Liquibase installed successfully!"
}

# Run Liquibase command
run_liquibase() {
    local cmd="$1"
    shift

    cd "${SCRIPT_DIR}/liquibase"

    LIQUIBASE_PASSWORD="${DB_PASSWORD}" "${LIQUIBASE_DIR}/liquibase" \
        --url="jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        --username="${DB_USER}" \
        --password="${DB_PASSWORD}" \
        --changeLogFile="changelog/db.changelog-master.yaml" \
        "$cmd" "$@"
}

# Drop and recreate database
drop_database() {
    log_warn "This will DROP the database ${DB_NAME}!"
    read -p "Are you sure? Type 'yes' to confirm: " confirm

    if [[ "$confirm" != "yes" ]]; then
        log_info "Aborted."
        exit 0
    fi

    log_info "Dropping database ${DB_NAME}..."
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -d postgres << EOF
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
EOF
    log_info "Database recreated."
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (none)         Run database migrations"
    echo "  --drop         Drop and recreate database (DESTRUCTIVE!)"
    echo "  --status       Show migration status"
    echo "  --rollback N   Rollback N changesets"
    echo "  --validate     Validate changelog"
    echo "  --help         Show this help"
    echo ""
    echo "Environment variables:"
    echo "  DB_HOST        Database host (default: localhost)"
    echo "  DB_PORT        Database port (default: 5432)"
    echo "  DB_NAME        Database name (default: stw_baltyk)"
    echo "  DB_USER        Database user (default: stw_user)"
    echo "  DB_PASSWORD    Database password (default: STWBaltyk2026)"
}

# Main
main() {
    case "$1" in
        --drop)
            install_liquibase
            drop_database
            log_info "Running migrations..."
            run_liquibase update
            log_info "Database setup complete!"
            ;;
        --status)
            install_liquibase
            run_liquibase status
            ;;
        --rollback)
            if [[ -z "$2" ]]; then
                log_error "Please specify number of changesets to rollback"
                exit 1
            fi
            install_liquibase
            run_liquibase rollbackCount "$2"
            ;;
        --validate)
            install_liquibase
            run_liquibase validate
            ;;
        --help|-h)
            show_usage
            ;;
        "")
            install_liquibase
            log_info "Running database migrations..."
            run_liquibase update
            log_info "Database up to date!"
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
