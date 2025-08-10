#!/bin/bash

# ObfusEngine Setup Script
# This script installs requirements and makes ObfusEngine globally accessible

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════╗
║         ObfusEngine Setup Script         ║
║              Version 1.0.0               ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root for global installation
if [[ $EUID -eq 0 ]]; then
    INSTALL_DIR="/opt/obfusengine"
    BIN_DIR="/usr/local/bin"
    print_status "Running as root - Installing globally"
else
    INSTALL_DIR="$HOME/.local/share/obfusengine"
    BIN_DIR="$HOME/.local/bin"
    print_status "Running as user - Installing locally"
    
    # Create local bin directory if it doesn't exist
    mkdir -p "$BIN_DIR"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_warning "$BIN_DIR is not in your PATH"
        echo "Add this line to your ~/.bashrc or ~/.zshrc:"
        echo "export PATH=\"$BIN_DIR:\$PATH\""
    fi
fi

print_status "Installation directory: $INSTALL_DIR"
print_status "Binary directory: $BIN_DIR"

# Get current directory (where ObfusEngine is located)
CURRENT_DIR=$(pwd)
OBFUS_SCRIPT="$CURRENT_DIR/ObfusEngine.py"

# Check if ObfusEngine.py exists
if [[ ! -f "$OBFUS_SCRIPT" ]]; then
    print_error "ObfusEngine.py not found in current directory!"
    print_error "Please run this script from the ObfusEngine directory"
    exit 1
fi

print_success "Found ObfusEngine.py"

# Check for Python 3
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    print_error "Please install Python 3 first"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
print_success "Python 3 found (version: $PYTHON_VERSION)"

# Check for pip and install if needed
print_status "Checking pip installation..."
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    print_warning "pip3 not found, attempting to install..."
    
    # Try to install pip
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-pip
    else
        print_error "Could not install pip automatically"
        print_error "Please install pip3 manually and run this script again"
        exit 1
    fi
    
    # Verify pip installation
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip installation failed!"
        exit 1
    fi
fi

print_success "pip found"

# Check for PowerShell Core
print_status "Checking PowerShell Core..."
if ! command -v pwsh &> /dev/null; then
    print_warning "PowerShell Core (pwsh) not found!"
    print_warning "Some obfuscation techniques require PowerShell Core"
    print_warning "Install it with: https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-linux"
else
    print_success "PowerShell Core found"
fi

# Detect if we're in an externally managed environment (PEP 668)
EXTERNALLY_MANAGED=false
if python3 -c "import sys; exit(0 if hasattr(sys, 'base_prefix') else 1)" 2>/dev/null; then
    if [ -f "/usr/lib/python*/EXTERNALLY-MANAGED" ] || [ -f "/usr/lib/python*/dist-packages/EXTERNALLY-MANAGED" ]; then
        EXTERNALLY_MANAGED=true
        print_warning "Detected externally managed Python environment (PEP 668)"
    fi
fi

# Check for pipx (preferred for externally managed environments)
PIPX_AVAILABLE=false
if command -v pipx &> /dev/null; then
    PIPX_AVAILABLE=true
    print_status "pipx found - will use for package installation"
elif $EXTERNALLY_MANAGED; then
    print_status "Installing pipx for externally managed environment..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y pipx
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-pipx
    elif command -v dnf &> /dev/null; then
        sudo dnf install pipx
    fi
    
    if command -v pipx &> /dev/null; then
        PIPX_AVAILABLE=true
        print_success "pipx installed"
    fi
fi

# Install Python requirements
print_status "Installing Python requirements..."

# Create requirements list (pathlib and argparse are built-in, removed)
REQUIREMENTS=(
    "rich"
    "pyperclip"
)

# Function to try system package installation first
install_system_package() {
    local req=$1
    local pkg_name=""
    
    case $req in
        "rich")
            pkg_name="python3-rich"
            ;;
        "pyperclip")
            pkg_name="python3-pyperclip"
            ;;
    esac
    
    if [[ -n "$pkg_name" ]]; then
        if command -v apt-get &> /dev/null; then
            if sudo apt-get install -y "$pkg_name" 2>/dev/null; then
                return 0
            fi
        elif command -v pacman &> /dev/null; then
            local arch_pkg=$(echo "$pkg_name" | sed 's/python3-/python-/')
            if sudo pacman -S --noconfirm "$arch_pkg" 2>/dev/null; then
                return 0
            fi
        elif command -v dnf &> /dev/null; then
            if sudo dnf install -y "$pkg_name" 2>/dev/null; then
                return 0
            fi
        fi
    fi
    return 1
}

for req in "${REQUIREMENTS[@]}"; do
    print_status "Installing $req..."
    
    # Check if already installed
    if python3 -c "import $req" 2>/dev/null; then
        print_success "$req already installed"
        continue
    fi
    
    # Try system package first (for Kali/Debian/Ubuntu)
    if install_system_package "$req"; then
        print_success "$req installed via system package manager"
        continue
    fi
    
    # For externally managed environments, try pipx or venv
    if $EXTERNALLY_MANAGED; then
        print_warning "Using alternative installation for externally managed environment..."
        
        # Create a virtual environment for ObfusEngine
        VENV_PATH="$INSTALL_DIR/venv"
        if [[ ! -d "$VENV_PATH" ]]; then
            print_status "Creating virtual environment..."
            python3 -m venv "$VENV_PATH"
        fi
        
        # Install in virtual environment
        if "$VENV_PATH/bin/pip" install "$req" --quiet; then
            print_success "$req installed in virtual environment"
            USE_VENV=true
            continue
        fi
        
        # Try with --break-system-packages as last resort
        print_warning "Trying with --break-system-packages (not recommended)..."
        if python3 -m pip install --user "$req" --break-system-packages --quiet; then
            print_success "$req installed (with --break-system-packages)"
            continue
        fi
    else
        # Standard installation methods for non-externally managed environments
        
        # Try primary method
        if python3 -m pip install --user "$req" --no-warn-script-location --quiet; then
            print_success "$req installed successfully"
            continue
        fi
        
        # Try alternative method
        if pip3 install --user "$req" --no-warn-script-location --quiet; then
            print_success "$req installed (alternative method)"
            continue
        fi
        
        # Try without --user flag (for virtual environments)
        if python3 -m pip install "$req" --quiet; then
            print_success "$req installed (system/venv method)"
            continue
        fi
    fi
    
    # All methods failed
    print_error "Failed to install $req"
    print_error ""
    print_error "Manual installation options:"
    print_error "1. System package: sudo apt install python3-$req"
    print_error "2. Virtual environment: python3 -m venv myenv && myenv/bin/pip install $req"
    print_error "3. Break system packages: python3 -m pip install --user $req --break-system-packages"
    print_error "4. Use pipx: pipx install $req"
    exit 1
done

# Create installation directory
print_status "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy ObfusEngine files
print_status "Copying ObfusEngine files..."
cp -r "$CURRENT_DIR"/* "$INSTALL_DIR/"
print_success "Files copied to $INSTALL_DIR"

# Make ObfusEngine.py executable
chmod +x "$INSTALL_DIR/ObfusEngine.py"

# Create wrapper script (handle virtual environment if used)
print_status "Creating global wrapper script..."

# Ensure BIN_DIR exists and is writable
if [[ ! -d "$BIN_DIR" ]]; then
    mkdir -p "$BIN_DIR" 2>/dev/null || {
        print_error "Cannot create directory $BIN_DIR"
        print_error "Try running with sudo for system-wide installation"
        exit 1
    }
fi

if [[ ! -w "$BIN_DIR" ]]; then
    print_error "No write permission to $BIN_DIR"
    print_error "Try running with sudo for system-wide installation"
    exit 1
fi

if [[ "$USE_VENV" == "true" ]]; then
    # Use virtual environment Python
    cat > "$BIN_DIR/obfusengine" << EOF
#!/bin/bash
# ObfusEngine Global Wrapper Script (with virtual environment)
cd "$INSTALL_DIR"
# Create a temporary script with the correct name for argparse
cp "$INSTALL_DIR/ObfusEngine.py" "/tmp/obfusengine.py" 2>/dev/null || true
if [[ -f "/tmp/obfusengine.py" ]]; then
    "$INSTALL_DIR/venv/bin/python" "/tmp/obfusengine.py" "\$@"
    rm -f "/tmp/obfusengine.py"
else
    "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/ObfusEngine.py" "\$@"
fi
EOF
    
    cat > "$BIN_DIR/obfus" << EOF
#!/bin/bash
# ObfusEngine Short Alias (with virtual environment)
cd "$INSTALL_DIR"
# Create a temporary script with the correct name for argparse
cp "$INSTALL_DIR/ObfusEngine.py" "/tmp/obfus.py" 2>/dev/null || true
if [[ -f "/tmp/obfus.py" ]]; then
    "$INSTALL_DIR/venv/bin/python" "/tmp/obfus.py" "\$@"
    rm -f "/tmp/obfus.py"
else
    "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/ObfusEngine.py" "\$@"
fi
EOF
else
    # Use system Python
    cat > "$BIN_DIR/obfusengine" << EOF
#!/bin/bash
# ObfusEngine Global Wrapper Script
cd "$INSTALL_DIR"
# Create a temporary script with the correct name for argparse
cp "$INSTALL_DIR/ObfusEngine.py" "/tmp/obfusengine.py" 2>/dev/null || true
if [[ -f "/tmp/obfusengine.py" ]]; then
    python3 "/tmp/obfusengine.py" "\$@"
    rm -f "/tmp/obfusengine.py"
else
    python3 "$INSTALL_DIR/ObfusEngine.py" "\$@"
fi
EOF
    
    cat > "$BIN_DIR/obfus" << EOF
#!/bin/bash
# ObfusEngine Short Alias
cd "$INSTALL_DIR"
# Create a temporary script with the correct name for argparse
cp "$INSTALL_DIR/ObfusEngine.py" "/tmp/obfus.py" 2>/dev/null || true
if [[ -f "/tmp/obfus.py" ]]; then
    python3 "/tmp/obfus.py" "\$@"
    rm -f "/tmp/obfus.py"
else
    python3 "$INSTALL_DIR/ObfusEngine.py" "\$@"
fi
EOF
fi

# Make wrapper executable
chmod +x "$BIN_DIR/obfusengine" 2>/dev/null || {
    print_error "Cannot make $BIN_DIR/obfusengine executable"
    exit 1
}

chmod +x "$BIN_DIR/obfus" 2>/dev/null || {
    print_error "Cannot make $BIN_DIR/obfus executable"
    exit 1
}

print_success "Global wrapper created at $BIN_DIR/obfusengine"
print_success "Short alias 'obfus' created"

# Final verification with better error handling and debugging
print_status "Verifying installation..."

# Debug information
print_status "Debug information:"
echo "  BIN_DIR: $BIN_DIR"
echo "  INSTALL_DIR: $INSTALL_DIR"
echo "  obfusengine exists: $(test -f "$BIN_DIR/obfusengine" && echo "YES" || echo "NO")"
echo "  obfusengine executable: $(test -x "$BIN_DIR/obfusengine" && echo "YES" || echo "NO")"

if [[ -f "$BIN_DIR/obfusengine" ]]; then
    if [[ -x "$BIN_DIR/obfusengine" ]]; then
        print_success "ObfusEngine installed successfully!"
        echo ""
        print_status "Usage:"
        echo "  obfusengine          # Run interactively"
        echo "  obfus               # Short alias"
        echo "  obfusengine --help  # Show help"
        echo ""
        
        # Test if it's in PATH
        if command -v obfusengine &> /dev/null; then
            print_success "ObfusEngine is globally accessible!"
            echo ""
            print_status "Try running: obfusengine"
        else
            print_warning "ObfusEngine installed but may not be in PATH"
            if [[ $EUID -ne 0 ]]; then
                echo ""
                print_status "To add to PATH, run one of these commands:"
                echo "echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
                echo "echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
                echo ""
                print_status "Or run directly with full path: $BIN_DIR/obfusengine"
            fi
        fi
    else
        print_error "Installation file exists but is not executable!"
        print_error "Run: chmod +x $BIN_DIR/obfusengine"
        exit 1
    fi
else
    print_error "Installation file not created!"
    print_error "Check write permissions to $BIN_DIR"
    print_error "Current user: $(whoami)"
    print_error "Directory permissions: $(ls -ld "$BIN_DIR" 2>/dev/null || echo "Directory does not exist")"
    
    if [[ $EUID -ne 0 ]] && [[ "$BIN_DIR" == "/usr/local/bin" ]]; then
        print_error "Try running with sudo for global installation:"
        print_error "sudo ./setup.sh"
    fi
    exit 1
fi

# Installation summary
echo ""
print_status "Installation Summary:"
echo "  Installation Path: $INSTALL_DIR"
echo "  Binary Path: $BIN_DIR/obfusengine"
echo "  Alias Path: $BIN_DIR/obfus"
echo ""
print_success "Setup completed successfully!"

# Optional: Run a quick test
echo ""
read -p "Do you want to test the installation? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Testing installation..."
    if "$BIN_DIR/obfusengine" --version &> /dev/null; then
        print_success "Installation test passed!"
    else
        print_warning "Installation test failed - but files are installed"
    fi
fi

print_success "ObfusEngine is ready to use!"