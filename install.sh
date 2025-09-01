#!/bin/bash

# Installer script for bot_social_network

# --- Configuration ---
# Default values, can be overridden by prompts or test mode
INSTALL_DIR=$(pwd)
ENV_TYPE="venv"
BIN_DIR=""

# --- Main Execution ---
if [ "$1" == "--test" ]; then
  echo "INFO: Running in non-interactive test mode."
  INSTALL_DIR="/tmp/bot_social_network_install/project"
  BIN_DIR="/tmp/bot_social_network_bin"
  ENV_TYPE="venv"
  # Clean up previous test runs
  rm -rf "/tmp/bot_social_network_install" "/tmp/bot_social_network_bin"
  mkdir -p "$INSTALL_DIR"
  mkdir -p "$BIN_DIR"
else
  # --- Interactive Prompts ---
  read -p "Enter installation directory [$(pwd)]: " USER_INSTALL_DIR
  INSTALL_DIR=${USER_INSTALL_DIR:-$(pwd)}

  echo "Select Python environment type:"
  echo "  1. Python venv (recommended)"
  echo "  2. Micromamba"
  echo "  3. Use base Python environment (not recommended)"
  read -p "Enter your choice (1-3): " ENV_CHOICE
  case "$ENV_CHOICE" in
    1) ENV_TYPE="venv" ;;
    2) ENV_TYPE="micromamba" ;;
    3) ENV_TYPE="base" ;;
    *)
      echo "Invalid choice. Defaulting to Python venv."
      ENV_TYPE="venv"
      ;;
  esac

  # Detect a suitable bin directory
  if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    DEFAULT_BIN_DIR="$HOME/.local/bin"
  elif [ -d "$HOME/bin" ] && [[ ":$PATH:" == *":$HOME/bin:"* ]]; then
    DEFAULT_BIN_DIR="$HOME/bin"
  else
    DEFAULT_BIN_DIR=""
  fi

  if [ -n "$DEFAULT_BIN_DIR" ]; then
    read -p "Create a symlink in $DEFAULT_BIN_DIR for easy access? [y/N]: " CREATE_SYMLINK
    if [[ "$CREATE_SYMLINK" =~ ^[Yy]$ ]]; then
      BIN_DIR="$DEFAULT_BIN_DIR"
    fi
  else
    echo "Could not find a standard user bin directory in your PATH."
    echo "You will need to run the application from the installation directory."
  fi
fi

# --- Ollama Check ---
echo "---"
echo "INFO: Checking for Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed. You can use local models."
else
    echo "⚠️ Ollama not found."
    echo "   To use local AI models, please install Ollama from https://ollama.com"
fi
echo "---"

set -e

VENV_DIR="$INSTALL_DIR/venv"
PROJECT_ROOT=$(pwd)

# --- Copy Project Files (if installing to a new directory) ---
if [ "$INSTALL_DIR" != "$PROJECT_ROOT" ]; then
  echo "INFO: Copying project files to $INSTALL_DIR..."
  rsync -a --exclude='.git' --exclude='*.tmp' --exclude='tests' "$PROJECT_ROOT/" "$INSTALL_DIR/"
fi

cd "$INSTALL_DIR"

# --- Environment Setup ---
case "$ENV_TYPE" in
  "venv")
    echo "INFO: Creating Python venv environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    ;;
  "micromamba")
    if ! command -v micromamba &> /dev/null; then
      echo "ERROR: Micromamba is not installed. Please install it and run this script again."
      exit 1
    fi
    echo "INFO: Creating Micromamba environment..."
    micromamba create -p "$VENV_DIR" python=3.10 -y
    micromamba activate "$VENV_DIR"
    ;;
  "base")
    echo "INFO: Using base Python environment."
    ;;
esac

# --- Dependency Installation ---
echo "INFO: Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# --- Make main script executable ---
chmod +x main.py

# --- Symlink ---
if [ -n "$BIN_DIR" ]; then
  echo "INFO: Creating symlink..."
  ln -sf "$INSTALL_DIR/main.py" "$BIN_DIR/bot-social-network"
fi

# --- Verification ---
if [ -n "$BIN_DIR" ]; then
  echo "INFO: Verifying installation..."
  if [ -f "$BIN_DIR/bot-social-network" ]; then
    echo "SUCCESS: Symlink created at $BIN_DIR/bot-social-network"
  else
    echo "ERROR: Symlink creation failed."
    exit 1
  fi

  if [ -x "$BIN_DIR/bot-social-network" ] && [ "$(readlink -f "$BIN_DIR/bot-social-network")" == "$INSTALL_DIR/main.py" ]; then
    echo "SUCCESS: Symlink is valid and executable."
  else
    echo "ERROR: Symlink is invalid or not executable."
  fi
fi

echo "INFO: Installation complete."
if [ -n "$BIN_DIR" ]; then
  echo "You can now run the application by typing: bot-social-network"
else
  echo "To run the application, navigate to the installation directory ($INSTALL_DIR) and run: python3 main.py"
fi
