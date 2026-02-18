# ❓ Frequently Asked Questions

Honest answers to common questions about Scientific Toolkit.

---

## General Questions

### ⚠️ DISCLAIMER: Read This First

**This software is provided "AS IS" without any warranty.**

**Your responsibilities as a user:**
- **Validate all results** - Check that classifications make sense for your samples
- **Verify methods are appropriate** - Not every classification applies to every sample type
- **Check your input data** - Errors in your data = errors in results
- **Use scientific judgment** - This is a tool to assist you, not replace expertise
- **Report bugs and issues** - If something seems wrong, report it!

**This is scientific software in active development. You MUST:**
1. Understand the methods you're using (read the citations)
2. Verify results are reasonable for your samples
3. Cross-check critical results with other methods/tools
4. Report any bugs or unexpected behavior

**We rely on users to test and report issues.** Your bug reports help everyone.

→ [Report issues on GitLab](https://gitlab.com/sefy76/scientific-toolkit/-/issues)

---

## General Questions

### What is Scientific Toolkit?

A free, open-source desktop application (Python/Tkinter) for scientific data analysis across multiple domains: geochemistry, archaeology, soil science, meteoritics, and more. It combines data management, classification engines, hardware integration, and visualization in one tool.

### Who made this?

Created by Sefy Levy, based on the Basalt Provenance Triage Toolkit v10.2. Implements published scientific methods from dozens of researchers worldwide (see [CITATIONS.md](CITATIONS.md)).

### Is it really free?

Yes, completely free under CC BY-NC-SA 4.0 license. Free for research, education, museums, and non-commercial use forever.

### Can I use this for commercial work?

**Yes!** You can use Scientific Toolkit for commercial purposes - a mining company can use it for exploration, a consulting firm can use it for client work, a museum can use it for paid exhibitions, etc.

**What you CANNOT do:**
- Sell the software itself (charging for Scientific Toolkit)
- Incorporate the code into commercial products you sell
- Take the code and use it in proprietary software you're selling

**Example scenarios:**

✅ **ALLOWED:** Company uses toolkit to analyze soil samples for clients  
✅ **ALLOWED:** Museum uses it to classify artifacts for paid exhibitions  
✅ **ALLOWED:** Consultant uses it to generate reports for customers  
❌ **NOT ALLOWED:** Company sells "GeoAnalyzer Pro" that's based on this code  
❌ **NOT ALLOWED:** Charging $500 for the toolkit  
❌ **NOT ALLOWED:** Bundling it into a commercial software package you sell  

**If you want to use the code in a commercial product:** Contact sefy76@protonmail.com to discuss licensing.

---

## Capabilities

### What can Scientific Toolkit do?

- Import/manage scientific data (CSV, Excel)
- Run 41 classification engines (TAS diagrams, soil texture, bone diagenesis, etc.)
- Connect to hardware instruments (XRF, FTIR, GPS, etc.)
- Create publication-ready figures
- Statistical analysis (PCA, LDA, machine learning)
- Export results in various formats

See [QUICK_START.md](QUICK_START.md) for examples.

### What can't it do?

- Handle massive datasets (performance degrades >10,000 samples)
- Replace specialized commercial tools in their specific domains
- Provide enterprise-level support
- Run in a web browser (desktop only)
- Perform every analysis imaginable (focused on common needs)

### How does this compare to commercial software?

**Compared to ioGAS/GCDkit:** Free, broader scope (includes archaeology), hardware integration. But less polished UI, smaller user community.

**Compared to SPSS:** Free, includes geochemistry/archaeology. But SPSS has more advanced statistics and enterprise support.

**Compared to Python/R scripts:** GUI-based, no programming needed. But less flexible than writing custom code.

**Best use:** Budget-constrained researchers, students, teaching labs, cross-disciplinary projects, museums.

---

## Installation & Technical

### What are the system requirements?

- Python 3.8+ (3.10+ recommended)
- Windows 10/11, macOS 10.14+, or modern Linux
- 2 GB RAM (4 GB recommended)
- 50 MB disk space (+200 MB for full dependencies)

See [INSTALLATION.md](INSTALLATION.md) for details.

### Do I need to know Python?

No. This is a GUI application - you interact through menus and buttons, not code.

### Can I run this on a tablet or phone?

No. Desktop only (Windows/Mac/Linux). Not optimized for touch interfaces.

### Does it work offline?

Yes! All functionality works offline except:
- AI assistant plugins (require API keys and internet)
- Web search features
- Downloading additional dependencies

### How do I update to new versions?

```bash
cd scientific-toolkit
git pull origin main
pip install --upgrade -r requirements.txt
```

Your data and settings are preserved.

---

## Data & Files

### What file formats are supported?

**Import:**
- CSV (comma-separated)
- Excel (.xlsx, .xls)
- Tab-delimited text
- Hardware-specific formats (Bruker, Niton, etc.)

**Export:**
- CSV
- Excel
- PDF (figures)
- PNG/SVG (figures)
- KML (for Google Earth)

### Can I import my existing data?

Probably! If it's in CSV or Excel format with column headers, yes. The toolkit is flexible about column naming.

### Will this modify my original files?

No. Your original files are never changed. All work happens on imported copies in the application.

### Can I save my work and come back later?

Yes. Save projects as `.toolkit` files (JSON format). Reload anytime.

### How big can my datasets be?

**Recommended:** Under 1,000 samples for smooth performance  
**Maximum tested:** ~10,000 samples (slower but usable)  
**Not recommended:** 100,000+ samples (use specialized tools or databases)

---

## Classifications & Analysis

### Are the classification methods peer-reviewed?

Yes! We implement published methods from scientific literature. See [CITATIONS.md](CITATIONS.md) for all references.

Examples:
- TAS diagram: Le Bas et al. (1986)
- AFM diagram: Irvine & Baragar (1971)
- Meteorite shock stages: Stöffler et al. (1991)
- Bone diagenesis: Hedges et al. (1995)

### Can I cite Scientific Toolkit in papers?

Yes, please do! Cite both this software AND the original methods:

> "Samples were classified using the TAS diagram (Le Bas et al., 1986) as implemented in Scientific Toolkit v2.0 (Levy, 2026)."

See [CITATIONS.md](CITATIONS.md) for proper citation format.

### How accurate are the classifications?

**They implement published formulas, but YOU must validate the results.**

**What we guarantee:**
- Formulas/boundaries from published literature are implemented correctly
- Code logic follows the cited methods
- Calculations are mathematically accurate

**What we DO NOT guarantee:**
- That the method is appropriate for YOUR specific samples
- That your input data is correct
- That results are scientifically meaningful for your study
- That there are no bugs (software is complex!)

**Accuracy depends on:**
1. **Quality of your input data** - Bad data → bad results
2. **Appropriateness of method** - TAS diagram for sedimentary rocks? Wrong!
3. **Correct column mapping** - Did you map the right columns?
4. **Sample preparation** - Was your sample properly prepared?
5. **Your scientific judgment** - Does the result make sense?

**Best practices:**
- Read the citation for each classification engine you use
- Understand what the method does and its limitations
- Cross-validate critical results with other tools
- Check outliers and unexpected results carefully
- When in doubt, consult with experts in the field

**Found incorrect results or bugs?** → Report them! This helps everyone.

---

### How do I report bugs or issues?

**Please test and report issues!** This software improves through user feedback.

**Where to report:**
GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues

**What to include in your report:**
1. **What you expected** - What should have happened?
2. **What actually happened** - What did you see instead?
3. **Steps to reproduce** - How can we recreate the problem?
4. **Your system** - OS (Windows/Mac/Linux), Python version
5. **Data type** - What kind of data were you analyzing?
6. **Error messages** - Copy/paste any error text
7. **Screenshots** - If relevant

**Types of issues to report:**
- ✅ Incorrect calculations or classifications
- ✅ Software crashes or freezes
- ✅ Installation problems
- ✅ Hardware devices not working
- ✅ Documentation errors
- ✅ Feature requests
- ✅ Unexpected behavior

**Before reporting:**
- Check if issue already reported (search GitLab issues)
- Verify it's not a data quality problem
- Try with sample data to confirm it's a software issue

**Response time:**
This is open-source software maintained by volunteers. Response time varies. Be patient and provide good details to help us help you faster.

---

### Is this software tested?

**Honestly: Not as thoroughly as commercial software.**

**Current testing status:**
- Core functionality: Tested by developer
- Classification engines: Implemented from published formulas
- Hardware plugins: Tested on available devices
- Statistical methods: Using established libraries (scikit-learn, scipy)

**What's NOT fully tested:**
- All possible combinations of data types
- All hardware devices in all configurations
- Edge cases and unusual data
- Performance with very large datasets
- All operating system variations

**This is why we need YOU to test and report!**

Your real-world usage finds bugs that test cases miss. Every bug report makes the software better for everyone.

**Want to help test systematically?**
- Test with your specific instruments
- Try different data types
- Test on different operating systems
- Document workflows that work (or don't)
- Share example datasets (with permission)

Contact sefy76@protonmail.com if you want to be a systematic tester.

### Can I add my own classification schemes?

Yes! Classification engines are JSON files. Copy the template, add your rules, save in the engines folder. See developer documentation.

---

## Hardware Integration

### Which instruments are supported?

26 hardware integrations including:
- XRF/pXRF (Bruker Tracer, Niton, Vanta, benchtop)
- FTIR (Bruker, PerkinElmer, Thermo)
- XRD powder diffraction
- GPS devices (NMEA protocol)
- EC meters, ion meters
- Digital calipers
- **Universal file monitor** (works with ANY device that saves files)

See hardware plugin documentation for complete list.

### What if my instrument isn't supported?

Use the **File Monitor** plugin - it watches a folder and auto-imports any CSV/Excel files your instrument creates. Works with 95% of instruments.

### Do I need special drivers?

**Usually not.** Most devices work via:
- USB serial (XRF, GPS, meters) - standard drivers
- File monitoring (universal)

Some Windows devices may need manufacturer's USB driver.

---

## Visualization & Plotting

### What plot types are available?

- Scatter plots
- Ternary diagrams
- REE spider diagrams
- Bar charts, histograms
- Box plots
- Heatmaps, contour plots
- 3D scatter/surface
- GIS maps with terrain

### Can I customize the plots?

Yes! Apply templates (Nature, Science, AGU styles), adjust:
- Colors and markers
- Axis labels and ranges
- Grid and tick styles
- Font sizes and families
- Color schemes (including color-blind safe)

### Are plots publication-quality?

Yes. Export as:
- High-resolution PDF (vector, 300+ DPI)
- PNG (raster, adjustable DPI)
- SVG (vector, editable)

Journal-specific templates help match publication requirements.

---

## Statistical Analysis

### What statistical methods are included?

- Descriptive statistics (mean, median, std dev)
- Principal Component Analysis (PCA)
- Linear Discriminant Analysis (LDA)
- Random Forest classification
- Support Vector Machines (SVM)
- t-SNE dimensionality reduction
- K-means clustering
- Correlation matrices
- Basic regression

### Is this a replacement for SPSS or R?

No. It handles common analyses but isn't as comprehensive as dedicated statistical software. For advanced statistics, use R/SPSS. For common geochemistry/archaeology stats, Scientific Toolkit may be sufficient.

---

## AI Features

### How do the AI assistants work?

Optional plugins connect to AI services (Claude, ChatGPT, Gemini, etc.) via API. You can ask questions about your data and get interpretation suggestions.

**Requirements:**
- API key from the AI provider (most have free tiers)
- Internet connection

**Ollama option:** Run AI models locally (free, no API key, works offline)

### Do I need to pay for AI features?

Depends:
- **Ollama:** Completely free, runs on your computer
- **Others:** Most have free tiers with limits (e.g., Claude.ai free tier, OpenAI free trial)
- AI features are optional - core toolkit works fine without them

### Is my data sent to AI companies?

Only if you use AI assistant plugins AND explicitly ask them questions. Your data stays local otherwise. When using AI:
- Only data you explicitly query is sent
- Follows the AI provider's privacy policy
- Consider data sensitivity before using with confidential samples

---

## Errors & Troubleshooting

### "Module not found" errors

Missing dependency. Install it:
```bash
pip install [module-name]
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Classification returns no results

Common causes:
- Required columns missing (check classification description)
- Data is text instead of numbers
- Missing values (NaN) in critical columns
- Column names don't match expected format

Solution: Check the classification engine requirements and your column names.

### Application is slow

- Large dataset? Try filtering/paging
- Many plugins loaded? Close unused windows
- Low RAM? Close other programs
- Restart application to clear memory

### Hardware device not detected

- Check USB connection
- Check device is powered on
- Linux: Add user to dialout group
- Windows: May need device driver
- Try File Monitor as fallback

### Can't export figures

- Check you have write permission to output folder
- Try exporting to desktop first
- PDF export requires matplotlib backend - check installation

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

---

## Contributing & Development

### Can I contribute?

Yes! Contributions welcome:
- Report bugs (GitLab Issues)
- Request features
- Add classification engines
- Create hardware plugins
- Improve documentation
- Share example workflows

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### I found a bug. What should I do?

Open an issue on GitLab: https://gitlab.com/sefy76/scientific-toolkit/-/issues

Include:
- Operating system
- Python version
- Steps to reproduce
- Error message
- What you expected vs what happened

### Can I modify the code for my needs?

Yes! CC BY-NC-SA 4.0 license allows modifications. If you improve it, please:
- Share improvements back (contribute)
- Keep same license (ShareAlike requirement)
- Credit original (Attribution requirement)

### Is there developer documentation?

Basic documentation in code comments. More comprehensive developer guide planned. For now, code is reasonably self-documented with clear structure.

---

## Support & Community

### Where do I get help?

1. Check [QUICK_START.md](QUICK_START.md)
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Check this FAQ
4. Search GitLab Issues
5. Open new issue if problem persists

### Is there a user community?

Growing! Connect via:
- GitLab Issues/Discussions
- Email: sefy76@protonmail.com

No Discord/Slack yet, but planned if community grows.

### Do you offer training or workshops?

Not currently. Video tutorials are planned for future releases.

### Can I hire you for custom development?

Contact sefy76@protonmail.com to discuss custom features, consulting, or training.

---

## Misc

### Why was this created?

To provide free, integrated tools for budget-constrained researchers, students, and institutions. Many labs can't afford $5,000-8,000/year in software subscriptions.

### Will this always be free?

Yes. The software will always be free to use for anyone - researchers, students, companies, museums, consultants, anyone.

**What "free" means:**
- No cost to download or use
- No license fees
- No subscription costs
- Use it for any purpose (research, education, commercial work)

**What's restricted:**
- Cannot sell the software itself
- Cannot use the code in commercial products you sell

**Bottom line:** Free to use forever. Just don't try to sell it or profit from the code itself.

### What's the long-term plan?

Continue developing based on community needs:
- More classification engines
- Performance improvements
- Better documentation
- Video tutorials
- Possible peer-reviewed publication

Depends on community adoption and contribution.

### Can I donate to support development?

Not set up for donations currently. Best support:
- ⭐ Star on GitLab
- Share with colleagues
- Cite in publications
- Contribute code/documentation
- Report bugs

### Why Tkinter instead of modern framework?

Tkinter is:
- Built into Python (no extra dependencies)
- Cross-platform
- Lightweight
- Fast to develop
- Runs on older hardware

Yes, it looks dated. But it works reliably on any system with Python.

Future versions may offer web interface option.

---

## Still have questions?

- Email: sefy76@protonmail.com
- GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues
- Check documentation folder for more guides

---

<p align="center">
<i>This FAQ is updated based on real user questions</i>
</p>
