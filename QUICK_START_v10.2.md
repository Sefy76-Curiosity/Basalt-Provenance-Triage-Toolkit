# ⚡ QUICK START GUIDE - v10.2

## **Get Started in 5 Minutes!**

---

## **STEP 1: Installation** (2 minutes)

```bash
# Install Python dependencies
pip install matplotlib pillow pandas openpyxl requests

# Optional: Install hardware support
pip install pyserial pynmea2 watchdog
```

---

## **STEP 2: Launch the Application** (30 seconds)

```bash
python Basalt_Provenance_Triage_Toolkit.py
```

You should see:
```
✓ Excel support: pandas available
✓ Plugin system available
✓ Classification engine available (v10.2)
```

---

## **STEP 3: Try the New Features!** (2 minutes)

### **A. Test Dynamic Classification:**

1. Click **Tools → Generate Demo Data** (creates 50 sample basalt artifacts)
2. Click **Tools → 🎯 Classify All (v10.2)**
3. Select **🎯 Basalt Provenance Triage (Egyptian–Sinai–Levantine)**
4. **BOOM!** All samples classified instantly!

### **B. Explore Other Classification Schemes:**

Try these:
- **🔬 Anhydrous Major-Oxide Normalization** (for TAS diagrams)
- **✅ Analytical Precision Filter** (for data quality)
- **🌋 Silica-Based Eruption Style Proxy** (for volcanology)
- **🪐 Fe/Mn Planetary Analog Ratio** (for Mars analog sites!)

### **C. Check Out Hardware Plugins:**

1. Click **Tools → 🔌 Manage Plugins**
2. Go to **🔌 Hardware Devices** tab
3. See 4 hardware plugins:
   - **📡 pXRF Analyzer** (13+ models supported!)
   - **📏 Digital Caliper** (numbers type automatically!)
   - **📍 GPS** (works with ALL GPS devices!)
   - **📁 File Monitor** (universal fallback!)

---

## **STEP 4: Create Your Own Classification Scheme!** (5 minutes)

1. Navigate to: `config/classification_schemes/`
2. Open `_TEMPLATE.json`
3. Copy it and rename: `my_custom_scheme.json`
4. Edit the rules:

```json
{
  "scheme_name": "My Custom Provenance Scheme",
  "version": "1.0",
  "author": "Your Name",
  "description": "My custom classification for X purpose",
  "icon": "🎯",
  "reference": "Your 2026 paper",
  
  "requires_fields": ["Zr_ppm", "Nb_ppm"],
  
  "classifications": [
    {
      "name": "HIGH ZR/NB",
      "color": "#4CAF50",
      "rules": [
        {
          "field": "Zr_Nb_Ratio",
          "operator": ">",
          "value": 15.0
        }
      ],
      "logic": "AND",
      "confidence_score": 0.85
    }
  ],
  
  "output_column_name": "My_Classification"
}
```

5. Save and restart the app
6. Your scheme appears in the **Classify All** menu!

---

## **STEP 5: Test Hardware Integration** (Optional)

### **If you have a pXRF analyzer:**

1. Connect it via USB
2. Click **Tools → 🔌 Manage Plugins**
3. Click **🔌 Hardware Devices** tab
4. Click **📡 pXRF Analyzer**
5. Select COM port and click **Connect**
6. Scan a sample → data imports automatically!
7. Click **Add to Sample** → Done!

### **If you have digital calipers:**

1. Connect USB caliper (Mitutoyo or generic)
2. Click **📏 Digital Caliper** plugin
3. Click in measurement field
4. Measure artifact
5. Press DATA button on caliper
6. **Number types automatically!** ✨
7. Click **Save to Sample** → Done!

### **If you have a GPS:**

1. Connect GPS via USB/Bluetooth
2. Click **📍 GPS** plugin
3. Select port and click **Connect**
4. Live position displays!
5. Click **Capture Location** → Coordinates saved!

---

## **🎯 COMMON WORKFLOWS**

### **Archaeological Excavation:**
```
1. Generate Demo Data (or import your CSV)
2. Tools → 🎯 Classify All
3. Select: Basalt Provenance Triage
4. Results: Egyptian, Sinai, Local classifications
5. File → Export → Google Earth
6. View provenance on map!
```

### **Data Quality Check:**
```
1. Import pXRF data
2. Tools → 🎯 Classify All
3. Select: Analytical Precision Filter
4. Results: Research Grade, Screening Grade, etc.
5. Filter out poor-quality data!
```

### **Mineral Exploration:**
```
1. Import field pXRF data
2. Tools → 🎯 Classify All
3. Select: Pathfinder Log-Transformation
4. Results: Ore Grade, Strong Anomaly, etc.
5. Export drill targets!
```

### **Planetary Science:**
```
1. Import Mars analog site data
2. Tools → 🎯 Classify All
3. Select: Fe/Mn Planetary Analog Ratio
4. Results: Martian Analog, Terrestrial, etc.
5. Send to NASA! 🚀
```

---

## **📊 KEYBOARD SHORTCUTS**

- **Ctrl+I** - Import CSV
- **Ctrl+S** - Export CSV
- **Ctrl+C** - Classify All (legacy)
- **Ctrl+G** - Generate Demo Data
- **Ctrl+T** - Show Statistics
- **F1** - Help

---

## **❓ TROUBLESHOOTING**

### **"Classification engine not available"**
- Make sure `classification_engine.py` is in the same folder as the main app
- Make sure `config/classification_schemes/` folder exists

### **"No schemes found"**
- Check that `config/classification_schemes/` contains `.json` files
- Make sure JSON files are valid (no syntax errors)

### **Hardware plugin doesn't connect:**
- **pXRF:** Check USB cable, try different COM port
- **Caliper:** Make sure it's in HID keyboard mode
- **GPS:** Check that GPS has fix (needs to see sky)
- **File Monitor:** Check that folder path is correct

### **"Missing dependencies"**
- Install: `pip install matplotlib pillow pandas openpyxl`
- For hardware: `pip install pyserial pynmea2 watchdog`

---

## **🚀 YOU'RE READY!**

**You now have:**
- ✅ 14 classification schemes at your fingertips
- ✅ 29+ hardware devices supported
- ✅ Ability to create custom classification schemes
- ✅ Professional citations for all methods
- ✅ 11+ scientific disciplines covered

**Welcome to the future of geochemical data analysis!** 🎉

---

**Need Help?**
- Press **F1** in the application
- Check **README_v10.2.md** for detailed docs
- Email: sefy76@gmail.com
- GitHub: https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit
