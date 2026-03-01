📥 Installation Guide

Complete installation instructions for Windows, macOS, and Linux.
Scientific Toolkit v2.5

⚠️ Disclaimer

This software is provided "AS IS" without any warranty.
You are responsible for validating all results and verifying methods are appropriate for your data.

Found a problem? → https://gitlab.com/sefy76/scientific-toolkit/-/issues

Requirements
    Python: 3.8 or higher (3.10+ recommended)
    Operating System: Windows 10/11, macOS 10.14+, or modern Linux
    Disk Space: ~50 MB for core files, +500 MB for full dependencies and sample data
    RAM: 2 GB minimum, 4 GB recommended (8 GB for large datasets)
    Display: 1280×800 minimum resolution

Quick Install (All Platforms)

    # 1. Clone repository
    git clone https://gitlab.com/sefy76/scientific-toolkit.git
    cd scientific-toolkit

    # 2. Install core + UI dependencies
    pip install numpy pandas matplotlib ttkbootstrap

    # 3. Launch
    python Scientific-Toolkit.py

That's it for basic functionality! You'll have access to:
    ✅ 70 classification engines
    ✅ 50 protocols
    ✅ Data import/export
    ✅ Basic plotting
    ✅ Toolkit AI (offline, no API key)
    ✅ All 16 Field Panels
    ✅ Statistical Console
    ✅ Auto-save with crash recovery

New in v2.5: ttkbootstrap is now required for the UI.
Install separately if not picked up by requirements.txt:
    pip install ttkbootstrap

Full Installation (All Features)

For complete functionality including all software plugins, add-ons, and hardware suites:

    pip install -r requirements.txt

Note: This installs ~40+ packages. Internet connection required. Total download ~300–500 MB.

Platform-Specific Instructions
Windows

Option 1: Using Python from python.org
    1. Download Python from python.org
       IMPORTANT: Check "Add Python to PATH" during installation
       Ensure "Install tkinter" is checked (default)
    2. Open Command Prompt (cmd) as Administrator
    3. Run:
       pip install -r requirements.txt
       python Scientific-Toolkit.py

Option 2: Using Anaconda (Recommended for beginners)

    conda create -n scitoolkit python=3.10
    conda activate scitoolkit
    pip install -r requirements.txt
    python Scientific-Toolkit.py

Troubleshooting Windows:
    If python command not found, try py instead
    For permission errors, run Command Prompt as Administrator
    Windows Defender may slow first launch — add exception for the folder
    For hardware devices, may need device-specific USB drivers (FTDI, Prolific, etc.)

macOS

Prerequisites:

    # Install Xcode Command Line Tools (if not already installed)
    xcode-select --install

Installation:

    # Using Homebrew Python (Recommended)
    brew install python
    pip3 install -r requirements.txt
    python3 Scientific-Toolkit.py

    # Or using system Python
    python3 -m pip install --user -r requirements.txt
    python3 Scientific-Toolkit.py

macOS-specific notes:
    Tkinter is included with Python on macOS
    Apple Silicon (M1/M2/M3) works natively with Python 3.10+
    For GPS devices, may need to grant location permissions in System Preferences

Linux

Ubuntu/Debian:

    sudo apt-get update
    sudo apt-get install python3 python3-pip python3-tk python3-dev
    pip3 install --user -r requirements.txt
    python3 Scientific-Toolkit.py

Fedora/RHEL:

    sudo dnf install python3 python3-pip python3-tkinter python3-devel
    pip3 install --user -r requirements.txt
    python3 Scientific-Toolkit.py

Arch Linux:

    sudo pacman -S python python-pip tk
    pip install --user -r requirements.txt
    python Scientific-Toolkit.py

Linux-specific notes:
    For hardware devices (serial), add user to dialout group:

        sudo usermod -a -G dialout $USER
        # Log out and back in

    Some USB devices may require udev rules (see hardware-specific docs)

Verifying Installation

After installation, test that everything works:

    python Scientific-Toolkit.py

You should see:
    Splash screen with "Scientific Toolkit v2.5"
    Main window loads with three-panel ttkbootstrap layout
    Menu bar shows: File, Classify, Protocols, Visualize, Hardware, Advanced, Help

Test basic functionality:

    1. File → Import Data → CSV → samples/geochemistry_test.csv
    2. Right panel shows: "Switch to Geochemistry Panel?" → Click Yes
    3. TAS diagram, AFM diagram, and Mg# histogram appear in right panel
    4. Click ← Back to return to Classification HUD
    5. Select scheme → Apply → results appear in HUD

Test Field Panels:
    Import any of the 16 domain test files from samples/:
    archaeology_test.csv, spectroscopy_test.csv, zooarch_test.csv, etc.
    Each should trigger the corresponding field panel offer.

Test Toolkit AI:
    Advanced → Plugin Manager → Add-ons → Toolkit AI → Enable
    Open Toolkit AI tab → ask "What plugins do I have installed?"
    Should list plugins scanned from the codebase

Test Auto-Save:
    Wait 5 minutes after importing data
    Check auto_save/ folder — recovery.stproj should appear
    Next launch: recovery prompt should appear

Test Macro Recorder:
    Ctrl+R (start recording)
    Import a file, select a classification scheme, apply it
    Sort a column, switch a tab, navigate pages
    Ctrl+T (stop recording)
    Ctrl+M → verify all actions were captured (should show 5+ action types)

Test Plugin Manager:
    Advanced → Plugin Manager
    Should show 37 software + 25 add-on + 16 hardware suites listed

Complete Dependency List

Core (Required — 4 packages)
    numpy>=1.20.0           # Numerical computing
    pandas>=1.3.0           # Data structures
    matplotlib>=3.4.0       # Plotting
    ttkbootstrap>=1.10.0    # Modern UI framework (NEW in v2.5)

Standard (Recommended — adds 10 packages)
    scipy>=1.7.0            # Scientific computing
    scikit-learn>=0.24.0    # Machine learning
    pillow>=8.0.0           # Image processing
    seaborn>=0.11.0         # Statistical plots
    openpyxl>=3.0.0         # Excel support
    requests>=2.26.0        # HTTP requests

Geospatial (Optional — 5 packages)
    geopandas>=0.10.0       # Spatial data
    rasterio>=1.2.0         # Raster data
    shapely>=1.8.0          # Geometry operations
    folium>=0.12.0          # Interactive maps
    contextily>=1.1.0       # Map tiles

Hardware Support (Optional — 6 packages)
    pyserial>=3.5           # Serial communication
    hidapi>=0.10.0          # USB HID devices (calipers)
    bleak>=0.14.0           # Bluetooth LE
    pyvisa>=1.11.0          # Instrument control (GPIB/USB-TMC)
    watchdog>=2.1.0         # File monitoring
    simplekml>=1.3.0        # KML export

Statistical & MCMC (Optional — 4 packages)
    emcee>=3.1.0            # MCMC sampling (Bayesian isotope mixing)
    corner>=2.2.1           # Corner plots
    joblib>=1.1.0           # Parallel processing
    statsmodels>=0.13.0     # Statistical models

Spectroscopy (Optional — 2 packages)
    pybaselines>=1.0.0      # Baseline correction (Spectral Toolbox)
    lmfit>=1.0.0            # Peak fitting

AI Assistants (Optional — varies)
    anthropic>=0.3.0        # Claude AI plugin (NOT needed for Toolkit AI)
    openai>=0.27.0          # ChatGPT plugin
    google-generativeai>=0.3.0  # Gemini plugin
    ollama                  # Local AI (optional)

Note: Toolkit AI (built-in) requires NO external packages.

Specialized (Optional)
    pyrolite>=0.8.0         # Geochemical data
    trimesh>=3.9.0          # 3D mesh handling
    pynmea2>=1.15.0         # GPS NMEA parsing
    reportlab>=3.6.0        # PDF generation
    python-docx>=0.8.0      # Word document export (Report Generator plugin)

Using the Plugin Manager

The Plugin Manager makes dependency management easy:

    Launch: Advanced → Plugin Manager
    Browse available plugins by category:
        Software (37 plugins): Advanced analysis tools
        Add-ons (25 plugins): Plotting, consoles, AI assistants
        Hardware (16 suites): Device drivers
    For each plugin, the manager shows:
        ✅ Installed and enabled
        ⚠️ Missing dependencies (with install button)
        ❌ Not installed (with install button)
    Click "Install Dependencies" to auto-install required packages

Two plugins are highlighted as always enabled by default:
    Toolkit AI (built-in AI, no dependencies)
    Statistical Console (no scipy needed)

Installation Issues & Solutions

"No module named ttkbootstrap"
    pip install ttkbootstrap

"No module named tkinter"
    Windows:  Reinstall Python with Tkinter option checked
    Linux:    sudo apt-get install python3-tk
    macOS:    brew install python-tk@3.10

"Permission denied" errors
    Linux/macOS:  pip install --user -r requirements.txt
    Windows:      Run Command Prompt as Administrator

"Microsoft Visual C++ 14.0 or greater is required" (Windows)
    Download Visual Studio Build Tools
    Select "Desktop development with C++"
    Restart command prompt and retry

Dependencies fail to install
    Upgrade pip first:
        python -m pip install --upgrade pip
    Install minimal set first:
        pip install numpy pandas matplotlib ttkbootstrap
    Then use Plugin Manager for specific plugin packages
    For problematic packages, try conda:
        conda install -c conda-forge geopandas rasterio

Hardware devices not recognized
    Serial devices: Windows may need FTDI/Prolific USB drivers
    Linux: sudo usermod -a -G dialout $USER (log out and back in)
    All platforms: check available ports:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            print(f"{p.device}: {p.description}")

Application crashes on startup
    Check Python version: python --version (need 3.8+)
    Check ttkbootstrap installed: python -c "import ttkbootstrap"
    Launch from terminal to see error messages
    Delete any stale cache files:
        rm -rf config/ai_knowledge_cache.json
        rm -rf config/plugin_cache.json

Uninstallation

    # Remove directory
    cd ..
    rm -rf scientific-toolkit

    # Remove config files (Linux/macOS)
    rm -rf ~/.scientific_toolkit

    # Windows: Delete %USERPROFILE%\.scientific_toolkit

No registry entries or system modifications are made.

Updating

    cd scientific-toolkit
    git pull origin main
    pip install --upgrade -r requirements.txt

    # Clear AI knowledge cache so Toolkit AI rescans new plugins
    rm config/ai_knowledge_cache.json

Your data, projects, and macros remain untouched.

Docker Installation (Advanced)

Dockerfile:

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

    docker build -t scientific-toolkit .
    docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix scientific-toolkit

Note: GUI applications in Docker require X11 forwarding (Linux) or XQuartz (macOS).

Common Installation Scenarios

Scenario 1: Student with limited disk space
    pip install numpy pandas matplotlib ttkbootstrap scipy
    # Use Plugin Manager to install specific plugins as needed

Scenario 2: Field geologist with portable XRF
    pip install numpy pandas matplotlib ttkbootstrap pyserial hidapi bleak
    # Elemental Geochemistry suite will auto-detect your device

Scenario 3: Archaeologist with zooarchaeology focus
    pip install numpy pandas matplotlib ttkbootstrap openpyxl
    # Enable Zooarchaeology field panel, Zooarch Analysis Suite, Photo Manager

Scenario 4: Researcher needing full capabilities
    pip install -r requirements.txt    # may take 10–15 minutes

Post-Installation Checklist

After installation, verify:
    ☐ python Scientific-Toolkit.py launches with ttkbootstrap-styled UI
    ☐ Sample data loads: File → Import Data → samples/geochemistry_test.csv
    ☐ Field panel auto-offer appears for geochemistry data
    ☐ Classification works: right panel → TAS → Apply
    ☐ Protocols work: Protocols → Behrensmeyer Weathering Protocol
    ☐ Plugin Manager loads: Advanced → Plugin Manager (37 sw + 25 add-ons + 16 hw)
    ☐ Toolkit AI listed: Advanced → Plugin Manager → Add-ons → Toolkit AI
    ☐ Statistical Console listed: Advanced → Plugin Manager → Add-ons
    ☐ Auto-save folder created: auto_save/ appears after first data import
    ☐ At least one plot generates: Visualize → Scatter Plot

Need Help?
    Check FAQ.md for common issues
    Open an issue: https://gitlab.com/sefy76/scientific-toolkit/-/issues

When reporting issues, include:
    Operating system and version
    Python version: python --version
    ttkbootstrap version: python -c "import ttkbootstrap; print(ttkbootstrap.__version__)"
    Full error message (copy-paste)
    What you were trying to do
    Output of pip list

Quick Reference
Command                                             Purpose
git clone https://...scientific-toolkit.git         Download
pip install -r requirements.txt                     Full install
pip install numpy pandas matplotlib ttkbootstrap    Minimal install
python Scientific-Toolkit.py                        Launch
python -m tkinter                                   Test Tkinter
pytest tests/ -v                                    Run tests

Questions? sefy76@gmail.com | Issues? GitLab Issues

Happy Scientisting! 🔬
