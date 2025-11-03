#!/bin/bash
# BM-AI Docker Management Script
# Description: Manage BM-AI services (Backend + Qdrant) with Docker

set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ────────────────────────────────────────────────
# 🔹 Color Definitions & Logging
# ────────────────────────────────────────────────
declare -A COLORS=(
  [RED]='\033[0;31m' [GREEN]='\033[0;32m'
  [YELLOW]='\033[1;33m' [BLUE]='\033[0;34m' [NC]='\033[0m'
)

log() {
  local color="$1"; shift
  echo -e "${color}$*${COLORS[NC]}"
}

# ────────────────────────────────────────────────
# 🔹 Checks
# ────────────────────────────────────────────────
check_docker() {
  if ! docker ps >/dev/null 2>&1; then
    log "${COLORS[RED]}" "[ERROR] Docker is not running. Please start Docker and try again."
    exit 1
  fi
}

check_env() {
  local env_file="$SCRIPT_DIR/backend/.env"
  local env_docker="$SCRIPT_DIR/backend/.env.docker"
  
  if [[ ! -f "$env_file" ]]; then
    if [[ -f "$env_docker" ]]; then
      log "${COLORS[YELLOW]}" "[WARN] .env not found — creating from .env.docker"
      cp "$env_docker" "$env_file"
    else
      log "${COLORS[RED]}" "[ERROR] No .env or .env.docker found in backend/ directory."
      exit 1
    fi
  fi

  if ! grep -q "GOOGLE_API_KEY=" "$env_file"; then
    log "${COLORS[YELLOW]}" "[WARN] Missing GOOGLE_API_KEY in .env — please add it manually."
  fi
}

# ────────────────────────────────────────────────
# 🔹 Commands
# ────────────────────────────────────────────────
start_services() {
  check_docker
  check_env

  local build_flag="--build"
  [[ "${2:-}" == "--no-build" ]] && build_flag=""

  log "${COLORS[BLUE]}" "[INFO] Starting BM-AI services..."
  (cd "$SCRIPT_DIR" && docker compose up -d $build_flag --remove-orphans)
  log "${COLORS[GREEN]}" "[SUCCESS] Services started!"

  echo ""
  log "${COLORS[BLUE]}" "Backend: http://localhost:8000"
  log "${COLORS[BLUE]}" "API Docs: http://localhost:8000/docs"
  log "${COLORS[BLUE]}" "Qdrant:  http://localhost:6333/dashboard"

  (cd "$SCRIPT_DIR" && docker compose logs -f --tail=50)
}

stop_services() {
  log "${COLORS[BLUE]}" "[INFO] Stopping services..."
  (cd "$SCRIPT_DIR" && docker compose down)
  log "${COLORS[GREEN]}" "[SUCCESS] Services stopped."
}

restart_services() {
  stop_services
  start_services
}

show_status() {
  check_docker
  log "${COLORS[BLUE]}" "[INFO] Service status:"
  (cd "$SCRIPT_DIR" && docker compose ps)
  echo ""

  log "${COLORS[BLUE]}" "[INFO] Health checks:"
  curl -fsS http://localhost:8000/health >/dev/null && \
    log "${COLORS[GREEN]}" "Backend API: ✅ Running" || \
    log "${COLORS[RED]}" "Backend API: ❌ Not responding"

  curl -fsS http://localhost:6333/health >/dev/null && \
    log "${COLORS[GREEN]}" "Qdrant: ✅ Running" || \
    log "${COLORS[RED]}" "Qdrant: ❌ Not responding"
}

show_logs() {
  local service="${2:-}"
  if [[ -n "$service" ]]; then
    (cd "$SCRIPT_DIR" && docker compose logs -f --tail=50 "$service")
  else
    (cd "$SCRIPT_DIR" && docker compose logs -f --tail=50)
  fi
}

cleanup() {
  if [[ "${2:-}" != "--force" ]]; then
    read -r -p "⚠️  This will remove all containers and volumes. Continue? (y/N): " confirm
    [[ "$confirm" =~ ^[yY]$ ]] || { log "${COLORS[YELLOW]}" "[INFO] Cleanup cancelled."; return; }
  fi

  log "${COLORS[BLUE]}" "[INFO] Cleaning up..."
  (cd "$SCRIPT_DIR" && docker compose down -v --remove-orphans)
  docker system prune -f
  log "${COLORS[GREEN]}" "[SUCCESS] Cleanup complete."
}

setup_env() {
  local env_file="$SCRIPT_DIR/backend/.env"
  local env_docker="$SCRIPT_DIR/backend/.env.docker"
  
  if [[ -f "$env_file" ]]; then
    cp "$env_file" "${env_file}.backup"
    log "${COLORS[YELLOW]}" "[WARN] Existing .env backed up to ${env_file}.backup"
  fi
  
  if [[ -f "$env_docker" ]]; then
    cp "$env_docker" "$env_file"
    log "${COLORS[GREEN]}" "[SUCCESS] .env created from template"
  else
    log "${COLORS[RED]}" "[ERROR] .env.docker not found in backend/ directory"
    exit 1
  fi
}

show_help() {
  cat <<EOF
BM-AI Docker Management
--------------------------------
Usage: $0 <command> [options]

Commands:
  start [--no-build]   Start all services (Backend + Qdrant)
  stop                 Stop all running containers
  restart              Restart services
  status               Show service status and health
  logs [service]       Tail logs (optionally specify a service)
  cleanup [--force]    Remove containers, volumes, and prune system
  setup                Copy .env.docker to .env in backend directory
  help, -h, --help     Show this help message

Examples:
  $0 start
  $0 start --no-build
  $0 logs backend
  $0 cleanup --force

Note: Run this script from the project root directory.
EOF
}

# ────────────────────────────────────────────────
# 🔹 Main CLI Entry
# ────────────────────────────────────────────────
case "${1:-}" in
  start) start_services "$@" ;;
  stop) stop_services ;;
  restart) restart_services ;;
  status) show_status ;;
  logs) show_logs "$@" ;;
  cleanup) cleanup "$@" ;;
  setup) setup_env ;;
  help|-h|--help|"") show_help ;;
  *)
    log "${COLORS[RED]}" "[ERROR] Unknown command: $1"
    show_help
    exit 1
    ;;
esac
