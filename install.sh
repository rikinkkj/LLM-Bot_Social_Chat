#!/bin/bash

# Installer script for bot_social_network
# - Detects OS and package manager
# - Checks for system-level dependencies
# - Offers to install missing dependencies
# - Sets up the application in a chosen directory

set -e # Exit immediately if a command exits with a non-zero status.

# --- Globals ---
INSTALL_DIR=$(pwd)
ENV_TYPE="venv"
BIN_DIR=""
OS_ID=""
PACKAGE_MANAGER=""
INSTALL_CMD=""
PYTHON_DEV_PKG=""
BUILD_ESSENTIALS_PKG=""
PYGAME_DEPS_PKG=""
SUDO_CMD="sudo"

# --- Helper Functions ---

show_help() {
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "This script installs the Bot Social Network application."
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help    Show this help message and exit."
}

if [[ " $1 " == " -h " ]] || [[ " $1 " == " --help " ]]; then
    show_help
    exit 0
fi

# Function to print a formatted header
print_header() {
    echo "================================================="
    echo " $1"
    echo "================================================="
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    SUDO_CMD=""
fi

# Function to detect the OS and set package manager variables
detect_os() {
    print_header "Detecting Operating System"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_ID=$ID
        echo "Detected OS: $NAME"
    else
        echo "Cannot determine OS. Exiting."
        exit 1
    fi

    case "$OS_ID" in
        ubuntu|debian|mint)
            PACKAGE_MANAGER="apt"
            INSTALL_CMD="$SUDO_CMD apt-get install -y"
            PYTHON_DEV_PKG="python3-dev"
            BUILD_ESSENTIALS_PKG="build-essential"
            PYGAME_DEPS_PKG="libsdl2-dev"
            ;; 
        fedora|centos|rhel)
            PACKAGE_MANAGER="dnf"
            INSTALL_CMD="$SUDO_CMD dnf install -y"
            PYTHON_DEV_PKG="python3-devel"
            BUILD_ESSENTIALS_PKG="Development Tools"
            PYGAME_DEPS_PKG="SDL2-devel"
            ;; 
        arch)
            PACKAGE_MANAGER="pacman"
            INSTALL_CMD="$SUDO_CMD pacman -S --noconfirm"
            PYTHON_DEV_PKG="python"
            BUILD_ESSENTIALS_PKG="base-devel"
            PYGAME_DEPS_PKG="sdl2"
            ;; 
        *)
            echo "Unsupported Linux distribution: $OS_ID"
            echo "This script supports Debian/Ubuntu, Fedora/CentOS, and Arch based systems."
            exit 1
            ;; 
    esac
    echo "Package manager: $PACKAGE_MANAGER"
}

# Function to check for a command's existence
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ ERROR: Command '$1' not found."
        return 1
    fi
    echo "✅ $1 is installed."
    return 0
}

# Function to check for a package's installation
check_package() {
    local pkg_name=$1
    local friendly_name=$2
    local is_installed=false

    case "$PACKAGE_MANAGER" in
        apt)
            if dpkg -l | grep -q "^ii  $pkg_name"; then is_installed=true; fi
            ;; 
        dnf)
            if rpm -q "$pkg_name" &> /dev/null; then is_installed=true; fi
            ;; 
        pacman)
            if pacman -Q "$pkg_name" &> /dev/null; then is_installed=true; fi
            ;; 
    esac

    if $is_installed;
    then
        echo "✅ $friendly_name ($pkg_name) is installed."
        return 0
    else
        echo "⚠️  $friendly_name ($pkg_name) is NOT installed."
        return 1
    fi
}

# Main dependency check function
check_dependencies() {
    print_header "Checking System Dependencies"
    
    local missing_packages=()
    
    check_command "python3" || { echo "Python 3 is required. Please install it and run this script again."; exit 1; }
    check_command "pip" || { echo "pip is required. Please install it and run this script again."; exit 1; }
    check_command "git" || { echo "git is required. Please install it and run this script again."; exit 1; }
    if [ -n "$SUDO_CMD" ]; then
        check_command "sudo" || { echo "sudo is required to install packages. Please install it and run this script again."; exit 1; }
    fi

    check_package "$PYTHON_DEV_PKG" "Python Development Headers" || missing_packages+=("$PYTHON_DEV_PKG")
    check_package "$BUILD_ESSENTIALS_PKG" "Build Tools" || missing_packages+=("$BUILD_ESSENTIALS_PKG")
    check_package "$PYGAME_DEPS_PKG" "Pygame Audio Dependencies" || missing_packages+=("$PYGAME_DEPS_PKG")

    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo ""
        echo "The following system packages are required but are not installed:"
        for pkg in "${missing_packages[@]}"; do
            echo "  - $pkg"
        done
        echo ""
        read -p "Would you like to attempt to install them now? (y/N): " INSTALL_MISSING
        if [[ "$INSTALL_MISSING" =~ ^[Yy]$ ]]; then
            echo "Installing missing packages..."
            if [ "$PACKAGE_MANAGER" == "dnf" ] && [[ " ${missing_packages[@]} " =~ " Development Tools " ]]; then
                $SUDO_CMD dnf groupinstall -y "Development Tools"
                # Remove it from the list to avoid installing it twice
                missing_packages=("${missing_packages[@]/"Development Tools"}")
            fi
            if [ ${#missing_packages[@]} -gt 0 ]; then
                $INSTALL_CMD "${missing_packages[@]}"
            fi
        else
            echo "Installation cancelled. Please install the missing packages manually and run this script again."
            exit 1
        fi
    else
        echo "All system dependencies are satisfied."
    fi
}


# --- Main Execution ---
detect_os
check_dependencies

print_header "Application Setup"

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
if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" == ":$HOME/.local/bin:" ]]; then
    DEFAULT_BIN_DIR="$HOME/.local/bin"
elif [ -d "$HOME/bin" ] && [[ ":$PATH:" == ":$HOME/bin:" ]]; then
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

VENV_DIR="$INSTALL_DIR/venv"
PROJECT_ROOT=$(pwd)

# --- Copy Project Files (if installing to a new directory) ---
if [ "$INSTALL_DIR" != "$PROJECT_ROOT" ]; then
  echo "INFO: Copying project files to $INSTALL_DIR..."
  rsync -a --exclude='.git' --exclude='*.tmp' --exclude='tests' --exclude='logs' "$PROJECT_ROOT/" "$INSTALL_DIR/"
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
echo "INFO: Installing Python packages from requirements.txt..."
pip install -r requirements.txt

# --- Make main script executable ---
chmod +x main.py

# --- Symlink ---
if [ -n "$BIN_DIR" ]; then
  echo "INFO: Creating symlink..."
  ln -sf "$INSTALL_DIR/main.py" "$BIN_DIR/bot-social-network"
fi

# --- Final Instructions ---
print_header "Installation Complete"
if [ -n "$BIN_DIR" ]; then
  echo "You can now run the application by typing: bot-social-network"
else
  echo "To run the application, navigate to the installation directory ($INSTALL_DIR) and run: python3 main.py"
fi
echo "Enjoy the simulation!"
