#!/bin/bash

set -Eeuo pipefail

PROJECT_NAME="Homescanner"
VENV_DIR="venv"
PYTHON_VERSION_REQUIRED="3.8"
REQUIREMENTS_FILE="requirements.txt"
CONFIG_PLACEHOLDER="config/config.yml"
LOG_FILE="setup.log"
PYTHON_EXEC="python3"

log() {
  local level="$1"
  local message="$2"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

header() {
  echo ""
  echo "=================================================="
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$PROJECT_NAME SETUP START]"
  echo "=================================================="
}

check_command() {
  if ! command -v "$1" &>/dev/null; then
    log "ERROR" "Missing required command: $1"
    exit 1
  fi
}

check_python_version() {
  local version
  version=$($PYTHON_EXEC -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
  if [[ $(printf '%s\n' "$PYTHON_VERSION_REQUIRED" "$version" | sort -V | head -n1) != "$PYTHON_VERSION_REQUIRED" ]]; then
    log "ERROR" "Python $PYTHON_VERSION_REQUIRED or higher is required. Found: $version"
    exit 1
  fi
  log "INFO" "Python version check passed ($version)"
}

create_virtualenv() {
  log "INFO" "Creating virtual environment in $VENV_DIR..."
  $PYTHON_EXEC -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  log "INFO" "Virtual environment activated."
}

upgrade_core_packages() {
  log "INFO" "Upgrading pip, setuptools, wheel..."
  pip install --quiet --upgrade pip setuptools wheel
}

install_project_dependencies() {
  if [[ -f "$REQUIREMENTS_FILE" ]]; then
    log "INFO" "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install --quiet -r "$REQUIREMENTS_FILE"
    log "INFO" "Dependencies installed."
  else
    log "WARN" "No $REQUIREMENTS_FILE found. Skipping dependency install."
  fi
}

prepare_directories() {
  log "INFO" "Creating required directories..."
  mkdir -p logs data config
}

generate_default_config() {
  if [[ ! -f "$CONFIG_PLACEHOLDER" ]]; then
    log "INFO" "Generating default config file..."
    cat <<EOF > "$CONFIG_PLACEHOLDER"
# config/config.yml
# Placeholder for detection rules configuration.
EOF
  fi
}

create_gitignore() {
  if [[ ! -f ".gitignore" ]]; then
    log "INFO" "Creating .gitignore file..."
    cat <<EOF > .gitignore
$VENV_DIR/
__pycache__/
*.pyc
logs/
data/
config/*.yml
*.log
EOF
  fi
}

final_summary() {
  echo ""
  echo "=================================================="
  echo "✅ Setup complete. Environment is ready."
  echo "Activate environment with:"
  echo "  source $VENV_DIR/bin/activate"
  echo "Run Homescanner with:"
  echo "  python main.py"
  echo "Log output is recorded in: $LOG_FILE"
  echo "=================================================="
}

main() {
  header
  check_command "$PYTHON_EXEC"
  check_command pip3
  check_python_version
  create_virtualenv
  upgrade_core_packages
  install_project_dependencies
  prepare_directories
  generate_default_config
  create_gitignore
  final_summary
}

main "$@"
