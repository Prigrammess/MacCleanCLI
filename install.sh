#!/bin/bash

# macOS Cleaner Installation Script
# This script helps set up the macOS Cleaner application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Header
print_color "$BLUE" "================================================"
print_color "$BLUE" "       macOS Cleaner Installation Script        "
print_color "$BLUE" "================================================"
echo

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_color "$RED" "Error: This application is designed for macOS only."
    exit 1
fi

# Check Python version
print_color "$YELLOW" "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.10"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        print_color "$GREEN" "✓ Python $PYTHON_VERSION found"
    else
        print_color "$RED" "Error: Python 3.10 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_color "$RED" "Error: Python 3 is not installed."
    echo "Please install Python 3.10 or higher from https://www.python.org"
    exit 1
fi

# Check if pip is installed
print_color "$YELLOW" "Checking pip..."
if ! python3 -m pip --version &> /dev/null; then
    print_color "$RED" "Error: pip is not installed."
    echo "Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi
print_color "$GREEN" "✓ pip is installed"

# Create virtual environment
print_color "$YELLOW" "Creating virtual environment..."
if [ -d "venv" ]; then
    read -p "Virtual environment already exists. Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi
print_color "$GREEN" "✓ Virtual environment created"

# Activate virtual environment
print_color "$YELLOW" "Activating virtual environment..."
source venv/bin/activate
print_color "$GREEN" "✓ Virtual environment activated"

# Upgrade pip
print_color "$YELLOW" "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_color "$GREEN" "✓ pip upgraded"

# Install dependencies
print_color "$YELLOW" "Installing dependencies..."
pip install -r requirements.txt
print_color "$GREEN" "✓ Dependencies installed"

# Install the application
print_color "$YELLOW" "Installing macOS Cleaner..."
pip install -e .
print_color "$GREEN" "✓ macOS Cleaner installed"

# Create necessary directories
print_color "$YELLOW" "Creating application directories..."
mkdir -p ~/.macos-cleaner/{logs,backups}
print_color "$GREEN" "✓ Directories created"

# Create default configuration if it doesn't exist
if [ ! -f ~/.macos-cleaner/config.json ]; then
    print_color "$YELLOW" "Creating default configuration..."
    python3 -c "from utils.config import Config; Config().save_to_file(Config.DEFAULT_CONFIG_FILE)"
    print_color "$GREEN" "✓ Default configuration created"
fi

# Create command line shortcuts
print_color "$YELLOW" "Setting up command line shortcuts..."
if [ -d "/usr/local/bin" ]; then
    # Create wrapper scripts
    cat > macos-cleaner-wrapper.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"
python "$SCRIPT_DIR/main.py" "$@"
EOF

    chmod +x macos-cleaner-wrapper.sh

    # Create symlinks
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$(pwd)/macos-cleaner-wrapper.sh" /usr/local/bin/macos-cleaner
        ln -sf "$(pwd)/macos-cleaner-wrapper.sh" /usr/local/bin/mclean
        print_color "$GREEN" "✓ Command line shortcuts created"
        print_color "$GREEN" "  You can now use 'macos-cleaner' or 'mclean' from anywhere"
    else
        print_color "$YELLOW" "⚠ Cannot create global shortcuts (no write permission to /usr/local/bin)"
        print_color "$YELLOW" "  Run with sudo or use './macos-cleaner-wrapper.sh' directly"
    fi
fi

# Success message
echo
print_color "$GREEN" "================================================"
print_color "$GREEN" "     Installation completed successfully!       "
print_color "$GREEN" "================================================"
echo
print_color "$BLUE" "To run macOS Cleaner:"
print_color "$BLUE" "  1. From this directory: python main.py"
print_color "$BLUE" "  2. From anywhere: macos-cleaner or mclean"
print_color "$BLUE" "  3. With make: make run"
echo
print_color "$YELLOW" "First time users should run:"
print_color "$YELLOW" "  macos-cleaner --scan-only"
echo
print_color "$BLUE" "For help and documentation:"
print_color "$BLUE" "  - See README.md"
print_color "$BLUE" "  - See QUICKSTART.md"
print_color "$BLUE" "  - Run: macos-cleaner --help"
echo

# Ask if user wants to run now
read -p "Would you like to run macOS Cleaner now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python main.py
fi