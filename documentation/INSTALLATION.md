📥 Installation Guide

Complete installation instructions for Windows, macOS, and Linux.
⚠️ Disclaimer

This software is provided "AS IS" without any warranty.

You are responsible for:

    Validating all results

    Verifying methods are appropriate for your data

    Reporting bugs and issues

Found a problem? → https://gitlab.com/sefy76/scientific-toolkit/-/issues
Requirements

    Python: 3.8 or higher (3.10+ recommended)

    Operating System: Windows 10/11, macOS 10.14+, or modern Linux

    Disk Space: ~50 MB for core files, +500 MB for full dependencies and sample data

    RAM: 2 GB minimum, 4 GB recommended (8 GB for large datasets)

    Display: 1280x800 minimum resolution

Quick Install (All Platforms)
bash

# 1. Clone repository
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# 2. Install core dependencies
pip install numpy pandas matplotlib

# 3. Launch
python Scientific-Toolkit.py

That's it for basic functionality! You'll have access to:

    ✅ 70 classification engines

    ✅ 50 protocols

    ✅ Data import/export

    ✅ Basic plotting

Full Installation (All Features)

For complete functionality including all 37 software plugins, 23 add-ons, and 7 hardware suites:
bash

pip install -r requirements.txt

Note: This installs ~40+ packages. Internet connection required. Total download size ~300-500 MB.
Platform-Specific Instructions
Windows

Option 1: Using Python from python.org

    Download Python from python.org

        IMPORTANT: Check "Add Python to PATH" during installation

        Ensure "Install tkinter" is checked (default)

    Open Command Prompt (cmd) as Administrator

    Run installation commands

Option 2: Using Anaconda (Recommended for beginners)
bash

conda create -n scitoolkit python=3.10
conda activate scitoolkit
pip install -r requirements.txt
python Scientific-Toolkit.py

Option 3: One-Click Installer (Windows only)

    Download Scientific-Toolkit-Setup.exe from Releases page

    Run installer (includes Python + all dependencies)

    Launch from Start Menu

Troubleshooting Windows:

    If python command not found, try py instead

    For permission errors, run Command Prompt as Administrator

    Windows Defender may slow first launch – add exception for folder

    For hardware devices, may need device-specific USB drivers

macOS

Prerequisites:
bash

# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

Installation:
bash

# Using system Python (macOS 10.14+)
python3 -m pip install --user -r requirements.txt
python3 Scientific-Toolkit.py

# Or using Homebrew Python (Recommended)
brew install python
pip3 install -r requirements.txt
python3 Scientific-Toolkit.py

macOS-specific notes:

    Tkinter is included with Python on macOS

    For GPS devices, may need to grant location permissions in System Preferences

    Hardware devices typically "just work" via USB

    If you get "Operation not permitted" errors, check Privacy settings

    Apple Silicon (M1/M2/M3) works natively with Python 3.10+

Linux

Ubuntu/Debian:
bash

# Install Python and Tkinter
sudo apt-get update
sudo apt-get install python3 python3-pip python3-tk python3-dev

# Install dependencies
pip3 install --user -r requirements.txt

# Launch
python3 Scientific-Toolkit.py

Fedora/RHEL:
bash

sudo dnf install python3 python3-pip python3-tkinter python3-devel
pip3 install --user -r requirements.txt
python3 Scientific-Toolkit.py

Arch Linux:
bash

sudo pacman -S python python-pip tk
pip install --user -r requirements.txt
python Scientific-Toolkit.py

Linux-specific notes:

    For hardware devices, may need to add user to dialout group:
    bash

    sudo usermod -a -G dialout $USER
    # Log out and back in

    Some USB devices may require udev rules (see hardware-specific docs)

    For serial devices, you may need python3-serial system package

    GUI may look different depending on your window manager

Verifying Installation

After installation, test that everything works:
bash

python Scientific-Toolkit.py

You should see:

    Splash screen with "Scientific Toolkit v2.0" logo

    Main window loads with three-panel layout

    Menu bar shows: File, Classify, Protocols, Visualize, Hardware, Advanced, Help

Test basic functionality:

    File → Import Data → CSV

    Navigate to samples/master_test_list.csv

    Data should load in the table (center panel)

    Try: Classify → Geochemistry → TAS Volcanic Classification

    Results should appear in right panel

Test Protocol Engine:

    Protocols → Behrensmeyer Weathering Protocol

    Select sample with weathering data

    Run protocol → should return stage 0-5

Test Plugin Manager:

    Advanced → Plugin Manager

    Should show 37 software + 23 add-on + 7 hardware plugins

    Toggle any plugin to enable/disable

If all this works, installation is successful!
Complete Dependency List
Core (Required - 3 packages)
text

numpy>=1.20.0          # Numerical computing
pandas>=1.3.0          # Data structures
matplotlib>=3.4.0      # Plotting

Standard (Recommended - adds 10 packages)
text

scipy>=1.7.0           # Scientific computing
scikit-learn>=0.24.0   # Machine learning
pillow>=8.0.0          # Image processing
seaborn>=0.11.0        # Statistical plots
openpyxl>=3.0.0        # Excel support
requests>=2.26.0       # HTTP requests
tkinter                # GUI (built-in)

Geospatial (Optional - 5 packages)
text

geopandas>=0.10.0      # Spatial data
rasterio>=1.2.0        # Raster data
shapely>=1.8.0         # Geometry operations
folium>=0.12.0         # Interactive maps
contextily>=1.1.0      # Map tiles

Hardware Support (Optional - 6 packages)
text

pyserial>=3.5          # Serial communication
hidapi>=0.10.0         # USB HID devices
bleak>=0.14.0          # Bluetooth LE
pyvisa>=1.11.0         # Instrument control
watchdog>=2.1.0        # File monitoring
simplekml>=1.3.0       # KML export

Statistical & MCMC (Optional - 4 packages)
text

emcee>=3.1.0           # MCMC sampling
corner>=2.2.1          # Corner plots
joblib>=1.1.0          # Parallel processing
statsmodels>=0.13.0    # Statistical models

AI Assistants (Optional - 6 packages)
text

anthropic>=0.3.0       # Claude AI
openai>=0.27.0         # ChatGPT
google-generativeai>=0.3.0  # Gemini
transformers>=4.21.0   # Hugging Face models
torch>=1.12.0          # PyTorch (optional)
ollama                 # Local AI (optional)

Specialized (Optional - varies)
text

pyrolite>=0.8.0        # Geochemical data
lmfit>=1.0.0           # Curve fitting
pybaselines>=1.0.0     # Baseline correction
trimesh>=3.9.0         # 3D mesh handling
pynmea2>=1.15.0        # GPS parsing
reportlab>=3.6.0       # PDF generation

Total optional packages: ~40-50 depending on selections
Using the Plugin Manager

The Plugin Manager makes dependency management easy:

    Launch: Advanced → Plugin Manager

    Browse available plugins by category:

        Software (37 plugins): Advanced analysis tools

        Add-ons (23 plugins): Plotting, consoles, AI

        Hardware (7 suites): Device drivers

    For each plugin, the manager shows:

        ✅ Installed and enabled

        ⚠️ Missing dependencies (with install button)

        ❌ Not installed (with install button)

    Click "Install Dependencies" for any plugin to auto-install required packages

Installation Issues & Solutions
"No module named 'tkinter'"

Windows: Reinstall Python with Tkinter option checked

Linux:
bash

sudo apt-get install python3-tk  # Ubuntu/Debian
sudo dnf install python3-tkinter  # Fedora

macOS: Tkinter should be included; if not:
bash

brew install python-tk@3.10

"Permission denied" errors

Linux/macOS:
bash

pip install --user -r requirements.txt
# Instead of sudo pip (don't use sudo with pip)

Windows: Run Command Prompt as Administrator
"Microsoft Visual C++ 14.0 or greater is required" (Windows)

Some packages need C++ compilers:

    Download Visual Studio Build Tools

    Run installer, select "Desktop development with C++"

    Restart command prompt and try again

Dependencies fail to install

Try upgrading pip first:
bash

python -m pip install --upgrade pip

Install minimal dependencies only:
bash

pip install numpy pandas matplotlib

Then use Plugin Manager to install specific feature packages.

For problematic packages, try conda:
bash

conda install -c conda-forge geopandas rasterio

Hardware devices not recognized

Serial devices (XRF, GPS, balances, meters):

    Windows: Install device-specific USB drivers (FTDI, Prolific, etc.)

    Linux: Add user to dialout group (see above)

    macOS: Usually works without drivers

Check available ports:
python

# In Python console
import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(f"{p.device}: {p.description}")

USB HID devices (calipers):

    Windows: Should work automatically

    Linux: May need sudo or udev rules

    macOS: Works without drivers

Bluetooth devices:

    Ensure Bluetooth is enabled

    Pair device first in system settings

    Note the MAC address for connection

Application crashes on startup

    Check Python version: python --version (need 3.8+)

    Launch from terminal to see error messages:
    bash

    python Scientific-Toolkit.py

    Check that Tkinter works:
    python

    python -m tkinter

    Should show a test window

    Delete any existing cache files:
    bash

    rm -rf ~/.scientific_toolkit_cache
    rm -rf config/plugin_cache.json

    Try with minimal dependencies:
    bash

    pip install numpy pandas matplotlib
    python Scientific-Toolkit.py --safe-mode

Plugin Manager shows "Failed to load"

Check permissions:
bash

# Linux/macOS
chmod -R 755 plugins/
chmod -R 755 config/

Check Python path:
python

import sys
print(sys.path)
# Should include your toolkit directory

Uninstallation

To remove Scientific Toolkit completely:
bash

# Remove directory
cd ..
rm -rf scientific-toolkit

# Remove Python packages (optional)
pip uninstall numpy pandas matplotlib scipy scikit-learn
# ... etc for any others you want to remove

# Remove config files (Linux/macOS)
rm -rf ~/.scientific_toolkit
rm -rf ~/.scientific_toolkit_cache

# Remove config files (Windows)
# Delete %USERPROFILE%\.scientific_toolkit

No registry entries or system modifications are made.
Updating

To update to a new version:
bash

cd scientific-toolkit
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Clear plugin cache (if needed)
rm -rf config/plugin_cache.json

Your data, projects, and settings remain untouched.
Development Installation

For contributors wanting to modify the code:
bash

git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt  # Includes testing tools

# Run tests
pytest tests/ -v

Development tools included:

    pytest (testing framework)

    black (code formatting)

    flake8 (linting)

    mypy (type checking)

Offline Installation

For computers without internet access:

Step 1: On a computer WITH internet:
bash

# Download all packages and dependencies
pip download -r requirements.txt -d packages/ --platform manylinux2014_x86_64
# Adjust platform for your target OS (win_amd64, macosx_10_9_x86_64, etc.)

Step 2: Copy files:
bash

# Copy scientific-toolkit/ folder and packages/ folder to offline computer
scp -r scientific-toolkit/ user@offline-computer:~
scp -r packages/ user@offline-computer:~

Step 3: On offline computer:
bash

cd scientific-toolkit
pip install --no-index --find-links=../packages/ -r requirements.txt
python Scientific-Toolkit.py

Docker Installation (Advanced)

For isolated containerized environment:

Dockerfile:
dockerfile

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    python3-tk \
    libgl1-mesa-glx \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "Scientific-Toolkit.py"]

Build and run:
bash

docker build -t scientific-toolkit .
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix scientific-toolkit

Note: GUI applications in Docker require X11 forwarding (Linux) or XQuartz (macOS).
Common Installation Scenarios
Scenario 1: Student with limited disk space
bash

# Install only core + essentials
pip install numpy pandas matplotlib scipy
# Use Plugin Manager to install specific plugins as needed

Scenario 2: Field geologist with portable XRF
bash

# Install core + hardware support
pip install numpy pandas matplotlib pyserial hidapi bleak
# Elemental Geochemistry suite will auto-detect your device

Scenario 3: Archaeologist with zooarchaeology focus
bash

# Install core + archaeology plugins
pip install numpy pandas matplotlib openpyxl
# Enable Zooarchaeology, Lithics, Photo Manager via Plugin Manager

Scenario 4: Researcher needing full capabilities
bash

# Full installation (may take 10-15 minutes)
pip install -r requirements.txt
# This installs all 40+ optional packages

Post-Installation Checklist

After installation, verify:

    python Scientific-Toolkit.py launches successfully

    Sample data loads (File → Import Data → samples/master_test_list.csv)

    Classification works (Classify → Geochemistry → TAS Volcanic Classification)

    Protocols work (Protocols → Behrensmeyer Weathering Protocol)

    Plugin Manager loads (Advanced → Plugin Manager)

    At least one plot generates (Visualize → Scatter Plot)

Need Help?

    Check FAQ for common issues

    Check Troubleshooting Guide for detailed solutions

    Open an issue: https://gitlab.com/sefy76/scientific-toolkit/-/issues

When reporting issues, include:

    Operating system and version

    Python version (python --version)

    Installation method (pip/conda/source)

    Full error message (copy-paste)

    What you were trying to do

    Output of pip list (optional)

Quick Reference
Command	Purpose
git clone https://gitlab.com/sefy76/scientific-toolkit.git	Download
pip install -r requirements.txt	Full install
pip install numpy pandas matplotlib	Minimal install
python Scientific-Toolkit.py	Launch
python -m tkinter	Test Tkinter
pytest tests/ -v	Run tests
pip list | grep -E "numpy|pandas|matplotlib"	Check versions

Questions? sefy76@gmail.com | Issues? GitLab Issues

Happy Scientisting! 🔬
