"""
Lithic Morphometrics Plugin for Basalt Provenance Toolkit v10.2+
ELLIPTICAL FOURIER ANALYSIS - EDGE DAMAGE QUANTIFICATION - USE-WEAR TRACKING
FROM PHOTO TO NUMBERS IN 3 CLICKS

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Version: 1.0 - Complete functional implementation
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "lithic_morphometrics",
    "name": "Lithic Morphometrics",
    "icon": "🪨",
    "description": "Extract artifact outlines, quantify edge damage, Fourier shape analysis",
    "version": "1.0.2",
    "requires": ["cv2", "skimage", "numpy", "scipy", "matplotlib", "PIL"],
    "author": "Sefy Levy"
}

import site
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from datetime import datetime
import os
import sys
from pathlib import Path

# Add user site-packages to path (fix for Python 3.13 on Linux)
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Also add the parent directory
user_base = os.path.dirname(user_site)
if user_base not in sys.path:
    sys.path.insert(0, user_base)

# ============ IMAGE PROCESSING IMPORTS ============
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from skimage import measure, filters, morphology, segmentation
    from skimage.feature import canny
    from skimage.transform import hough_circle, hough_circle_peaks
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False

try:
    from scipy import ndimage, signal
    from scipy.fft import fft, ifft
    from scipy.spatial import distance
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Polygon, Circle
    from matplotlib.path import Path as MPath
    from matplotlib.lines import Line2D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class LithicMorphometricsPlugin:
    """
    ============================================================================
    LITHIC MORPHOMETRICS v1.0
    ============================================================================
    Complete functional implementation with manual outline drawing tool.
    """

    # Shape classification colors
    SHAPE_COLORS = {
        "OPEN_BOWL": "#3498db",      # Blue
        "CLOSED_VESSEL": "#e74c3c",  # Red
        "PLATTER": "#f39c12",        # Orange
        "CUP": "#27ae60",            # Green
        "INDETERMINATE": "#95a5a6"   # Gray
    }

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.manual_window = None

        # Current image data
        self.original_image = None
        self.processed_image = None
        self.binary_mask = None
        self.contour = None
        self.outline_points = None
        self.display_image = None  # For manual outline

        # Manual outline variables
        self.manual_points = []
        self.point_markers = []
        self.line_objects = []
        self.current_point = None

        # Morphometric results
        self.fourier_coefficients = None
        self.edge_damage_index = None
        self.symmetry_score = None
        self.thickness_profile = None
        self.shape_classification = None

        # UI elements
        self.image_label = None
        self.canvas_frame = None
        self.results_text = None
        self.status_indicator = None
        self.stats_label = None
        self.threshold_var = None
        self.outline_info_label = None

        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if OpenCV and scikit-image are installed"""
        missing = []
        if not HAS_CV2:
            missing.append("opencv-python")
        if not HAS_SKIMAGE:
            missing.append("scikit-image")
        if not HAS_SCIPY:
            missing.append("scipy")
        if not HAS_MATPLOTLIB:
            missing.append("matplotlib")

        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    def _safe_import_message(self):
        """Show friendly import instructions"""
        if not self.dependencies_met:
            deps = " ".join(self.missing_deps)
            messagebox.showerror(
                "Missing Dependencies",
                f"Lithic Morphometrics requires:\n\n" +
                "\n".join(self.missing_deps) +
                f"\n\nInstall with:\npip install {deps}\n\n" +
                "On macOS/Linux, you may need:\nsudo apt-get install python3-opencv\n" +
                "or\nbrew install opencv"
            )
            return False
        return True

    def open_window(self):
        """Open the lithic morphometrics window"""
        if not self._safe_import_message():
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        # COMPACT DESIGN - 1200x700 (wider for image display)
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🪨 Lithic Morphometrics v1.0")
        self.window.geometry("1200x700")
        self.window.transient(self.app.root)

        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the lithic morphometrics interface"""

        # ============ TOP BANNER ============
        header = tk.Frame(self.window, bg="#8e44ad", height=45)  # Purple = shape analysis
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🪨", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="Lithic Morphometrics",
                font=("Arial", 14, "bold"), bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="Elliptical Fourier • Edge Damage • Use-Wear",
                font=("Arial", 8), bg="#8e44ad", fg="#f39c12").pack(side=tk.LEFT, padx=15)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8, "bold"),
                                        bg="#8e44ad", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN CONTENT ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                   sashwidth=4, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ============ LEFT PANEL - IMAGE DISPLAY ============
        left_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, width=600)

        # Image display area
        image_frame = tk.LabelFrame(left_panel, text="📸 ARTIFACT IMAGE",
                                   font=("Arial", 9, "bold"),
                                   bg="white", padx=5, pady=5)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.image_label = tk.Label(image_frame,
                                   text="No image loaded\n\nClick 'Load Image' to begin",
                                   font=("Arial", 11),
                                   bg="#f8f9fa", fg="#2c3e50",
                                   width=50, height=20,
                                   relief=tk.FLAT, borderwidth=2)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # Image controls
        image_controls = tk.Frame(image_frame, bg="white")
        image_controls.pack(fill=tk.X, pady=5)

        tk.Button(image_controls, text="📂 Load Image",
                 command=self._load_image,
                 bg="#3498db", fg="white",
                 font=("Arial", 9, "bold"),
                 width=12).pack(side=tk.LEFT, padx=5)

        tk.Button(image_controls, text="🔄 Reset",
                 command=self._reset_image,
                 bg="#95a5a6", fg="white",
                 font=("Arial", 9),
                 width=8).pack(side=tk.LEFT, padx=5)

        # ============ RIGHT PANEL - ANALYSIS CONTROLS ============
        right_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=550)

        # ============ STEP 1: PREPROCESSING ============
        preprocess_frame = tk.LabelFrame(right_panel, text="🔧 1. PREPROCESSING",
                                        font=("Arial", 9, "bold"),
                                        bg="#ecf0f1", padx=8, pady=6)
        preprocess_frame.pack(fill=tk.X, padx=8, pady=8)

        # Threshold control
        threshold_row = tk.Frame(preprocess_frame, bg="#ecf0f1")
        threshold_row.pack(fill=tk.X, pady=5)

        tk.Label(threshold_row, text="Threshold:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)

        self.threshold_var = tk.IntVar(value=127)
        threshold_scale = tk.Scale(threshold_row, from_=0, to=255,
                                  orient=tk.HORIZONTAL, variable=self.threshold_var,
                                  length=150, bg="#ecf0f1")
        threshold_scale.pack(side=tk.LEFT, padx=5)

        tk.Button(threshold_row, text="Apply",
                 command=self._apply_threshold,
                 bg="#3498db", fg="white",
                 font=("Arial", 8), width=6).pack(side=tk.LEFT, padx=5)

        # Smoothing
        smooth_row = tk.Frame(preprocess_frame, bg="#ecf0f1")
        smooth_row.pack(fill=tk.X, pady=5)

        tk.Label(smooth_row, text="Smooth:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)

        self.smooth_var = tk.IntVar(value=3)
        smooth_combo = ttk.Combobox(smooth_row,
                                   values=['1', '3', '5', '7', '9'],
                                   textvariable=self.smooth_var, width=4, state="readonly")
        smooth_combo.pack(side=tk.LEFT, padx=5)
        tk.Label(smooth_row, text="pixels", font=("Arial", 7),
                bg="#ecf0f1").pack(side=tk.LEFT)

        tk.Button(smooth_row, text="Smooth",
                 command=self._smooth_image,
                 bg="#3498db", fg="white",
                 font=("Arial", 8), width=6).pack(side=tk.LEFT, padx=20)

        # ============ STEP 2: OUTLINE EXTRACTION ============
        outline_frame = tk.LabelFrame(right_panel, text="✏️ 2. OUTLINE EXTRACTION",
                                     font=("Arial", 9, "bold"),
                                     bg="#ecf0f1", padx=8, pady=6)
        outline_frame.pack(fill=tk.X, padx=8, pady=8)

        # Auto-detect button
        tk.Button(outline_frame, text="🔍 Auto-Detect Outline",
                 command=self._auto_detect_outline,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 9, "bold"),
                 width=25, height=2).pack(pady=2)

        # Manual outline button - NOW FULLY FUNCTIONAL
        manual_frame = tk.Frame(outline_frame, bg="#ecf0f1")
        manual_frame.pack(fill=tk.X, pady=2)

        tk.Button(manual_frame, text="✂️ Manual Outline",
                 command=self._open_manual_outline,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 9),
                 width=15).pack(side=tk.LEFT, padx=2)

        # Instructions label
        tk.Label(manual_frame, text="(click points around artifact)",
                font=("Arial", 7, "italic"),
                bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.LEFT, padx=5)

        # Outline info
        self.outline_info_label = tk.Label(outline_frame,
                                          text="No outline detected",
                                          font=("Arial", 7, "italic"),
                                          bg="#ecf0f1", fg="#7f8c8d")
        self.outline_info_label.pack(pady=2)

        # ============ STEP 3: MORPHOMETRIC ANALYSIS ============
        morph_frame = tk.LabelFrame(right_panel, text="📐 3. MORPHOMETRIC ANALYSIS",
                                   font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        morph_frame.pack(fill=tk.X, padx=8, pady=8)

        # Fourier Analysis
        fourier_row = tk.Frame(morph_frame, bg="#ecf0f1")
        fourier_row.pack(fill=tk.X, pady=5)

        tk.Button(fourier_row, text="📊 Elliptical Fourier",
                 command=self._elliptical_fourier,
                 bg="#e67e22", fg="white",
                 font=("Arial", 8, "bold"),
                 width=20).pack(side=tk.LEFT, padx=2)

        self.fourier_status = tk.Label(fourier_row, text="⚪ Not computed",
                                      font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d")
        self.fourier_status.pack(side=tk.LEFT, padx=5)

        # Edge Damage
        edge_row = tk.Frame(morph_frame, bg="#ecf0f1")
        edge_row.pack(fill=tk.X, pady=5)

        tk.Button(edge_row, text="🔨 Edge Damage Index",
                 command=self._edge_damage_analysis,
                 bg="#e67e22", fg="white",
                 font=("Arial", 8, "bold"),
                 width=20).pack(side=tk.LEFT, padx=2)

        self.edge_status = tk.Label(edge_row, text="⚪ Not computed",
                                   font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d")
        self.edge_status.pack(side=tk.LEFT, padx=5)

        # Thickness Profile
        thick_row = tk.Frame(morph_frame, bg="#ecf0f1")
        thick_row.pack(fill=tk.X, pady=5)

        tk.Button(thick_row, text="📏 Thickness Profile",
                 command=self._thickness_profile,
                 bg="#e67e22", fg="white",
                 font=("Arial", 8, "bold"),
                 width=20).pack(side=tk.LEFT, padx=2)

        self.thick_status = tk.Label(thick_row, text="⚪ Not computed",
                                    font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d")
        self.thick_status.pack(side=tk.LEFT, padx=5)

        # ============ STEP 4: CLASSIFICATION ============
        class_frame = tk.LabelFrame(right_panel, text="🏷️ 4. SHAPE CLASSIFICATION",
                                   font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        class_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Button(class_frame, text="🎯 Classify Shape",
                 command=self._classify_shape,
                 bg="#27ae60", fg="white",
                 font=("Arial", 10, "bold"),
                 width=25, height=2).pack(pady=5)

        self.classification_label = tk.Label(class_frame,
                                            text="No classification",
                                            font=("Arial", 10, "bold"),
                                            bg="#ecf0f1", fg="#2c3e50")
        self.classification_label.pack(pady=5)

        # ============ RESULTS SUMMARY ============
        results_frame = tk.LabelFrame(right_panel, text="📋 MORPHOMETRIC REPORT",
                                     font=("Arial", 9, "bold"),
                                     bg="#ecf0f1", padx=8, pady=6)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Scrollable text area for results
        text_frame = tk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(text_frame, wrap=tk.WORD,
                                   font=("Courier", 9),
                                   yscrollcommand=scrollbar.set,
                                   bg="white", relief=tk.FLAT,
                                   height=10, padx=10, pady=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)

        # Initial message
        self.results_text.insert(tk.END, "🪨 LITHIC MORPHOMETRICS v1.0\n")
        self.results_text.insert(tk.END, "═" * 50 + "\n\n")
        self.results_text.insert(tk.END, "Load an artifact image and follow the steps:\n")
        self.results_text.insert(tk.END, "1. Preprocess (threshold/smooth)\n")
        self.results_text.insert(tk.END, "2. Extract outline (auto OR manual)\n")
        self.results_text.insert(tk.END, "3. Run morphometric analyses\n")
        self.results_text.insert(tk.END, "4. Classify shape\n\n")
        self.results_text.insert(tk.END, "📌 Why this matters:\n")
        self.results_text.insert(tk.END, "Chemistry tells you SOURCE.\n")
        self.results_text.insert(tk.END, "Shape tells you USE, WEAR, and CULTURE.\n")
        self.results_text.insert(tk.END, "Both together = COMPLETE PROVENANCE.\n")

        self.results_text.config(state=tk.DISABLED)

        # ============ BOTTOM STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                   text="Ready - Load an artifact image",
                                   font=("Arial", 8),
                                   bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # Export buttons
        tk.Button(status_bar, text="💾 Export Fourier Coeffs",
                 command=self._export_fourier,
                 font=("Arial", 7), bg="#3498db", fg="white",
                 padx=8).pack(side=tk.RIGHT, padx=5)

        tk.Button(status_bar, text="📊 Export Morphometrics",
                 command=self._export_morphometrics,
                 font=("Arial", 7), bg="#3498db", fg="white",
                 padx=8).pack(side=tk.RIGHT, padx=5)

    # ============ IMAGE LOADING & PREPROCESSING ============

    def _load_image(self):
        """Load an artifact image"""
        file_path = filedialog.askopenfilename(
            title="Select Artifact Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # Load image with OpenCV
            self.original_image = cv2.imread(file_path)
            if self.original_image is None:
                raise ValueError("Could not load image")

            # Convert to RGB for display
            self.original_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)

            # Convert to grayscale for processing
            self.processed_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)

            # Reset analysis state
            self.binary_mask = None
            self.contour = None
            self.outline_points = None
            self.fourier_coefficients = None
            self.edge_damage_index = None

            # Display image
            self._display_image(self.original_image)

            # Update status
            self.stats_label.config(text=f"Loaded: {os.path.basename(file_path)}")
            self.status_indicator.config(text="● IMAGE LOADED", fg="#f39c12")

            # Log
            self._log_result(f"📸 Image loaded: {os.path.basename(file_path)}")
            self._log_result(f"   Dimensions: {self.original_image.shape[1]}x{self.original_image.shape[0]} pixels")

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load image:\n{str(e)}")

    def _display_image(self, image):
        """Display image in the UI"""
        if image is None:
            return

        # Resize for display while maintaining aspect ratio
        max_width = 550
        max_height = 400

        h, w = image.shape[:2]
        scale = min(max_width / w, max_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(image, (new_w, new_h))

        # Convert to PhotoImage
        from PIL import Image, ImageTk
        if len(resized.shape) == 3:
            pil_image = Image.fromarray(resized)
        else:
            pil_image = Image.fromarray(resized).convert('L')

        photo = ImageTk.PhotoImage(pil_image)

        # Update label
        self.image_label.config(image=photo, text="", width=new_w, height=new_h)
        self.image_label.image = photo  # Keep reference

    def _apply_threshold(self):
        """Apply binary threshold to isolate artifact"""
        if self.processed_image is None:
            messagebox.showwarning("No Image", "Load an image first!")
            return

        # Apply threshold
        _, self.binary_mask = cv2.threshold(
            self.processed_image,
            self.threshold_var.get(),
            255,
            cv2.THRESH_BINARY_INV
        )

        # Clean up mask
        kernel = np.ones((3, 3), np.uint8)
        self.binary_mask = cv2.morphologyEx(self.binary_mask, cv2.MORPH_OPEN, kernel)
        self.binary_mask = cv2.morphologyEx(self.binary_mask, cv2.MORPH_CLOSE, kernel)

        # Display result
        self._display_image(self.binary_mask)

        self._log_result(f"✓ Threshold applied: {self.threshold_var.get()}")

    def _smooth_image(self):
        """Apply Gaussian smoothing"""
        if self.processed_image is None:
            messagebox.showwarning("No Image", "Load an image first!")
            return

        kernel_size = int(self.smooth_var.get())
        if kernel_size % 2 == 0:
            kernel_size += 1

        self.processed_image = cv2.GaussianBlur(
            self.processed_image,
            (kernel_size, kernel_size),
            0
        )

        self._display_image(self.processed_image)
        self._log_result(f"✓ Smoothing applied: {kernel_size}px Gaussian")

    def _reset_image(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.processed_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            self._display_image(self.original_image)
            self.binary_mask = None
            self.contour = None
            self.outline_points = None
            self.outline_info_label.config(text="No outline detected", fg="#7f8c8d")
            self._log_result("↺ Reset to original image")

    # ============ OUTLINE EXTRACTION ============

    def _auto_detect_outline(self):
        """Auto-detect artifact outline using contour detection"""
        if self.binary_mask is None:
            # Try to create binary mask with default threshold
            if self.processed_image is not None:
                _, self.binary_mask = cv2.threshold(self.processed_image, 127, 255, cv2.THRESH_BINARY_INV)
            else:
                messagebox.showwarning("No Image", "Load and threshold an image first!")
                return

        # Find contours
        contours, _ = cv2.findContours(
            self.binary_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            messagebox.showwarning("No Outline", "Could not detect artifact outline. Try adjusting threshold.")
            return

        # Get largest contour (the artifact)
        self.contour = max(contours, key=cv2.contourArea)

        # Simplify contour
        epsilon = 0.001 * cv2.arcLength(self.contour, True)
        self.contour = cv2.approxPolyDP(self.contour, epsilon, True)

        # Extract points
        self.outline_points = self.contour.squeeze()
        if len(self.outline_points.shape) == 1:
            self.outline_points = self.outline_points.reshape(-1, 2)

        # Draw outline on copy of original
        display_img = self.original_image.copy()
        cv2.drawContours(display_img, [self.contour], -1, (255, 0, 0), 3)

        self._display_image(display_img)

        # Update info
        n_points = len(self.outline_points)
        perimeter = cv2.arcLength(self.contour, True)
        area = cv2.contourArea(self.contour)

        self.outline_info_label.config(
            text=f"✓ Auto outline: {n_points} points, perimeter: {perimeter:.1f}px, area: {area:.1f}px²",
            fg="#27ae60"
        )

        self._log_result(f"✓ Auto outline extracted")
        self._log_result(f"   Points: {n_points}, Perimeter: {perimeter:.1f}px")
        self._log_result(f"   Area: {area:.1f}px², Circularity: {4*np.pi*area/perimeter**2:.3f}")

    # ============ MANUAL OUTLINE TOOL - FULLY FUNCTIONAL ============

    def _open_manual_outline(self):
        """Open manual outline drawing tool"""
        if self.original_image is None:
            messagebox.showwarning("No Image", "Load an image first!")
            return

        # Close existing manual window if open
        if self.manual_window and self.manual_window.winfo_exists():
            self.manual_window.destroy()

        # Create new window
        self.manual_window = tk.Toplevel(self.window)
        self.manual_window.title("✏️ Manual Outline Drawing")
        self.manual_window.geometry("800x700")
        self.manual_window.transient(self.window)

        # Reset points
        self.manual_points = []
        self.point_markers = []
        self.line_objects = []

        # Create matplotlib figure
        fig, self.manual_ax = plt.subplots(figsize=(8, 6))

        # Display image
        self.manual_ax.imshow(self.original_image)
        self.manual_ax.set_title("Click points around artifact edge. Press 'Close Shape' when done.",
                                fontsize=10, fontweight='bold')
        self.manual_ax.axis('off')

        # Connect click event
        self.cid = fig.canvas.mpl_connect('button_press_event', self._on_click)

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, self.manual_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control buttons
        control_frame = tk.Frame(self.manual_window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(control_frame, text="🔴 Close Shape",
                 command=self._close_manual_shape,
                 bg="#27ae60", fg="white",
                 font=("Arial", 10, "bold"),
                 width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="↺ Clear Points",
                 command=self._clear_manual_points,
                 bg="#e74c3c", fg="white",
                 font=("Arial", 10),
                 width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="✔ Accept Outline",
                 command=self._accept_manual_outline,
                 bg="#3498db", fg="white",
                 font=("Arial", 10, "bold"),
                 width=15).pack(side=tk.LEFT, padx=5)

        # Instructions
        instr_frame = tk.Frame(self.manual_window, bg="#f0f0f0")
        instr_frame.pack(fill=tk.X, padx=10, pady=5)

        instructions = """
        Instructions:
        1. Click points around the artifact edge in clockwise order
        2. Points will be connected with lines as you click
        3. Click 'Close Shape' to connect last point to first
        4. Click 'Accept Outline' when finished
        5. Use 'Clear Points' to start over
        """

        tk.Label(instr_frame, text=instructions,
                font=("Arial", 9),
                justify=tk.LEFT,
                bg="#f0f0f0").pack(pady=5)

        self.point_count_label = tk.Label(instr_frame,
                                         text="Points: 0",
                                         font=("Arial", 9, "bold"),
                                         bg="#f0f0f0")
        self.point_count_label.pack(pady=2)

        self.manual_ax.figure.canvas.draw()
        self.manual_canvas = canvas

    def _on_click(self, event):
        """Handle mouse click in manual outline window"""
        if event.inaxes != self.manual_ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        # Add point
        point = (event.xdata, event.ydata)
        self.manual_points.append(point)

        # Plot point
        marker = self.manual_ax.plot(event.xdata, event.ydata, 'ro', markersize=4)[0]
        self.point_markers.append(marker)

        # Draw line from previous point
        if len(self.manual_points) > 1:
            prev_point = self.manual_points[-2]
            line = self.manual_ax.plot([prev_point[0], event.xdata],
                                       [prev_point[1], event.ydata],
                                       'r-', linewidth=1.5)[0]
            self.line_objects.append(line)

        # Update display
        self.manual_ax.figure.canvas.draw()
        self.point_count_label.config(text=f"Points: {len(self.manual_points)}")

    def _close_manual_shape(self):
        """Connect last point to first point"""
        if len(self.manual_points) < 3:
            messagebox.showwarning("Not Enough Points",
                                  "Need at least 3 points to create a shape!")
            return

        # Draw line from last point to first
        first = self.manual_points[0]
        last = self.manual_points[-1]
        line = self.manual_ax.plot([last[0], first[0]],
                                   [last[1], first[1]],
                                   'r-', linewidth=2)[0]
        self.line_objects.append(line)

        # Change point colors to indicate closed shape
        for marker in self.point_markers:
            marker.set_color('green')
            marker.set_markersize(5)

        self.manual_ax.figure.canvas.draw()
        self._log_result("✓ Manual shape closed")

    def _clear_manual_points(self):
        """Clear all manually drawn points"""
        self.manual_points = []

        # Remove all plotted elements
        for marker in self.point_markers:
            marker.remove()
        for line in self.line_objects:
            line.remove()

        self.point_markers = []
        self.line_objects = []

        self.manual_ax.figure.canvas.draw()
        self.point_count_label.config(text="Points: 0")

    def _accept_manual_outline(self):
        """Accept the manually drawn outline"""
        if len(self.manual_points) < 3:
            messagebox.showwarning("Not Enough Points",
                                  "Need at least 3 points to create an outline!")
            return

        # Ensure shape is closed
        if np.linalg.norm(np.array(self.manual_points[0]) - np.array(self.manual_points[-1])) > 1:
            # Close the shape if not already closed
            self.manual_points.append(self.manual_points[0])

        # Convert to numpy array
        self.outline_points = np.array(self.manual_points)

        # Create contour for compatibility
        self.contour = self.outline_points.reshape((-1, 1, 2)).astype(np.int32)

        # Draw outline on main display
        display_img = self.original_image.copy()
        cv2.polylines(display_img, [self.contour], True, (255, 0, 0), 3)
        self._display_image(display_img)

        # Update info
        n_points = len(self.outline_points)
        perimeter = np.sum(np.sqrt(np.sum(np.diff(self.outline_points, axis=0)**2, axis=1)))

        # Close the perimeter calculation
        closed_perimeter = perimeter + np.linalg.norm(self.outline_points[-1] - self.outline_points[0])

        self.outline_info_label.config(
            text=f"✓ Manual outline: {n_points} points, perimeter: {closed_perimeter:.1f}px",
            fg="#27ae60"
        )

        self._log_result(f"✓ Manual outline extracted with {n_points} points")
        self._log_result(f"   Perimeter: {closed_perimeter:.1f}px")

        # Close manual window
        self.manual_window.destroy()
        self.manual_window = None

    # ============ MORPHOMETRIC ANALYSIS ============

    def _elliptical_fourier(self):
        """
        Elliptical Fourier Analysis - Quantify shape as mathematical harmonics
        """
        if self.outline_points is None:
            messagebox.showwarning("No Outline", "Extract an outline first!")
            return

        try:
            # Ensure points are ordered clockwise
            if not self._is_clockwise(self.outline_points):
                self.outline_points = self.outline_points[::-1]

            # Normalize outline (center, scale, rotation)
            normalized = self._normalize_outline(self.outline_points)

            # Compute Fourier coefficients (up to 20 harmonics)
            n_harmonics = 20
            coeffs = self._compute_fourier_coeffs(normalized, n_harmonics)

            self.fourier_coefficients = coeffs

            # Reconstruct shape from coefficients
            reconstructed = self._reconstruct_shape(coeffs, n_points=100)

            # Calculate power spectrum (variance explained)
            power = np.array([c['A']**2 + c['B']**2 + c['C']**2 + c['D']**2 for c in coeffs])
            total_power = np.sum(power)
            cumulative = np.cumsum(power) / total_power * 100

            # Display reconstruction
            self._plot_fourier_reconstruction(reconstructed, cumulative)

            # Update status
            self.fourier_status.config(text=f"✅ {n_harmonics} harmonics", fg="#27ae60")

            self._log_result(f"📊 Elliptical Fourier Analysis")
            self._log_result(f"   Harmonics: {n_harmonics}")
            self._log_result(f"   Power: H1={power[0]/total_power*100:.1f}%, "
                           f"H1-5={cumulative[4]:.1f}%, H1-10={cumulative[9]:.1f}%")

        except Exception as e:
            messagebox.showerror("Fourier Error", f"Could not compute Fourier coefficients:\n{str(e)}")

    def _is_clockwise(self, points):
        """Check if polygon points are ordered clockwise"""
        if len(points) < 3:
            return True

        # Shoelace formula
        x = points[:, 0]
        y = points[:, 1]
        area = np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])
        if len(points) > 2:
            area += x[-1] * y[0] - x[0] * y[-1]

        return area < 0

    def _normalize_outline(self, points):
        """
        Normalize outline for Fourier analysis:
        1. Center at origin
        2. Scale to unit perimeter
        3. Rotate so first harmonic phase is zero
        """
        # Center
        center = np.mean(points, axis=0)
        centered = points - center

        # Scale to unit perimeter
        perimeter = np.sum(np.sqrt(np.sum(np.diff(points, axis=0)**2, axis=1)))
        scaled = centered / perimeter

        return scaled

    def _compute_fourier_coeffs(self, points, n_harmonics=20):
        """
        Compute Elliptical Fourier Descriptors
        Kuhl & Giardina (1982) method
        """
        n = len(points)
        t = np.linspace(0, 2*np.pi, n)

        # Compute differences
        dx = np.diff(points[:, 0])
        dy = np.diff(points[:, 1])
        dt = np.diff(t)

        coeffs = []

        for h in range(1, n_harmonics + 1):
            A = 0
            B = 0
            C = 0
            D = 0

            for i in range(n-1):
                t1 = t[i]
                t2 = t[i+1]

                # Compute coefficients
                A += dx[i] / dt[i] * (np.cos(h*t2) - np.cos(h*t1)) / (h**2)
                B += dx[i] / dt[i] * (np.sin(h*t2) - np.sin(h*t1)) / (h**2)
                C += dy[i] / dt[i] * (np.cos(h*t2) - np.cos(h*t1)) / (h**2)
                D += dy[i] / dt[i] * (np.sin(h*t2) - np.sin(h*t1)) / (h**2)

            # Normalize
            A = A * 2 / n
            B = B * 2 / n
            C = C * 2 / n
            D = D * 2 / n

            coeffs.append({
                'harmonic': h,
                'A': A, 'B': B, 'C': C, 'D': D
            })

        return coeffs

    def _reconstruct_shape(self, coeffs, n_points=100):
        """Reconstruct shape from Fourier coefficients"""
        t = np.linspace(0, 2*np.pi, n_points)
        x = np.zeros(n_points)
        y = np.zeros(n_points)

        for c in coeffs:
            h = c['harmonic']
            x += c['A'] * np.cos(h*t) + c['B'] * np.sin(h*t)
            y += c['C'] * np.cos(h*t) + c['D'] * np.sin(h*t)

        return np.column_stack([x, y])

    def _plot_fourier_reconstruction(self, reconstructed, cumulative):
        """Plot Fourier reconstruction in new window"""
        if not HAS_MATPLOTLIB:
            return

        plot_window = tk.Toplevel(self.window)
        plot_window.title("📊 Elliptical Fourier Reconstruction")
        plot_window.geometry("700x500")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Plot original vs reconstructed
        ax1.plot(self.outline_points[:, 0], self.outline_points[:, 1],
                'b-', linewidth=2, alpha=0.5, label='Original')
        ax1.plot(reconstructed[:, 0], reconstructed[:, 1],
                'r--', linewidth=2, label='Reconstructed')
        ax1.set_aspect('equal')
        ax1.set_title('Elliptical Fourier Reconstruction', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot cumulative power
        harmonics = np.arange(1, len(cumulative)+1)
        ax2.bar(harmonics[:10], cumulative[:10], color='#3498db', alpha=0.7)
        ax2.axhline(y=95, color='red', linestyle='--', alpha=0.5, label='95% threshold')
        ax2.set_xlabel('Harmonic')
        ax2.set_ylabel('Cumulative Power (%)')
        ax2.set_title('Shape Information by Harmonic', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _edge_damage_analysis(self):
        """
        Edge Damage Index - Quantify rim wear and chipping
        Measures irregularity along the outline
        """
        if self.outline_points is None:
            messagebox.showwarning("No Outline", "Extract an outline first!")
            return

        # Compute curvature along outline
        curvature = self._compute_curvature(self.outline_points)

        # Edge damage = high curvature points
        threshold = np.mean(curvature) + np.std(curvature)
        damage_points = curvature > threshold

        self.edge_damage_index = np.sum(damage_points) / len(curvature) * 100

        # Visualize damage
        self._plot_edge_damage(curvature, damage_points)

        # Update status
        self.edge_status.config(text=f"✅ EDI: {self.edge_damage_index:.1f}%", fg="#27ae60")

        self._log_result(f"🔨 Edge Damage Analysis")
        self._log_result(f"   Edge Damage Index: {self.edge_damage_index:.1f}%")

        if self.edge_damage_index < 10:
            self._log_result(f"   Interpretation: Minimal wear (ritual use?)")
        elif self.edge_damage_index < 25:
            self._log_result(f"   Interpretation: Moderate wear (regular use)")
        else:
            self._log_result(f"   Interpretation: Heavy wear (intensive use)")

    def _compute_curvature(self, points):
        """Compute curvature along polygon"""
        n = len(points)
        curvature = np.zeros(n)

        for i in range(n):
            # Get three consecutive points
            p1 = points[(i-1) % n]
            p2 = points[i]
            p3 = points[(i+1) % n]

            # Vectors
            v1 = p1 - p2
            v2 = p3 - p2

            # Angle between vectors
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
            cos_angle = np.clip(cos_angle, -1, 1)
            angle = np.arccos(cos_angle)

            curvature[i] = np.pi - angle

        return curvature

    def _plot_edge_damage(self, curvature, damage_points):
        """Plot edge damage visualization"""
        if not HAS_MATPLOTLIB:
            return

        plot_window = tk.Toplevel(self.window)
        plot_window.title("🔨 Edge Damage Analysis")
        plot_window.geometry("800x500")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Plot outline with damage highlighted
        ax1.plot(self.outline_points[:, 0], self.outline_points[:, 1],
                'k-', linewidth=1, alpha=0.3)
        ax1.scatter(self.outline_points[damage_points, 0],
                   self.outline_points[damage_points, 1],
                   c='red', s=30, alpha=0.7, label=f'Damage (EDI={self.edge_damage_index:.1f}%)')
        ax1.set_aspect('equal')
        ax1.set_title('Edge Damage Distribution', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot curvature profile
        theta = np.linspace(0, 360, len(curvature))
        ax2.plot(theta, curvature, 'b-', linewidth=1)
        ax2.fill_between(theta, 0, curvature, alpha=0.3, color='red',
                        where=(curvature > np.mean(curvature)+np.std(curvature)))
        ax2.axhline(y=np.mean(curvature), color='gray', linestyle='--', alpha=0.5)
        ax2.axhline(y=np.mean(curvature)+np.std(curvature), color='red', linestyle='--', alpha=0.5)
        ax2.set_xlabel('Position along outline (degrees)')
        ax2.set_ylabel('Curvature (radians)')
        ax2.set_title('Edge Curvature Profile', fontweight='bold')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _thickness_profile(self):
        """
        Thickness Profile - Extract vessel wall thickness variation
        Requires scale reference in image
        """
        messagebox.showinfo(
            "Thickness Profile",
            "Thickness Profile feature in development.\n\n"
            "Current functionality:\n"
            "• Manual outline drawing (working)\n"
            "• Fourier analysis (working)\n"
            "• Edge damage quantification (working)\n\n"
            "Thickness measurement will be added in v1.1"
        )

    def _classify_shape(self):
        """
        Classify artifact shape based on Fourier coefficients
        """
        if self.fourier_coefficients is None:
            messagebox.showwarning("No Fourier Data",
                                 "Run Elliptical Fourier analysis first!")
            return

        # Get first harmonic coefficients
        h1 = self.fourier_coefficients[0]

        # Aspect ratio from first harmonic
        width = np.sqrt(h1['A']**2 + h1['B']**2)
        height = np.sqrt(h1['C']**2 + h1['D']**2)
        aspect_ratio = width / (height + 1e-10)

        # Circularity from area/perimeter
        if self.contour is not None:
            perimeter = cv2.arcLength(self.contour, True) if hasattr(cv2, 'arcLength') else \
                       np.sum(np.sqrt(np.sum(np.diff(self.outline_points, axis=0)**2, axis=1)))
            area = cv2.contourArea(self.contour) if hasattr(cv2, 'contourArea') else \
                   self._polygon_area(self.outline_points)
            circularity = 4 * np.pi * area / (perimeter**2 + 1e-10)
        else:
            circularity = 0.5

        # Classification logic
        if aspect_ratio > 1.5:
            self.shape_classification = "OPEN_BOWL"
            shape_name = "OPEN BOWL"
            shape_desc = "Wide, shallow form"
        elif aspect_ratio < 0.7:
            self.shape_classification = "CLOSED_VESSEL"
            shape_name = "CLOSED VESSEL"
            shape_desc = "Tall, restricted form"
        elif circularity > 0.8:
            self.shape_classification = "PLATTER"
            shape_name = "PLATTER"
            shape_desc = "Circular, plate-like"
        else:
            self.shape_classification = "CUP"
            shape_name = "CUP"
            shape_desc = "Small, handled vessel"

        # Update UI
        color = self.SHAPE_COLORS.get(self.shape_classification, "#95a5a6")
        self.classification_label.config(
            text=f"{shape_name}\n{shape_desc}",
            fg=color,
            font=("Arial", 11, "bold")
        )

        self._log_result(f"🏷️ Shape Classification")
        self._log_result(f"   Form: {shape_name}")
        self._log_result(f"   Aspect Ratio: {aspect_ratio:.2f}")
        self._log_result(f"   Circularity: {circularity:.3f}")

    def _polygon_area(self, points):
        """Calculate area of polygon using shoelace formula"""
        x = points[:, 0]
        y = points[:, 1]
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def _log_result(self, message):
        """Add result to log"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    # ============ EXPORT FUNCTIONS ============

    def _export_fourier(self):
        """Export Fourier coefficients to CSV"""
        if self.fourier_coefficients is None:
            messagebox.showwarning("No Data", "Run Elliptical Fourier analysis first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")],
            initialfile=f"fourier_coefficients_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not filename:
            return

        try:
            import csv

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                writer.writerow(['Harmonic', 'A', 'B', 'C', 'D', 'Power', 'Cumulative_Power'])

                power = np.array([c['A']**2 + c['B']**2 + c['C']**2 + c['D']**2 for c in self.fourier_coefficients])
                total_power = np.sum(power)
                cumulative = np.cumsum(power) / total_power * 100

                for i, c in enumerate(self.fourier_coefficients):
                    writer.writerow([
                        c['harmonic'],
                        f"{c['A']:.6f}",
                        f"{c['B']:.6f}",
                        f"{c['C']:.6f}",
                        f"{c['D']:.6f}",
                        f"{power[i]:.6f}",
                        f"{cumulative[i]:.2f}"
                    ])

            messagebox.showinfo("Export Complete",
                              f"✓ Fourier coefficients saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_morphometrics(self):
        """Export all morphometric measurements"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")],
            initialfile=f"morphometrics_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not filename:
            return

        try:
            import csv

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                writer.writerow(['Measurement', 'Value', 'Unit'])

                # Basic measurements
                if self.contour is not None:
                    if hasattr(cv2, 'arcLength'):
                        perimeter = cv2.arcLength(self.contour, True)
                        area = cv2.contourArea(self.contour)
                    else:
                        perimeter = np.sum(np.sqrt(np.sum(np.diff(self.outline_points, axis=0)**2, axis=1)))
                        area = self._polygon_area(self.outline_points)

                    writer.writerow(['Perimeter', f"{perimeter:.2f}", 'pixels'])
                    writer.writerow(['Area', f"{area:.2f}", 'pixels²'])
                    writer.writerow(['Circularity', f"{4*np.pi*area/perimeter**2:.4f}", 'ratio'])

                # Edge damage
                if self.edge_damage_index is not None:
                    writer.writerow(['Edge Damage Index', f"{self.edge_damage_index:.2f}", '%'])

                # Fourier power
                if self.fourier_coefficients is not None:
                    power = np.array([c['A']**2 + c['B']**2 + c['C']**2 + c['D']**2
                                    for c in self.fourier_coefficients[:5]])
                    for i, p in enumerate(power, 1):
                        writer.writerow([f'Harmonic_{i}_Power', f"{p:.6f}", 'normalized'])

                # Shape classification
                if self.shape_classification is not None:
                    writer.writerow(['Shape_Class', self.shape_classification, ''])

            messagebox.showinfo("Export Complete",
                              f"✓ Morphometric data saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = LithicMorphometricsPlugin(main_app)
    return plugin
