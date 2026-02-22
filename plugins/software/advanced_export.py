"""
Advanced Export Plugin for Basalt Provenance Toolkit
High-resolution publication-quality export functionality

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""
PLUGIN_INFO = {
      "category": "software",
    "id": "advanced_export",
    "name": "Publication Export",
    "description": "High-resolution PDF/EPS/SVG export for publications",
    "icon": "💾",
    "version": "1.0",
    "requires": ["matplotlib"],
    "author": "Sefy Levy"
}



import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    HAS_REQUIREMENTS = True
except ImportError as e:
    HAS_REQUIREMENTS = False
    IMPORT_ERROR = str(e)


class AdvancedExportPlugin:
    """Plugin for advanced export functionality"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None

    def open_window(self):  # ← FIXED: Renamed from open_export_window
        """Open advanced export interface"""
        if not HAS_REQUIREMENTS:
            messagebox.showerror(
                "Missing Dependencies",
                f"Advanced Export requires matplotlib:\n\n"
                f"Error: {IMPORT_ERROR}\n\n"
                f"Install with:\n"
                f"pip install matplotlib"
            )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Advanced Export - Publication Quality")
        self.window.geometry("580x480")

        self._create_export_interface()

    def _create_export_interface(self):
        """Create the export configuration interface"""
        # Header
        header = tk.Frame(self.window, bg="#673AB7")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="📄 Publication-Quality Export",
                font=("Arial", 16, "bold"),
                bg="#673AB7", fg="white",
                pady=5).pack()

        # Main content
        content = tk.Frame(self.window, padx=10, pady=8)
        content.pack(fill=tk.BOTH, expand=True)

        # === Data Export Section ===
        data_frame = tk.LabelFrame(content, text="📊 Data Export",
                                  font=("Arial", 11, "bold"),
                                  padx=10, pady=5)
        data_frame.pack(fill=tk.X, pady=5)

        tk.Label(data_frame,
                text="Export your complete dataset in multiple formats",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, pady=5)

        btn_frame1 = tk.Frame(data_frame)
        btn_frame1.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame1, text="Export as CSV",
                 command=lambda: self._export_data("csv"),
                 bg="#4CAF50", fg="white",
                 width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame1, text="Export as Excel",
                 command=lambda: self._export_data("excel"),
                 bg="#2196F3", fg="white",
                 width=20).pack(side=tk.LEFT, padx=5)

        btn_frame2 = tk.Frame(data_frame)
        btn_frame2.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame2, text="Export as JSON",
                 command=lambda: self._export_data("json"),
                 bg="#FF9800", fg="white",
                 width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame2, text="Export Summary Report",
                 command=self._export_summary_report,
                 bg="#9C27B0", fg="white",
                 width=20).pack(side=tk.LEFT, padx=5)

        # === Plot Export Section ===
        plot_frame = tk.LabelFrame(content, text="📈 High-Resolution Plot Export",
                                  font=("Arial", 11, "bold"),
                                  padx=10, pady=5)
        plot_frame.pack(fill=tk.X, pady=5)

        tk.Label(plot_frame,
                text="Export publication-ready figures with customizable settings",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, pady=5)

        # DPI selection
        dpi_frame = tk.Frame(plot_frame)
        dpi_frame.pack(fill=tk.X, pady=5)

        tk.Label(dpi_frame, text="Resolution (DPI):",
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)

        self.dpi_var = tk.IntVar(value=300)
        dpi_options = [150, 300, 600, 1200]

        for dpi in dpi_options:
            tk.Radiobutton(dpi_frame, text=str(dpi),
                          variable=self.dpi_var, value=dpi,
                          font=("Arial", 9)).pack(side=tk.LEFT, padx=10)

        # Format selection
        format_frame = tk.Frame(plot_frame)
        format_frame.pack(fill=tk.X, pady=5)

        tk.Label(format_frame, text="Format:",
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)

        self.format_var = tk.StringVar(value="PDF")
        formats = ["PDF", "PNG", "SVG", "EPS"]

        for fmt in formats:
            tk.Radiobutton(format_frame, text=fmt,
                          variable=self.format_var, value=fmt,
                          font=("Arial", 9)).pack(side=tk.LEFT, padx=10)

        tk.Label(plot_frame,
                text="⚠️ Note: To export plots, first generate them using the Advanced menu",
                font=("Arial", 8), fg="orange",
                wraplength=500,
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        # === Report Generation ===
        report_frame = tk.LabelFrame(content, text="📑 Report Generation",
                                    font=("Arial", 11, "bold"),
                                    padx=10, pady=5)
        report_frame.pack(fill=tk.X, pady=5)

        tk.Label(report_frame,
                text="Generate comprehensive analysis reports",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, pady=5)

        self.report_include_plots = tk.BooleanVar(value=True)
        tk.Checkbutton(report_frame, text="Include plots (if generated)",
                      variable=self.report_include_plots,
                      font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        self.report_include_samples = tk.BooleanVar(value=True)
        tk.Checkbutton(report_frame, text="Include sample details table",
                      variable=self.report_include_samples,
                      font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        self.report_include_stats = tk.BooleanVar(value=True)
        tk.Checkbutton(report_frame, text="Include statistical summaries",
                      variable=self.report_include_stats,
                      font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        tk.Button(report_frame, text="▶ Generate Full Report (PDF)",
                 command=self._generate_full_report,
                 bg="#E91E63", fg="white",
                 font=("Arial", 10, "bold"),
                 width=30, height=2).pack(pady=5)

        # === Citation ===
        citation_frame = tk.LabelFrame(content, text="📚 Citation",
                                      font=("Arial", 11, "bold"),
                                      padx=10, pady=5)
        citation_frame.pack(fill=tk.X, pady=5)

        citation_text = (
            "When publishing results from this toolkit, please cite:\n\n"
            "Levy, S. (2026). Scientific Toolkit v2.0.\n"
            "Zenodo. https://doi.org/10.5281/zenodo.18727756"
        )

        tk.Label(citation_frame, text=citation_text,
                font=("Arial", 8),
                justify=tk.LEFT,
                fg="#555").pack(anchor=tk.W)

        tk.Button(citation_frame, text="📋 Copy Citation",
                 command=self._copy_citation,
                 width=15).pack(anchor=tk.W, pady=5)

    def _export_data(self, format_type):
        """Export data in specified format"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples to export")
            return

        # Determine file extension
        extensions = {
            "csv": ".csv",
            "excel": ".xlsx",
            "json": ".json"
        }

        filetypes = {
            "csv": [("CSV Files", "*.csv"), ("All Files", "*.*")],
            "excel": [("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            "json": [("JSON Files", "*.json"), ("All Files", "*.*")]
        }

        filename = filedialog.asksaveasfilename(
            defaultextension=extensions[format_type],
            filetypes=filetypes[format_type],
            initialfile=f"basalt_data_export{extensions[format_type]}"
        )

        if not filename:
            return

        try:
            if format_type == "csv":
                self._export_csv(filename)
            elif format_type == "excel":
                self._export_excel(filename)
            elif format_type == "json":
                self._export_json(filename)

            messagebox.showinfo("Export Successful",
                              f"Data exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error",
                               f"Failed to export data:\n{e}")

    def _export_csv(self, filename):
        """Export to CSV"""
        import csv

        if not self.app.samples:
            return

        # Get all possible fieldnames
        fieldnames = set()
        for sample in self.app.samples:
            fieldnames.update(sample.keys())

        fieldnames = sorted(list(fieldnames))

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.app.samples)

    def _export_excel(self, filename):
        """Export to Excel"""
        try:
            import pandas as pd

            df = pd.DataFrame(self.app.samples)
            df.to_excel(filename, index=False, engine='openpyxl')
        except ImportError:
            messagebox.showerror("Missing Dependency",
                               "Excel export requires pandas and openpyxl.\n\n"
                               "Install with:\npip install pandas openpyxl")

    def _export_json(self, filename):
        """Export to JSON"""
        import json

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.app.samples, f, indent=2, ensure_ascii=False)

    def _export_summary_report(self):
        """Export a summary text report"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="basalt_summary_report.txt"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("BASALT PROVENANCE ANALYSIS - SUMMARY REPORT\n")
                f.write("=" * 70 + "\n\n")

                f.write(f"Total Samples: {len(self.app.samples)}\n\n")

                # Classification summary
                classifications = {}
                for sample in self.app.samples:
                    cls = sample.get('Final_Classification', 'Unclassified')
                    classifications[cls] = classifications.get(cls, 0) + 1

                f.write("CLASSIFICATION SUMMARY:\n")
                f.write("-" * 40 + "\n")
                for cls, count in sorted(classifications.items()):
                    f.write(f"{cls}: {count} samples\n")

                f.write("\n" + "=" * 70 + "\n")
                f.write("Generated by Basalt Provenance Triage Toolkit v11.0\n")
                f.write("Author: Sefy Levy | https://doi.org/10.5281/zenodo.18727756\n")
                f.write("=" * 70 + "\n")

            messagebox.showinfo("Export Successful",
                              f"Summary report saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error",
                               f"Failed to create report:\n{e}")

    def _generate_full_report(self):
        """Generate a comprehensive PDF report"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "PDF report generation requires reportlab:\n\n"
                "Install with:\n"
                "pip3 install reportlab\n\n"
                "OR use python -m pip install reportlab",
                parent=self.window
            )
            return

        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples to export!", parent=self.window)
            return

        # Get save path
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Save PDF Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            parent=self.window
        )

        if not path:
            return

        try:
            # Create PDF
            doc = SimpleDocTemplate(path, pagesize=letter,
                                   rightMargin=0.75*inch, leftMargin=0.75*inch,
                                   topMargin=1*inch, bottomMargin=0.75*inch)

            # Container for the 'Flowable' objects
            elements = []

            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=12,
                spaceBefore=12
            )

            # Title
            title = Paragraph("Basalt Provenance Triage Report", title_style)
            elements.append(title)
            elements.append(Spacer(1, 0.2*inch))

            # Metadata
            from datetime import datetime
            metadata_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
            metadata_text += f"Total Samples: {len(self.app.samples)}"
            metadata = Paragraph(metadata_text, styles['Normal'])
            elements.append(metadata)
            elements.append(Spacer(1, 0.3*inch))

            # Classification Summary
            heading = Paragraph("Classification Summary", heading_style)
            elements.append(heading)

            # Count classifications
            from collections import Counter
            classifications = [s.get('Final_Classification', s.get('Auto_Classification', 'UNKNOWN'))
                             for s in self.app.samples]
            class_counts = Counter(classifications)

            # Create table
            class_data = [['Classification', 'Count', 'Percentage']]
            for classification, count in sorted(class_counts.items(), key=lambda x: -x[1]):
                percentage = (count / len(self.app.samples)) * 100
                class_data.append([classification, str(count), f"{percentage:.1f}%"])

            class_table = Table(class_data, colWidths=[3.5*inch, 1*inch, 1*inch])
            class_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(class_table)
            elements.append(Spacer(1, 0.3*inch))

            # Sample List
            if self.report_include_samples.get():
                heading = Paragraph("Sample Details", heading_style)
                elements.append(heading)

                sample_data = [['Sample ID', 'Classification', 'Zr/Nb', 'Cr', 'Ni']]
                for sample in self.app.samples[:50]:  # Limit to 50 for PDF size
                    sid = sample.get('Sample_ID', 'Unknown')
                    classification = sample.get('Final_Classification',
                                               sample.get('Auto_Classification', 'UNKNOWN'))

                    # Get ratio
                    zr = sample.get('Zr_ppm', '')
                    nb = sample.get('Nb_ppm', '')
                    try:
                        if zr and nb and float(nb) > 0:
                            ratio = f"{float(zr)/float(nb):.2f}"
                        else:
                            ratio = '-'
                    except:
                        ratio = '-'

                    cr = sample.get('Cr_ppm', '-')
                    ni = sample.get('Ni_ppm', '-')

                    sample_data.append([sid, classification, ratio, str(cr), str(ni)])

                if len(self.app.samples) > 50:
                    sample_data.append(['...', f'({len(self.app.samples)-50} more samples)', '...', '...', '...'])

                sample_table = Table(sample_data, colWidths=[1.5*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                sample_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                elements.append(sample_table)
                elements.append(Spacer(1, 0.2*inch))

            # Statistics Summary
            if self.report_include_stats.get():
                elements.append(PageBreak())
                heading = Paragraph("Statistical Summary", heading_style)
                elements.append(heading)

                # Calculate basic stats for key elements
                elements_to_analyze = ['Zr_ppm', 'Nb_ppm', 'Cr_ppm', 'Ni_ppm', 'Ba_ppm', 'Rb_ppm']
                stats_data = [['Element', 'Mean', 'Median', 'Std Dev', 'Min', 'Max', 'N']]

                for elem in elements_to_analyze:
                    values = []
                    for s in self.app.samples:
                        val = s.get(elem)
                        if val:
                            try:
                                values.append(float(val))
                            except:
                                pass

                    if values:
                        import statistics
                        mean_val = statistics.mean(values)
                        median_val = statistics.median(values)
                        std_val = statistics.stdev(values) if len(values) > 1 else 0
                        min_val = min(values)
                        max_val = max(values)
                        n = len(values)

                        stats_data.append([
                            elem.replace('_ppm', ''),
                            f"{mean_val:.1f}",
                            f"{median_val:.1f}",
                            f"{std_val:.1f}",
                            f"{min_val:.1f}",
                            f"{max_val:.1f}",
                            str(n)
                        ])

                stats_table = Table(stats_data, colWidths=[0.9*inch]*7)
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colours.grey)
                ]))
                elements.append(stats_table)

            # Footer with citation
            elements.append(Spacer(1, 0.5*inch))
            citation_text = (
                "<b>Citation:</b><br/>"
                "Levy, S. (2026). Basalt Provenance Triage Toolkit (Version 10.1). "
                "Zenodo. https://doi.org/10.5281/zenodo.18727756"
            )
            citation = Paragraph(citation_text, styles['Normal'])
            elements.append(citation)

            # Build PDF
            doc.build(elements)

            messagebox.showinfo("PDF Generated",
                              f"Report saved successfully!\n\n{path}",
                              parent=self.window)

        except Exception as e:
            messagebox.showerror("PDF Error",
                               f"Error generating PDF:\n\n{str(e)}",
                               parent=self.window)


    def _copy_citation(self):
        """Copy citation to clipboard"""
        citation = (
            "Levy, S. (2026). Basalt Provenance Triage Toolkit: An Integrated "
            "Software Tool for Geochemical Classification of Archaeological Basalt "
            "Samples (Version 11.0). Zenodo. https://doi.org/10.5281/zenodo.18727756"
        )

        self.window.clipboard_clear()
        self.window.clipboard_append(citation)
        messagebox.showinfo("Citation Copied",
                          "Citation copied to clipboard!\n\n"
                          "Paste it into your publication's reference section.")

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = AdvancedExportPlugin(main_app)
    return plugin
