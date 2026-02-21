❓ Frequently Asked Questions

Honest answers to common questions about Scientific Toolkit.
Updated February 2026 to reflect current version (70 engines, 50 protocols, 67 plugins, 7 hardware suites)
⚠️ DISCLAIMER: Read This First

This software is provided "AS IS" without any warranty.

Your responsibilities as a user:

    Validate all results - Check that classifications make sense for your samples

    Verify methods are appropriate - Not every classification applies to every sample type

    Check your input data - Errors in your data = errors in results

    Use scientific judgment - This is a tool to assist you, not replace expertise

    Report bugs and issues - If something seems wrong, report it!

This is scientific software in active development. You MUST:

    Understand the methods you're using (read the citations)

    Verify results are reasonable for your samples

    Cross-check critical results with other methods/tools

    Report any bugs or unexpected behavior

We rely on users to test and report issues. Your bug reports help everyone.

→ Report issues on GitLab
📊 Quick Stats Reference
Category	Count
Classification Engines	70
Scientific Protocols	50
Software Plugins	37
Add-on Plugins	23
Hardware Suites	7
Total Plugins	67
Built-in Citations	200+
Lines of Code	~77,000
Active Development	2024-2026
General Questions
What is Scientific Toolkit?

A free, open-source desktop application (Python/Tkinter) for scientific data analysis across multiple domains: geochemistry, archaeology, soil science, meteoritics, and more. It combines data management, 70 classification engines, 50 scientific protocols, 67 plugins, and 7 hardware integration suites in one tool.
Who made this?

Created by Sefy Levy, based on the Basalt Provenance Triage Toolkit v10.2. Implements published scientific methods from 200+ researchers worldwide (see CITATIONS.md).
Is it really free?

Yes, completely free under CC BY-NC-SA 4.0 license. Free for research, education, museums, and commercial use forever.
Can I use this for commercial work?

Yes! You can use Scientific Toolkit for commercial purposes - a mining company can use it for exploration, a consulting firm can use it for client work, a museum can use it for paid exhibitions, etc.

What you CANNOT do:

    ❌ Sell the software itself (charging for Scientific Toolkit)

    ❌ Incorporate the code into commercial products you sell

    ❌ Take the code and use it in proprietary software you're selling

Example scenarios:
Scenario	Allowed?
Mining company uses toolkit to analyze soil samples for clients	✅ ALLOWED
Museum uses it to classify artifacts for paid exhibitions	✅ ALLOWED
Consultant uses it to generate reports for customers	✅ ALLOWED
Company sells "GeoAnalyzer Pro" based on this code	❌ NOT ALLOWED
Charging $500 for the toolkit download	❌ NOT ALLOWED
Bundling it into commercial software you sell	❌ NOT ALLOWED

If you want to use the code in a commercial product: Contact sefy76@gmail.com to discuss licensing.
🎯 Capabilities
What can Scientific Toolkit do?
Category	Capabilities
Classification	70 engines (TAS, AFM, REE, soil texture, bone diagenesis, meteorite shock, etc.)
Protocols	50 multi-stage workflows (Behrensmeyer, EPA, IUGS, Maresha, etc.)
Software Analysis	37 plugins (PCA/LDA, geochronology, isotope mixing, normative calculations)
Hardware	7 suites (barcode, elemental, mineralogy, physical, solution, spectroscopy, zooarch)
Plotting	23 add-ons (matplotlib, seaborn, ternary, GIS, ASCII, missingno)
AI Assistants	7 options (Claude, ChatGPT, Gemini, DeepSeek, Grok, Copilot, Ollama)

See QUICK_START.md for examples.
What can't it do?

    ❌ Handle massive datasets (performance degrades >10,000 samples)

    ❌ Replace specialized commercial tools in their single domains

    ❌ Provide enterprise-level support contracts

    ❌ Run in a web browser (desktop only)

    ❌ Perform every analysis imaginable (focused on common needs)

How does this compare to commercial software?
Tool	Cost	Strengths	Weaknesses
ioGAS	$2,000+/year	Polished UI, mining focus	Expensive, no hardware, no archaeology
GCDkit	Free	Excellent igneous petrology	R-based, steep learning curve, no hardware
PAST	Free	400+ statistical tests	1990s UI, limited geochemistry
SPSS	$1,500+/year	Advanced statistics	Expensive, no geochemistry
Scientific Toolkit	Free	Cross-disciplinary, hardware, GUI	Less polished UI, smaller community

Best use: Budget-constrained researchers, students, teaching labs, cross-disciplinary projects, museums, field work with portable instruments.
💻 Installation & Technical
What are the system requirements?
Component	Minimum	Recommended
Python	3.8	3.10+
OS	Windows 10, macOS 10.14, Linux	Latest versions
RAM	2 GB	4 GB (8 GB for large datasets)
Disk Space	50 MB	500 MB (with all plugins)
Display	1280×800	1920×1080

See INSTALLATION.md for details.
Do I need to know Python?

No. This is a GUI application - you interact through menus and buttons, not code. However, knowing Python helps if you want to:

    Create custom plugins

    Modify existing engines

    Export workflows as scripts

Can I run this on a tablet or phone?

No. Desktop only (Windows/Mac/Linux). Not optimized for touch interfaces.
Does it work offline?

Yes! All functionality works offline except:

    AI assistant plugins (require API keys and internet)

    Downloading additional dependencies via Plugin Manager

    Some online data sources (EarthChem, USGS)

How do I update to new versions?
bash

cd scientific-toolkit
git pull origin main
pip install --upgrade -r requirements.txt

Your data, projects, and settings are preserved.
What about the Plugin Manager?

The Plugin Manager (Advanced → Plugin Manager) handles:

    Discovering available plugins (67 total)

    Checking dependencies

    One-click installation

    Enabling/disabling plugins

    Uninstalling plugins

No manual pip commands needed for most plugins!
📁 Data & Files
What file formats are supported?

Import:

    ✅ CSV (any delimiter)

    ✅ Excel (.xlsx, .xls)

    ✅ Tab-delimited text

    ✅ Hardware-specific: Bruker, Niton, Olympus, SciAps, Thermo

    ✅ Spectral: .spa, .opj, .dpt, .wdf, .ngs, .jdx

    ✅ Images: .jpg, .png, .tif (for lithics/photos)

Export:

    ✅ CSV

    ✅ Excel

    ✅ JSON

    ✅ PDF (figures)

    ✅ PNG/SVG (figures)

    ✅ KML (for Google Earth)

    ✅ Shapefile (GIS)

Can I import my existing data?

Probably! If it's in CSV or Excel format with column headers, yes. The toolkit is flexible about column naming and will auto-map using chemical_elements.json.
Will this modify my original files?

No. Your original files are never changed. All work happens on imported copies in the application. The only files created are:

    Project files (.stproj) when you save

    Exported results when you choose to export

    Log files in config/

Can I save my work and come back later?

Yes. Save projects as .stproj files (JSON format). They store:

    All sample data

    Column order and structure

    Current filters and search terms

    Selected classification schemes

    UI state (tabs, page numbers)

    Window size and position

How big can my datasets be?
Size	Performance
<1,000 samples	✅ Smooth, instant
1,000-5,000 samples	⚠️ Good, slight delay on some operations
5,000-10,000 samples	⚠️ Slower but usable
>10,000 samples	❌ Not recommended

For large datasets, consider:

    Using filters to work with subsets

    Enabling pagination (50-100 samples per page)

    Using the SQL console for queries

    Exporting to R/Python for heavy processing

🧬 Classifications & Analysis
How many classification engines are there?

70 classification engines across 2 engines:
Engine Type	Count	Description
Classification Engine	70	Rule-based JSON schemes
Protocol Engine	50	Multi-stage workflows

These cover:

    Geochemistry (20+)

    Metamorphic petrology (5+)

    Sedimentology (12+)

    Geochronology (3+)

    Isotope geochemistry (3+)

    Environmental (8+)

    Soil science (8+)

    Archaeology (10+)

    Meteoritics (6+)

    Archaeometallurgy (5+)

    Hydrogeochemistry (5+)

    Provenance & tectonics (5+)

    Alteration & weathering (3+)

    Analytical QA/QC (4+)

Are the methods peer-reviewed?

Yes! We implement published methods from scientific literature. See CITATIONS.md for all 200+ references.

Key examples:

    TAS diagram: Le Bas et al. (1986)

    AFM diagram: Irvine & Baragar (1971)

    Meteorite shock stages: Stöffler et al. (1991)

    Bone diagenesis: Hedges et al. (1995)

    Geoaccumulation index: Müller (1969, 1981)

    U-Pb concordia: Wetherill (1956), Tera & Wasserburg (1972)

Can I cite Scientific Toolkit in papers?

Yes, please do! Cite both this software AND the original methods:

    "Samples were classified using the TAS diagram (Le Bas et al., 1986) as implemented in Scientific Toolkit v2.0 (Levy, 2026)."

Software citation:
text

Levy, S. (2026). Scientific Toolkit v2.0 [Computer software].
GitLab: https://gitlab.com/sefy76/scientific-toolkit
DOI: 10.5281/zenodo.18499129

See CITATIONS.md for complete format.
How accurate are the classifications?

They implement published formulas, but YOU must validate the results.

What we guarantee:

    ✅ Formulas/boundaries from published literature are implemented correctly

    ✅ Code logic follows the cited methods

    ✅ Calculations are mathematically accurate

What we DO NOT guarantee:

    ❌ That the method is appropriate for YOUR specific samples

    ❌ That your input data is correct

    ❌ That results are scientifically meaningful for your study

    ❌ That there are no bugs (software is complex!)

Accuracy depends on:

    Quality of your input data - Bad data → bad results

    Appropriateness of method - TAS diagram for sedimentary rocks? Wrong!

    Correct column mapping - Did you map the right columns?

    Sample preparation - Was your sample properly prepared?

    Your scientific judgment - Does the result make sense?

Best practices:

    Read the citation for each classification engine you use

    Understand what the method does and its limitations

    Cross-validate critical results with other tools

    Check outliers and unexpected results carefully

    When in doubt, consult with experts in the field

Found incorrect results or bugs? → Report them! This helps everyone.
What's the difference between Classification Engine and Protocol Engine?
Feature	Classification Engine	Protocol Engine
Purpose	Single-step classification	Multi-stage workflows
Rules	AND/OR logic on fields	Sequential stages with conditions
Output	Single classification	Multiple derived fields
Example	TAS diagram → "Basalt"	Behrensmeyer → weathering stage + flags
Count	70 schemes	50 protocols
Can I add my own classification schemes?

Yes! Classification engines are JSON files in engines/classification/:

    Copy _TEMPLATE.json to a new file

    Add your rules using supported operators (>, <, between, etc.)

    Save and restart

    Your scheme appears in the dropdown!

See engines/classification/README.md for details.
Can I add my own protocols?

Yes! Protocols are JSON files in engines/protocols/:

    Copy any existing protocol as template

    Define stages with rules

    Add conditions and outputs

    Save and restart

🔌 Hardware Integration
Which instruments are supported?

7 hardware suites supporting dozens of device models:
Suite	Devices Supported
Barcode/QR Scanner	Zebra, Honeywell, Datalogic, Socket, Inateck, Eyoyo (50+ models)
Elemental Geochemistry	SciAps X-550/X-505, Olympus Vanta/Delta, Bruker S1/Tracer, Thermo Niton, ICP-MS
Mineralogy	Any with RRUFF spectra – 5,185 minerals
Physical Properties	AGICO Kappabridge, Bartington MS2/MS3, ZH Instruments, Terraplus KT, Mitutoyo calipers, Sylvac Bluetooth, Mahr MarCal, iGaging
Solution Chemistry	Mettler Toledo, Thermo Orion, Hanna, Horiba LAQUA, YSI ProDSS, Hach, WTW (45+ models)
Spectroscopy	Thermo Nicolet, PerkinElmer, Bruker ALPHA, Agilent handheld, B&W Tek Raman, Ocean Optics, Avantes (50+ models)
Zooarchaeology	Mitutoyo calipers, Sylvac Bluetooth, Ohaus balances, Sartorius balances, Mettler Toledo balances, Emlid Reach GNSS, Dino-Lite microscopes

See hardware plugin documentation for complete lists.
What if my instrument isn't supported?

Option 1: File Monitor
The File Monitor plugin watches a folder and auto-imports any CSV/Excel files your instrument creates. Works with 95% of instruments.

Option 2: Universal Parser
Many hardware plugins include generic parsers that can handle:

    Any 2-column CSV (time, intensity)

    Any tabular data with headers

    Custom delimiter detection

Option 3: Create a plugin
If you're comfortable with Python, you can create a new hardware plugin following the pattern in existing ones.
Do I need special drivers?

Usually not. Most devices work via:

    USB serial (XRF, GPS, meters) - standard drivers built into OS

    USB HID (calipers) - no drivers needed

    Bluetooth (wireless devices) - built-in OS support

    File monitoring (universal) - no drivers

Some Windows devices may need manufacturer's USB serial driver (FTDI, Prolific, etc.).
Linux users: Permission issues?
bash

# Add user to dialout group for serial devices
sudo usermod -a -G dialout $USER
# Log out and back in

# For USB devices, may need udev rules
# See hardware-specific documentation

📈 Visualization & Plotting
What plot types are available?

Built-in (from add-on plugins):

    Scatter plots (matplotlib)

    Ternary diagrams (ternary-plotter)

    REE spider diagrams

    Bar charts, histograms

    Box plots, violin plots (seaborn)

    Heatmaps, contour plots

    3D scatter/surface

    GIS maps with terrain

    ASCII art plots (for CLI lovers)

    Missing data visualizations

From software plugins:

    PCA biplots

    LDA projections

    U-Pb concordia diagrams

    Ar-Ar age spectra

    KDE density plots

    MDS configurations

    Ternary mixing diagrams

Can I customize the plots?

Yes! Use the Plot Templates system:

    Create your plot

    Plot → Apply Template

    Choose from:

        Journal styles: Nature, Science, AGU, Elsevier, GSA

        Aesthetic: Color-blind safe, high contrast, B&W print

        Functional: Publication-ready, reviewer-friendly

        Discipline-specific: REE spider, TAS, stable isotopes

Adjust:

    Colors and markers

    Axis labels and ranges

    Grid and tick styles

    Font sizes and families

    Color schemes (including color-blind safe)

Are plots publication-quality?

Yes. Export as:

    PDF (vector, 300+ DPI) - best for journals

    SVG (vector, editable in Inkscape/Illustrator)

    PNG (raster, adjustable DPI)

    EPS (LaTeX compatible)

Journal-specific templates help match publication requirements.
📊 Statistical Analysis
What statistical methods are included?

From core:

    Descriptive statistics (mean, median, std dev, quartiles)

    Correlation matrices with significance

    t-tests, ANOVA, Mann-Whitney

From software plugins:

    PCA+LDA Explorer: PCA, LDA, PLS-DA, Random Forest, SVM, t-SNE, K-means

    Compositional Stats: CLR/ILR transforms, robust covariance, bootstrap

    Geochemical Explorer: Multivariate analysis, clustering

    Isotope Mixing: Binary/ternary mixing, Monte Carlo, Bayesian MCMC

    Geochronology: KDE, MDS, age calculations

Is this a replacement for SPSS or R?

No. It handles common analyses but isn't as comprehensive as dedicated statistical software.
Tool	Good For	Not Good For
SPSS	Complex surveys, social sciences	Geochemistry, hardware
R	Everything (with packages)	Steep learning curve
Scientific Toolkit	Common geo/archaeo stats	Advanced econometrics, psychometrics

For advanced statistics, use R/SPSS. For common geochemistry/archaeology stats, Scientific Toolkit may be sufficient.
🤖 AI Features
How do the AI assistants work?

Optional plugins connect to AI services via API:
Plugin	Provider	Requires
Claude AI	Anthropic	API key (free tier available)
ChatGPT	OpenAI	API key (free tier available)
Gemini AI	Google	API key (free tier available)
DeepSeek AI	DeepSeek	API key (free tier available)
Grok AI	xAI	API key
Copilot AI	Microsoft	API key
Ollama AI	Local	Ollama installation (free, no key)

You can ask questions about your data and get interpretation suggestions.
Do I need to pay for AI features?

Depends:

    Ollama: Completely free, runs on your computer (no internet needed)

    Others: Most have free tiers with limits (e.g., Claude.ai free tier, OpenAI free trial)

    AI features are optional - core toolkit works fine without them

Is my data sent to AI companies?

Only if you use AI assistant plugins AND explicitly ask them questions. Your data stays local otherwise.

When using AI:

    Only data you explicitly query is sent

    Follows the AI provider's privacy policy

    Consider data sensitivity before using with confidential samples

    Ollama keeps everything 100% local

🐞 Errors & Troubleshooting
"Module not found" errors

Missing dependency. Fix with:
bash

pip install [module-name]
# OR use Plugin Manager (auto-installs)

Classification returns no results

Common causes:

    Required columns missing (check engine description)

    Data is text instead of numbers

    Missing values (NaN) in critical columns

    Column names don't match expected format

Solution: Check the classification engine requirements in engines/classification/[scheme].json → requires_fields
Protocol fails

Common causes:

    Required fields missing

    Data type mismatch (text vs number)

    Stage conditions not met

Solution: Check protocol requirements in engines/protocols/[protocol].json → requires_fields
Application is slow

    Large dataset? Try filtering/paging (bottom right)

    Many plugins loaded? Close unused windows

    Low RAM? Close other programs

    Restart application to clear memory

    Check Task Manager/Activity Monitor for memory usage

Hardware device not detected

Checklist:

    USB cable connected?

    Device powered on?

    Correct port selected? (try different COM ports)

    Linux: User in dialout group?

    Windows: Driver installed?

    Try Hardware → File Monitor as fallback

Diagnostic:
python

# In Python console
import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(f"{p.device}: {p.description}")

Can't export figures

    Check write permission to output folder

    Try exporting to desktop first

    PDF export requires matplotlib - check installation

    Some formats need additional libraries (cairo for SVG)

Plugin Manager shows errors

    Check config/plugin_manager.log for details

    Ensure plugins folder is writable

    Some plugins need restart after install

🤝 Contributing & Development
Can I contribute?

Yes! Contributions welcome in all forms:
Contribution Type	How to Help
Bug reports	Open GitLab issue with details
Feature requests	Describe what you need
Classification engines	Add JSON schemes
Protocols	Create multi-stage workflows
Hardware plugins	Add new device support
Documentation	Improve guides, fix typos
Testing	Try on your hardware, report results
Translation	Add UI translations
Example workflows	Share with community

See CONTRIBUTING.md for guidelines.
I found a bug. What should I do?

    Search existing issues first (maybe already reported)

    Test with sample data to confirm it's not your data

    Open issue at https://gitlab.com/sefy76/scientific-toolkit/-/issues

Include:

    Operating system and version

    Python version (python --version)

    Steps to reproduce

    Error message (copy-paste)

    What you expected vs what happened

    Screenshots if relevant

Can I modify the code for my needs?

Yes! CC BY-NC-SA 4.0 license allows modifications. If you improve it, please:

    Share improvements back (contribute)

    Keep same license (ShareAlike requirement)

    Credit original (Attribution requirement)

Is there developer documentation?

    Code comments - Each plugin has detailed comments

    Classification schemes - JSON format documented in engines/classification/README.md

    Protocols - JSON format documented in engines/protocols/README.md

    Plugin system - See plugins/plugin_manager.py for registration

More comprehensive developer guide planned for v2.1.
👥 Support & Community
Where do I get help?

Self-help (fastest):

    QUICK_START.md - 5-minute guide

    INSTALLATION.md - Setup help

    This FAQ

    Search GitLab Issues

Community help:

    GitLab Issues/Discussions

    Email: sefy76@gmail.com

Paid support:

    Custom development: sefy76@gmail.com

    Training/workshops: Contact for availability

Is there a user community?

Growing! Connect via:

    GitLab Issues - Report bugs, request features

    GitLab Discussions - Ask questions, share workflows

    Email list - Announcements only (contact to join)

No Discord/Slack yet, but planned if community grows.
Do you offer training or workshops?

Not currently. Video tutorials are planned for future releases (target: mid-2026).
Can I hire you for custom development?

Yes! Contact sefy76@gmail.com to discuss:

    Custom plugins for your hardware

    New classification engines

    Integration with your systems

    Consulting on specific projects

💭 Misc
Why was this created?

To provide free, integrated tools for budget-constrained researchers, students, and institutions. Many labs can't afford $5,000-8,000/year in software subscriptions.

Real cost comparison:
Software	Annual Cost
ioGAS	~$2,000
SPSS	~$1,500
ArcGIS	~$1,600
MATLAB	~$2,150
Specialized petrology tools	~$1,000-3,000
Total commercial stack	$5,000-10,000/year
Scientific Toolkit	$0
Will this always be free?

Yes. The software will always be free to use for anyone - researchers, students, companies, museums, consultants, anyone.

What "free" means:

    No cost to download or use

    No license fees

    No subscription costs

    Use it for any purpose (research, education, commercial work)

What's restricted:

    Cannot sell the software itself

    Cannot use the code in commercial products you sell

Bottom line: Free to use forever. Just don't try to sell it or profit from the code itself.
What's the long-term plan?

Continue developing based on community needs:
Timeline	Plans
2026 Q2	Video tutorials, more classification engines
2026 Q3	Performance optimization for large datasets
2026 Q4	Peer-reviewed methods publication
2027	Community plugin repository, possible web interface

Depends on community adoption and contribution.
Can I donate to support development?

Not set up for donations currently. Best support:

    ⭐ Star on GitLab

    Share with colleagues

    Cite in publications

    Contribute code/documentation

    Report bugs

    Answer questions in Issues

Why Tkinter instead of modern framework?

Tkinter is:

    ✅ Built into Python (no extra dependencies)

    ✅ Cross-platform (Windows/Mac/Linux)

    ✅ Lightweight (runs on old hardware)

    ✅ Fast to develop

    ✅ Stable and reliable

Yes, it looks dated. But it works reliably on any system with Python, which is more important for scientific software than visual flair.

Future versions may offer a web interface option alongside the desktop app.
📝 Still have questions?

    Email: sefy76@gmail.com

    GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues

    Documentation: See /docs/ folder for more guides

📋 Quick Reference
Topic	Go To
Getting started	QUICK_START.md
Installation	INSTALLATION.md
Citations	CITATIONS.md
Troubleshooting	TROUBLESHOOTING.md
Plugin Guide	PLUGIN_GUIDE.md
Hardware Guide	HARDWARE_GUIDE.md
<p align="center"> <i>This FAQ is updated based on real user questions. Last updated: February 21, 2026</i> </p><p align="center"> <a href="README.md">← Back to Main</a> • <a href="QUICK_START.md">Quick Start</a> • <a href="INSTALLATION.md">Installation</a> • <a href="CITATIONS.md">Citations</a> </p>
