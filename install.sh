#!/bin/bash

set -Eeuo pipefail

PROJECT_NAME="Homescanner"
VENV_DIR="venv"
PYTHON_VERSION_REQUIRED="3.8"
REQUIREMENTS_FILE="requirements.txt"
CONFIG_PLACEHOLDER="config/config.yml"
LOG_FILE="setup.log"

log() {
  local level="$1"
  local message="$2"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$LOG_FILE"
}

header() {
  echo "=================================================="
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$PROJECT_NAME Setup]"
  echo "=================================================="
}

check_command() {
  if ! command -v "$1" &>/dev/null; then
    log "ERROR" "Missing required command: $1"
    exit 1
  fi
}

check_python_version() {
  current=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
  required="$PYTHON_VERSION_REQUIRED"
  if [[ $(echo -e "$required\n$current" | sort -V | head -n1) != "$required" ]]; then
    log "ERROR" "Python $required or higher is required. Found: $current"
    exit 1
  fi
}

create_venv() {
  log "INFO" "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
}

upgrade_packages() {
  log "INFO" "Upgrading pip, setuptools, wheel..."
  pip install --upgrade pip setuptools wheel >>"$LOG_FILE" 2>&1
}

install_dependencies() {
  if [[ -f "$REQUIREMENTS_FILE" ]]; then
    log "INFO" "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE" >>"$LOG_FILE" 2>&1
  else
    log "WARN" "$REQUIREMENTS_FILE not found. Skipping pip installs."
  fi
}

create_directories() {
  log "INFO" "Creating project folders..."
  mkdir -p logs data config
}

generate_default_config() {
  if [[ ! -f "$CONFIG_PLACEHOLDER" ]]; then
    log "INFO" "Generating default config file..."
    cat <<EOF > "$CONFIG_PLACEHOLDER"
# Default detection rules placeholder
# Add YAML detection rules under the config/ directory.
EOF
  fi
}

create_gitignore() {
  if [[ ! -f ".gitignore" ]]; then
    log "INFO" "Adding default .gitignore..."
    cat <<EOF > .gitignore
$VENV_DIR/
__pycache__/
*.pyc
logs/
data/
EOF
  fi
}

show_summary() {
  echo ""
  echo "=================================================="
  echo "Homescanner environment is ready."
  echo "Activate with:"
  echo "  source $VENV_DIR/bin/activate"
  echo "Run the project with:"
  echo "  python main.py"
  echo "Logs saved to: $LOG_FILE"
  echo "=================================================="
}

main() {
  header
  check_command python3
  check_command pip3
  check_python_version
  create_venv
  upgrade_packages
  install_dependencies
  create_directories
  generate_default_config
  create_gitignore
  show_summary
}

main "$@"
