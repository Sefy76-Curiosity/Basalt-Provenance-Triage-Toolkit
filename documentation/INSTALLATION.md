# 📥 Installation Guide

Complete installation instructions for Windows, macOS, and Linux.

---

## ⚠️ Disclaimer

**This software is provided "AS IS" without any warranty.**

You are responsible for:
- Validating all results
- Verifying methods are appropriate for your data
- Reporting bugs and issues

**Found a problem?** → https://gitlab.com/sefy76/scientific-toolkit/-/issues

---

## Requirements

- **Python**: 3.8 or higher (3.10+ recommended)
- **Operating System**: Windows 10/11, macOS 10.14+, or modern Linux
- **Disk Space**: ~50 MB for core files, +200 MB for full dependencies
- **RAM**: 2 GB minimum, 4 GB recommended
- **Display**: 1280x800 minimum resolution

---

## Quick Install (All Platforms)

```bash
# 1. Clone repository
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# 2. Install core dependencies
pip install numpy pandas matplotlib

# 3. Launch
python Scientific-Toolkit.py
```

That's it for basic functionality!

---

## Full Installation (All Features)

For complete functionality including all plugins:

```bash
pip install -r requirements.txt
```

**Note:** This installs ~20 packages. Internet connection required.

---

## Platform-Specific Instructions

### Windows

**Option 1: Using Python from python.org**

1. Download Python from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
2. Open Command Prompt (cmd)
3. Run installation commands above

**Option 2: Using Anaconda**

```bash
conda create -n scitoolkit python=3.10
conda activate scitoolkit
pip install -r requirements.txt
python Scientific-Toolkit.py
```

**Troubleshooting Windows:**
- If `python` command not found, try `py` instead
- Tkinter should be included with Python on Windows
- For hardware devices, may need device-specific USB drivers

---

### macOS

**Prerequisites:**
```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install
```

**Installation:**
```bash
# Using system Python (macOS 10.14+)
python3 -m pip install --user -r requirements.txt
python3 Scientific-Toolkit.py

# Or using Homebrew Python
brew install python
pip3 install -r requirements.txt
python3 Scientific-Toolkit.py
```

**macOS-specific notes:**
- Tkinter is included with Python on macOS
- For GPS devices, may need to grant location permissions
- Hardware devices typically "just work" via USB

---

### Linux

**Ubuntu/Debian:**
```bash
# Install Python and Tkinter
sudo apt-get update
sudo apt-get install python3 python3-pip python3-tk

# Install dependencies
pip3 install -r requirements.txt

# Launch
python3 Scientific-Toolkit.py
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip python3-tkinter
pip3 install -r requirements.txt
python3 Scientific-Toolkit.py
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip tk
pip install -r requirements.txt
python Scientific-Toolkit.py
```

**Linux-specific notes:**
- For hardware devices, may need to add user to dialout group:
  ```bash
  sudo usermod -a -G dialout $USER
  # Log out and back in
  ```
- Some USB devices may require udev rules

---

## Verifying Installation

After installation, test that everything works:

```bash
python Scientific-Toolkit.py
```

You should see:
1. Splash screen with "Scientific Toolkit" logo
2. Main window loads
3. Menu bar shows: File, Classify, Visualize, Hardware, Advanced

**Test basic functionality:**
1. File → Import Data → CSV
2. Navigate to `samples/master_test_list.csv`
3. Data should load in the table
4. Try: Classify → Geochemistry → TAS Volcanic Classification

If this works, installation is successful!

---

## Dependency List

### Core (Required)
```
numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.4.0
```

### Standard (Recommended)
```
scipy>=1.7.0
scikit-learn>=0.24.0
pillow>=8.0.0
```

### Optional (For Specific Features)

**Geospatial:**
```
geopandas>=0.10.0
rasterio>=1.2.0
shapely>=1.8.0
```

**Advanced Plotting:**
```
seaborn>=0.11.0
plotly>=5.0.0
```

**Hardware Devices:**
```
pyserial>=3.5      # XRF, GPS, EC meters
watchdog>=2.1.0    # File monitoring
```

**AI Assistants:**
```
anthropic>=0.3.0   # Claude AI
openai>=0.27.0     # ChatGPT
google-generativeai  # Gemini
```

**Statistical:**
```
statsmodels>=0.13.0
```

---

## Installation Issues & Solutions

### "No module named 'tkinter'"

**Windows:** Reinstall Python with Tkinter option checked

**Linux:**
```bash
sudo apt-get install python3-tk  # Ubuntu/Debian
sudo dnf install python3-tkinter  # Fedora
```

**macOS:** Tkinter should be included; if not, reinstall Python from python.org

---

### "Permission denied" errors

**Linux/macOS:**
```bash
pip install --user -r requirements.txt
# Instead of sudo pip (don't use sudo with pip)
```

---

### Dependencies fail to install

**Try upgrading pip first:**
```bash
python -m pip install --upgrade pip
```

**Install minimal dependencies only:**
```bash
pip install numpy pandas matplotlib
```

Then add others as needed.

---

### Hardware devices not recognized

**Serial devices (XRF, GPS, meters):**
- Windows: Install device-specific USB drivers
- Linux: Add user to dialout group (see above)
- macOS: Usually works without drivers

**Check device connection:**
```python
# In Python console
import serial.tools.list_ports
list(serial.tools.list_ports.comports())
```

---

### Application crashes on startup

1. Check Python version: `python --version` (need 3.8+)
2. Try launching from terminal to see error messages
3. Check that Tkinter works:
   ```python
   python -m tkinter
   ```
   Should show a test window

4. Delete any existing .toolkit cache files
5. Try with minimal dependencies (just numpy, pandas, matplotlib)

---

## Uninstallation

To remove Scientific Toolkit:

```bash
# Remove directory
cd ..
rm -rf scientific-toolkit

# Remove Python packages (optional)
pip uninstall numpy pandas matplotlib scipy scikit-learn
# ... etc for any others you want to remove
```

No registry entries or system modifications are made.

---

## Updating

To update to a new version:

```bash
cd scientific-toolkit
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt
```

Your data and projects remain untouched.

---

## Development Installation

For contributors wanting to modify the code:

```bash
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements.txt
```

---

## Offline Installation

For computers without internet access:

1. On a computer WITH internet:
   ```bash
   pip download -r requirements.txt -d packages/
   ```

2. Copy `scientific-toolkit/` folder and `packages/` folder to offline computer

3. On offline computer:
   ```bash
   pip install --no-index --find-links=packages/ -r requirements.txt
   ```

---

## Docker Installation (Advanced)

For isolated environment:

```dockerfile
# Dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y python3-tk
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "Scientific-Toolkit.py"]
```

**Note:** GUI applications in Docker require X11 forwarding.

---

## Need Help?

- Check [FAQ](FAQ.md) for common issues
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Open an issue: https://gitlab.com/sefy76/scientific-toolkit/-/issues

Include in your issue:
- Operating system and version
- Python version (`python --version`)
- Full error message
- What you were trying to do
