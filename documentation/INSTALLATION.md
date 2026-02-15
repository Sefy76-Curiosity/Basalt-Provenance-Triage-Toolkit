# Installation Guide

Complete guide to installing Scientific Toolkit v2.0 on Windows, macOS, and Linux.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation](#detailed-installation)
   - [Windows](#windows)
   - [macOS](#macos)
   - [Linux](#linux)
4. [Installing Dependencies](#installing-dependencies)
5. [Verifying Installation](#verifying-installation)
6. [Optional Components](#optional-components)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+, Fedora 34+)
- **Python**: 3.8 or higher
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **Display**: 1280×720 resolution

### Recommended
- **Python**: 3.10 or higher
- **RAM**: 8 GB or more
- **Storage**: 5 GB free space
- **Display**: 1920×1080 or higher
- **Internet**: For AI integrations and map tiles

---

## Quick Installation

For experienced users who already have Python installed:

```bash
# Clone repository
git clone https://github.com/sefy-levy/scientific-toolkit.git
cd scientific-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python Scientific-Toolkit.py
```

---

## Detailed Installation

### Windows

#### Step 1: Install Python

1. Download Python from [python.org/downloads](https://www.python.org/downloads/)
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:
```cmd
python --version
pip --version
```

#### Step 2: Install Git (Optional but Recommended)

Download from [git-scm.com](https://git-scm.com/download/win) or use GitHub Desktop.

#### Step 3: Download Scientific Toolkit

**Option A: Using Git**
```cmd
git clone https://github.com/sefy-levy/scientific-toolkit.git
cd scientific-toolkit
```

**Option B: Download ZIP**
1. Go to [GitHub repository](https://github.com/sefy-levy/scientific-toolkit)
2. Click "Code" → "Download ZIP"
3. Extract to your desired location
4. Open Command Prompt in that folder

#### Step 4: Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

#### Step 5: Install Dependencies

**Full installation:**
```cmd
pip install -r requirements.txt
```

**Minimal installation (faster, fewer features):**
```cmd
pip install -r requirements-minimal.txt
```

#### Step 6: Run the Toolkit

```cmd
python Scientific-Toolkit.py
```

---

### macOS

#### Step 1: Install Python

**Option A: Using Homebrew (Recommended)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10
```

**Option B: Download from python.org**
Download from [python.org/downloads](https://www.python.org/downloads/)

Verify installation:
```bash
python3 --version
pip3 --version
```

#### Step 2: Install Git

```bash
# Using Homebrew
brew install git

# Or download from git-scm.com
```

#### Step 3: Download Scientific Toolkit

```bash
git clone https://github.com/sefy-levy/scientific-toolkit.git
cd scientific-toolkit
```

#### Step 4: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 5: Install Dependencies

```bash
# Full installation
pip install -r requirements.txt

# Or minimal
pip install -r requirements-minimal.txt
```

#### Step 6: Run the Toolkit

```bash
python Scientific-Toolkit.py
```

**Note**: If you encounter permission issues, you may need to install tkinter:
```bash
brew install python-tk@3.10
```

---

### Linux

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv python3-tk git

# Clone repository
git clone https://github.com/sefy-levy/scientific-toolkit.git
cd scientific-toolkit

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python Scientific-Toolkit.py
```

#### Fedora/RHEL/CentOS

```bash
# Install Python and dependencies
sudo dnf install python3 python3-pip python3-tkinter git

# Clone repository
git clone https://github.com/sefy-levy/scientific-toolkit.git
cd scientific-toolkit

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python Scientific-Toolkit.py
```

#### Arch Linux

```bash
# Install Python and dependencies
sudo pacman -S python python-pip tk git

# Clone and setup (same as above)
```

---

## Installing Dependencies

### Understanding the Requirements Files

The toolkit provides two requirements files:

1. **requirements.txt** (Full installation)
   - All features enabled
   - ~60 packages
   - ~500 MB download
   - Includes AI integrations, advanced plotting, hardware support

2. **requirements-minimal.txt** (Basic installation)
   - Core features only
   - ~15 packages
   - ~150 MB download
   - Suitable for data analysis without hardware

### Installation Options

**Option 1: Full Installation (Recommended)**
```bash
pip install -r requirements.txt
```

**Option 2: Minimal Installation**
```bash
pip install -r requirements-minimal.txt
```

**Option 3: Custom Installation**

Install only what you need:

```bash
# Install core
pip install -r requirements-minimal.txt

# Add AI support
pip install openai anthropic google-generativeai

# Add hardware support
pip install pyserial pyvisa hidapi

# Add advanced plotting
pip install plotly python-ternary pyvista
```

### Troubleshooting Dependency Installation

**Issue: Compilation errors (especially on Windows)**

Some packages require C compilers. Solutions:

1. **Install Visual Studio Build Tools** (Windows)
   - Download from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/downloads/)
   - Install "Desktop development with C++"

2. **Use pre-compiled wheels**
   ```bash
   pip install --only-binary :all: package-name
   ```

3. **Use conda instead of pip**
   ```bash
   conda install -c conda-forge package-name
   ```

**Issue: "No module named 'tkinter'"**

Tkinter is Python's built-in GUI library but may not be included:

- **Ubuntu/Debian**: `sudo apt install python3-tk`
- **Fedora**: `sudo dnf install python3-tkinter`
- **macOS**: `brew install python-tk@3.10`
- **Windows**: Reinstall Python with "tcl/tk" option checked

**Issue: Permission denied**

On Linux/macOS, don't use `sudo pip`. Use virtual environments instead:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Verifying Installation

### Test Basic Functionality

```bash
# Activate virtual environment if not already active
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run toolkit
python Scientific-Toolkit.py
```

You should see:
1. Splash screen with loading progress
2. Main window with three panels
3. No error messages in terminal

### Test Imports

Run this test script:

```python
# test_installation.py
import sys

print("Testing Scientific Toolkit installation...\n")

required = {
    'numpy': 'NumPy',
    'pandas': 'Pandas',
    'matplotlib': 'Matplotlib',
    'scipy': 'SciPy',
    'sklearn': 'Scikit-learn',
    'geopandas': 'GeoPandas',
}

optional = {
    'plotly': 'Plotly',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic',
    'serial': 'PySerial',
}

print("Required packages:")
for module, name in required.items():
    try:
        __import__(module)
        print(f"  ✓ {name}")
    except ImportError:
        print(f"  ✗ {name} - MISSING!")

print("\nOptional packages:")
for module, name in optional.items():
    try:
        __import__(module)
        print(f"  ✓ {name}")
    except ImportError:
        print(f"  - {name} - Not installed")

print("\nInstallation test complete!")
```

Run it:
```bash
python test_installation.py
```

---

## Optional Components

### AI Integrations

To use AI assistants, you need API keys:

1. **OpenAI (ChatGPT)**
   - Sign up at [platform.openai.com](https://platform.openai.com/)
   - Get API key from dashboard
   - Set environment variable:
     ```bash
     export OPENAI_API_KEY="sk-..."  # Linux/macOS
     set OPENAI_API_KEY=sk-...       # Windows
     ```

2. **Anthropic (Claude)**
   - Sign up at [console.anthropic.com](https://console.anthropic.com/)
   - Set `ANTHROPIC_API_KEY`

3. **Google (Gemini)**
   - Get key from [makersuite.google.com](https://makersuite.google.com/)
   - Set `GOOGLE_API_KEY`

4. **Ollama (Local models)**
   - Download from [ollama.ai](https://ollama.ai/)
   - No API key needed

### Hardware Drivers

For instrument integration:

1. **Serial devices**: Usually work out-of-box on Linux/macOS
   - Windows: May need driver from manufacturer

2. **USB devices**: May need specific drivers
   - Check docs/INSTRUMENTS.md for specific requirements

3. **VISA instruments**: Install NI-VISA or pyvisa-py
   ```bash
   pip install pyvisa-py
   ```

### Google Earth Engine

For satellite data access:

```bash
pip install earthengine-api
earthengine authenticate
```

---

## Troubleshooting

### Common Issues

#### 1. "Python not found" or "pip not found"

**Solution**: Python not in PATH

- **Windows**: Reinstall Python, check "Add to PATH"
- **macOS/Linux**: Use `python3` and `pip3` instead

#### 2. "ModuleNotFoundError: No module named 'X'"

**Solution**: Package not installed

```bash
pip install package-name
```

Or reinstall requirements:
```bash
pip install -r requirements.txt --force-reinstall
```

#### 3. Toolkit window doesn't appear

**Solution**: Check terminal for errors

- Missing tkinter: Install python3-tk
- Display issues: Try setting `export DISPLAY=:0`

#### 4. ImportError: DLL load failed (Windows)

**Solution**: Visual C++ Redistributable needed

Download from [Microsoft](https://support.microsoft.com/help/2977003/the-latest-supported-visual-c-downloads)

#### 5. Permission denied (Linux/macOS)

**Solution**: Don't use sudo with pip

```bash
# Instead of: sudo pip install ...
# Do:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 6. Slow installation

**Solutions**:
- Use minimal requirements: `pip install -r requirements-minimal.txt`
- Use conda: `conda install -c conda-forge package-name`
- Use faster mirror: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`

### Getting Help

If you encounter issues not covered here:

1. Check [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Search [GitHub Issues](https://github.com/sefy-levy/scientific-toolkit/issues)
3. Create new issue with:
   - Your OS and Python version
   - Full error message
   - Steps to reproduce

---

## Next Steps

After successful installation:

1. Read [USER_GUIDE.md](USER_GUIDE.md) for usage instructions
2. Try example workflows with sample data in `samples/`
3. Configure your instruments (if applicable)
4. Set up AI assistants (optional)
5. Join discussions on GitHub

---

## Updating

To update to the latest version:

```bash
# Navigate to toolkit directory
cd scientific-toolkit

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart toolkit
python Scientific-Toolkit.py
```

---

## Uninstallation

To completely remove the toolkit:

```bash
# Deactivate virtual environment
deactivate

# Remove directory
cd ..
rm -rf scientific-toolkit  # Linux/macOS
# Or delete folder in Windows Explorer

# Remove API keys from environment (optional)
# Edit your .bashrc/.zshrc (Linux/macOS) or Environment Variables (Windows)
```

---

**Need help?** Email: sefy76@gmail.com or open an issue on GitHub!
