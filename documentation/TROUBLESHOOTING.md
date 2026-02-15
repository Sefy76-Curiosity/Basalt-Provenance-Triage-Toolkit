# Troubleshooting Guide

Common problems and solutions for Scientific Toolkit v2.0.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Starting the Toolkit](#starting-the-toolkit)
3. [Data Import Problems](#data-import-problems)
4. [Classification Issues](#classification-issues)
5. [Visualization Problems](#visualization-problems)
6. [Plugin Issues](#plugin-issues)
7. [Performance Problems](#performance-problems)
8. [Error Messages](#error-messages)
9. [Platform-Specific Issues](#platform-specific-issues)
10. [Getting More Help](#getting-more-help)

---

## Installation Issues

### Python Not Found

**Symptom**: `python: command not found` or `'python' is not recognized`

**Solutions**:
1. **Check if Python is installed**:
   ```bash
   python --version  # or python3 --version
   ```

2. **Install Python**:
   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - **macOS**: `brew install python@3.10`
   - **Linux**: `sudo apt install python3` (Ubuntu/Debian)

3. **Add Python to PATH** (Windows):
   - Reinstall Python, check "Add Python to PATH"
   - Or manually add to environment variables

### pip Not Found

**Symptom**: `pip: command not found`

**Solutions**:
```bash
# Try pip3 instead
pip3 --version

# Install pip
python -m ensurepip --upgrade

# On Linux
sudo apt install python3-pip
```

### Permission Denied (Linux/macOS)

**Symptom**: `Permission denied` when installing packages

**Solutions**:
```bash
# DON'T use sudo pip install
# Instead, use virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Compilation Errors

**Symptom**: `error: Microsoft Visual C++ 14.0 or greater is required`

**Solutions**:
1. **Install Visual Studio Build Tools** (Windows):
   - Download from [Visual Studio](https://visualstudio.microsoft.com/downloads/)
   - Install "Desktop development with C++"

2. **Use pre-compiled wheels**:
   ```bash
   pip install --only-binary :all: package-name
   ```

3. **Use conda instead**:
   ```bash
   conda install -c conda-forge package-name
   ```

### ModuleNotFoundError: No module named 'tkinter'

**Symptom**: Toolkit won't start, missing tkinter

**Solutions**:
- **Ubuntu/Debian**: `sudo apt install python3-tk`
- **Fedora**: `sudo dnf install python3-tkinter`
- **macOS**: `brew install python-tk@3.10`
- **Windows**: Reinstall Python, check "tcl/tk and IDLE" option

### Slow Installation

**Symptom**: `pip install` takes forever

**Solutions**:
1. **Use faster mirror** (China users):
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. **Install minimal requirements first**:
   ```bash
   pip install -r requirements-minimal.txt
   ```

3. **Use conda**:
   ```bash
   conda install -c conda-forge numpy pandas matplotlib
   ```

---

## Starting the Toolkit

### Toolkit Won't Start

**Symptom**: Double-click does nothing, or immediate crash

**Diagnosis**:
```bash
# Run from terminal to see error messages
python Scientific-Toolkit.py
```

**Common causes and solutions**:

1. **Missing dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Wrong Python version**:
   ```bash
   python --version  # Should be 3.8+
   ```

3. **Corrupted config files**:
   ```bash
   # Delete and regenerate
   rm -rf config/*.json
   ```

4. **Permission issues**:
   ```bash
   # Check file permissions
   chmod +x Scientific-Toolkit.py
   ```

### Splash Screen Freezes

**Symptom**: Loading screen appears but never completes

**Solutions**:
1. **Check terminal for errors**
2. **Disable auto-loading plugins**:
   - Edit `config/enabled_plugins.json`
   - Set all to empty arrays `[]`
3. **Clear cache**:
   ```bash
   rm -rf __pycache__/ */__pycache__/
   ```

### Window Doesn't Appear

**Symptom**: Process runs but no window

**Solutions**:
1. **Check display** (Linux):
   ```bash
   export DISPLAY=:0
   python Scientific-Toolkit.py
   ```

2. **Run as admin** (Windows):
   - Right-click → "Run as administrator"

3. **Check taskbar**: Window may be minimized or behind other windows

---

## Data Import Problems

### File Won't Import

**Symptom**: "Could not open file" or blank table

**Solutions**:

1. **Check file format**:
   - Must be CSV, Excel (.xlsx, .xls), or JSON
   - Open in text editor to verify format

2. **Check encoding**:
   ```python
   # Try different encodings
   # In import dialog, select: UTF-8, Latin-1, or Windows-1252
   ```

3. **Check for special characters**:
   - Remove non-ASCII characters from headers
   - Use only letters, numbers, underscores

4. **Verify file path**:
   - No special characters in folder names
   - Path not too long (Windows: <260 characters)

### Excel Import Fails

**Symptom**: `xlrd.biffh.XLRDError` or similar

**Solutions**:
```bash
# Update openpyxl
pip install --upgrade openpyxl

# If using old .xls format
pip install xlrd
```

### Wrong Delimiter

**Symptom**: All data in one column

**Solutions**:
1. **In import dialog**, try different delimiters:
   - Comma (`,`)
   - Tab (`\t`)
   - Semicolon (`;`)
   - Pipe (`|`)

2. **Auto-detect**:
   - Enable "Auto-detect delimiter" option

### Decimal Separator Issues

**Symptom**: Numbers treated as text (e.g., European format `5,2` instead of `5.2`)

**Solutions**:
1. **In import dialog**, set decimal separator:
   - Use `.` (international)
   - Or `,` (European)

2. **Pre-process file**:
   - Find/replace in text editor
   - Change `,` to `.` in numerical columns

---

## Classification Issues

### All Samples "Unclassified"

**Symptom**: Classification runs but all results are "Unclassified"

**Diagnosis**:
1. **Check required columns exist**:
   - Classification requirements shown in right panel
   - Column names must match (case-sensitive)

2. **Check data values**:
   - Must be numerical
   - No NaN, Inf, or text values
   - Check units (e.g., wt% vs ppm)

**Solutions**:
1. **Standardize column names**:
   - Edit → Standardize Column Names
   - Or rename manually

2. **Check data types**:
   ```python
   # In Python console
   df.dtypes  # Should show float64 or int64, not object
   ```

3. **Handle missing values**:
   - Edit → Fill Missing Values
   - Or remove incomplete samples

### Classification Error

**Symptom**: Error message during classification

**Common errors**:

1. **"Column not found"**:
   - Rename column to match required name
   - Or edit classification JSON to accept your column name

2. **"Invalid data type"**:
   - Convert to numeric: Edit → Convert Column Type

3. **"Division by zero"**:
   - Check for zero values in denominators
   - Filter them out first

### Wrong Classification Results

**Symptom**: Results don't match literature

**Check**:
1. **Units**: Classification may expect wt%, you have ppm
2. **Normalization**: Some need anhydrous or volatile-free
3. **Total**: Oxide totals should be ~98-102%
4. **Standards**: Compare with known samples

---

## Visualization Problems

### Plot Doesn't Appear

**Symptom**: Click "Plot" but nothing happens

**Solutions**:
1. **Check for errors** in terminal
2. **Select correct columns** for X and Y axes
3. **Ensure numerical data** (not text)
4. **Close other plots** (may have reached limit)
5. **Update matplotlib**:
   ```bash
   pip install --upgrade matplotlib
   ```

### Plot Looks Wrong

**Symptom**: Data present but visualization is incorrect

**Common issues**:

1. **Axes swapped**: Check X/Y selection
2. **Wrong scale**: Try log scale for large ranges
3. **Overlapping points**: Reduce point size or add transparency
4. **Missing data**: Filter NaN values first
5. **Wrong plot type**: Scatter for continuous, bar for categorical

### Can't Export Plot

**Symptom**: Export fails or file is blank

**Solutions**:
1. **Check permissions** in save directory
2. **Use different format**: Try PNG instead of SVG
3. **Reduce resolution**: Lower DPI (e.g., 150 instead of 600)
4. **Close plot first**, then export

### Ternary Diagram Error

**Symptom**: `ValueError` when creating ternary plot

**Check**:
1. **Three columns selected**
2. **Values sum to 100** (or will be normalized)
3. **No negative values**
4. **All numerical**

---

## Plugin Issues

### Plugin Won't Enable

**Symptom**: Check box doesn't stay checked

**Solutions**:
1. **Check dependencies**:
   - Plugin may require additional packages
   - Check plugin documentation

2. **Check error log**:
   - View → Show Error Log
   - Look for ImportError or ModuleNotFoundError

3. **Install missing packages**:
   ```bash
   pip install package-name
   ```

### Hardware Plugin Won't Connect

**Symptom**: "Connection failed" error

**Check**:
1. **Device connected** via USB/serial/Bluetooth
2. **Correct port selected** (e.g., COM3, /dev/ttyUSB0)
3. **Drivers installed** (check device manager)
4. **Device powered on**
5. **No other software** using the device

**Solutions**:
1. **Check port**:
   - Windows: Device Manager → Ports
   - Linux: `ls /dev/tty*`
   - macOS: `ls /dev/cu.*`

2. **Set permissions** (Linux):
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

3. **Install driver**:
   - Check manufacturer website
   - FTDI, CH340, CP210x common

### AI Plugin Won't Work

**Symptom**: "API key invalid" or "Connection error"

**Solutions**:
1. **Set API key**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   export ANTHROPIC_API_KEY="sk-ant-..."
   export GOOGLE_API_KEY="..."
   ```

2. **Check internet connection**
3. **Verify key is valid**: Test on provider website
4. **Check rate limits**: May be temporarily blocked

---

## Performance Problems

### Toolkit is Slow

**Symptom**: Long load times, laggy interface

**Solutions**:

1. **Filter large datasets**:
   - Work with subsets
   - Use advanced filter to reduce rows

2. **Close unused plugins**:
   - Plugins → Manage Plugins
   - Disable what you don't need

3. **Clear cache**:
   - Tools → Clear Cache
   - Or delete `__pycache__/` folders

4. **Upgrade hardware**:
   - 8+ GB RAM recommended
   - SSD for faster file I/O

5. **Update packages**:
   ```bash
   pip install --upgrade numpy pandas matplotlib
   ```

### Out of Memory

**Symptom**: `MemoryError` or system freeze

**Solutions**:
1. **Reduce dataset size**:
   - Filter to essential samples
   - Remove unnecessary columns

2. **Close other applications**
3. **Increase virtual memory** (Windows)
4. **Use 64-bit Python** (not 32-bit)
5. **Add more RAM** if possible

### Plots Take Forever

**Symptom**: Creating plots is very slow

**Solutions**:
1. **Reduce point count**:
   - Subsample large datasets
   - Use hexbin instead of scatter for >10k points

2. **Use raster instead of vector**:
   - PNG instead of SVG for many points

3. **Disable anti-aliasing** in plot settings
4. **Update graphics drivers**

---

## Error Messages

### ImportError: DLL load failed

**Platform**: Windows

**Cause**: Missing Visual C++ Redistributable

**Solution**:
1. Download [VC++ Redistributable](https://support.microsoft.com/help/2977003)
2. Install both x86 and x64 versions
3. Restart computer

### AttributeError: module has no attribute 'X'

**Cause**: Version mismatch or outdated package

**Solution**:
```bash
# Update all packages
pip install -r requirements.txt --upgrade

# Or specific package
pip install --upgrade package-name
```

### KeyError: 'column_name'

**Cause**: Expected column doesn't exist

**Solution**:
1. Check column names in data
2. Standardize column names
3. Rename to match expected name

### ValueError: invalid literal for int()

**Cause**: Non-numeric data in numerical column

**Solution**:
1. Check for text in numbers column
2. Remove non-numeric characters
3. Convert column type

### FileNotFoundError

**Cause**: File or directory doesn't exist

**Solution**:
1. Check file path is correct
2. Use absolute paths, not relative
3. Check for typos

---

## Platform-Specific Issues

### Windows

**Problem**: Antivirus blocks toolkit

**Solution**:
- Add toolkit folder to exceptions
- Or temporarily disable antivirus

**Problem**: "Windows protected your PC" message

**Solution**:
- Click "More info" → "Run anyway"
- Or right-click → Properties → Unblock

### macOS

**Problem**: "Cannot be opened because developer cannot be verified"

**Solution**:
```bash
# Remove quarantine flag
xattr -d com.apple.quarantine Scientific-Toolkit.py

# Or right-click → Open (override)
```

**Problem**: Permission denied

**Solution**:
```bash
chmod +x Scientific-Toolkit.py
```

### Linux

**Problem**: Missing system libraries

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install python3-tk python3-dev build-essential

# Fedora
sudo dnf install python3-tkinter python3-devel gcc

# Arch
sudo pacman -S tk python-devel base-devel
```

**Problem**: Display issues

**Solution**:
```bash
export DISPLAY=:0
# Or check $DISPLAY variable
```

---

## Getting More Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Read relevant documentation**:
   - [USER_GUIDE.md](USER_GUIDE.md)
   - [INSTALLATION.md](INSTALLATION.md)
3. **Search existing issues** on GitHub
4. **Try with sample data** to isolate problem

### How to Report an Issue

When reporting bugs, include:

1. **System information**:
   ```bash
   python --version
   pip list
   uname -a  # Linux/macOS
   ver  # Windows
   ```

2. **Full error message**:
   - Copy entire traceback
   - Include context

3. **Steps to reproduce**:
   - Minimal example
   - Sample data if possible

4. **Expected vs actual behavior**

5. **Screenshots** if relevant

### Where to Get Help

- **Documentation**: Check docs/ folder
- **GitHub Issues**: [Report bugs](https://github.com/sefy-levy/scientific-toolkit/issues)
- **Discussions**: [Ask questions](https://github.com/sefy-levy/scientific-toolkit/discussions)
- **Email**: sefy76@gmail.com (for sensitive issues)

### Create Test Script

To help diagnose, create a minimal test:

```python
# test_minimal.py
import sys
print(f"Python: {sys.version}")

try:
    import numpy as np
    print(f"NumPy: {np.__version__}")
except ImportError as e:
    print(f"NumPy error: {e}")

try:
    import pandas as pd
    print(f"Pandas: {pd.__version__}")
except ImportError as e:
    print(f"Pandas error: {e}")

# Add other imports to test
```

Run and share output:
```bash
python test_minimal.py > test_output.txt 2>&1
```

---

## Quick Reference

### Reset Everything

If all else fails:

```bash
# Deactivate virtual environment
deactivate

# Delete virtual environment
rm -rf venv/

# Recreate
python3 -m venv venv
source venv/bin/activate

# Reinstall
pip install -r requirements.txt

# Clear caches
rm -rf __pycache__/ */__pycache__/

# Restart toolkit
python Scientific-Toolkit.py
```

### Check Versions

```bash
python --version
pip --version
pip list | grep numpy
pip list | grep pandas
pip list | grep matplotlib
```

### Common Commands

```bash
# Update toolkit
git pull origin main
pip install -r requirements.txt --upgrade

# Activate environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Check for issues
python -m pip check

# Verify installation
python -c "import scientific_toolkit; print('OK')"
```

---

## Still Having Problems?

Don't hesitate to reach out! The community is here to help.

**Contact**: sefy76@gmail.com

Please be patient - responses may take a few days, especially during busy periods.

---

*Troubleshooting Guide v1.0 | Last Updated: February 2026*
