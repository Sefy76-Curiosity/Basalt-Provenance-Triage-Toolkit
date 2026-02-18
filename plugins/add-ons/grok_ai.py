"""
xAI Grok AI Assistant - UI Add-on
Powered by xAI's Grok models (OpenAI-compatible API)
Category: add-ons
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import requests
from pathlib import Path

# ────────────────────────────────────────────────
PLUGIN_INFO = {
    'id': 'grok_ai',
    'name': 'Grok (xAI)',
    'category': 'add-ons',
    'icon': '🚀',
    'version': '2.0',
    'requires': ['requests'],
    'description': 'xAI Grok AI assistant (requires API key from console.x.ai)'
}


class GrokAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Grok (xAI)"
        self.version = "1.0"

        # Config
        self.config_file = Path("config/grok_ai_config.json")
        self.config = self.load_config()

        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "grok-2-1212")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 8192)

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    # ────────────────────────────────────────────────
    # Context builder - this is the magic
    # ────────────────────────────────────────────────
    def get_context(self) -> str:
        """Build rich, structured context from currently selected samples"""
        if not hasattr(self.app, 'selected_rows') or not self.app.selected_rows:
            return "No samples selected in the table."

        context = "You are an expert in Levantine and Egyptian Bronze Age basalt provenance.\n"
        context += "Reference: Hartung 2017, Philip & Williams-Thorpe 2001, Rosenberg et al. 2016, Williams-Thorpe & Thorpe 1993.\n\n"
        context += "Current selected samples:\n\n"

        for idx in list(self.app.selected_rows)[:6]:  # max 6 to keep prompt reasonable
            if idx >= len(self.app.samples):
                continue
            row = self.app.samples[idx]

            sid = row.get("Sample_ID", f"Row_{idx}")
            cls = get_consistent_classification(row)          # your existing function
            zr = get_element_value(row, "Zr")
            nb = get_element_value(row, "Nb")
            cr = get_element_value(row, "Cr")
            ni = get_element_value(row, "Ni")
            ba = get_element_value(row, "Ba")
            wall = get_element_value(row, "Wall_Thickness_mm")

            context += f"• {sid}: {cls}\n"
            if zr is not None and nb is not None:
                context += f"  Zr/Nb = {zr/nb:.2f}\n"
            if cr is not None and ni is not None:
                context += f"  Cr/Ni = {cr/ni:.2f}\n"
            if ba is not None:
                context += f"  Ba = {ba:.0f} ppm\n"
            if wall is not None:
                context += f"  Wall thickness = {wall:.1f} mm\n"
            context += "\n"

        context += "Answer in clear, scientific but accessible language. "
        context += "When relevant, mention which geochemical thresholds were decisive."
        return context

    # ────────────────────────────────────────────────
    # Main query method (used by AI tab)
    # ────────────────────────────────────────────────
    def query(self, user_prompt: str) -> str:
        if not self.api_key:
            return "Error: No Grok API key configured.\nGo to Grok Settings → Enter API key."

        full_prompt = self.get_context() + "\n\nUser question: " + user_prompt

        try:
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False
                },
                timeout=90
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return "Error: Invalid or expired Grok API key."
            elif e.response.status_code == 429:
                return "Error: Rate limit reached. Please wait a moment."
            else:
                return f"HTTP {e.response.status_code}: {e.response.text[:300]}"
        except Exception as e:
            return f"Grok API error: {str(e)}"

    # ────────────────────────────────────────────────
    # Settings dialog (mirrors Gemini style)
    # ────────────────────────────────────────────────
    def show_settings(self):
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Grok (xAI) Settings")
        dialog.geometry("570x520")
        dialog.transient(self.app.root)
        dialog.grab_set()

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🚀 Grok (xAI) Configuration",
                 font=("Arial", 13, "bold")).pack(pady=(0, 15))

        # API Key
        ttk.Label(main, text="API Key", font=("Arial", 10, "bold")).pack(anchor="w")
        api_entry = ttk.Entry(main, width=60, show="*")
        api_entry.insert(0, self.api_key)
        api_entry.pack(fill=tk.X, pady=(2, 8))

        link = ttk.Label(main, text="🔗 Get API key → https://console.x.ai",
                        foreground="blue", cursor="hand2")
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda e: webbrowser.open("https://console.x.ai"))

        # Model
        ttk.Label(main, text="Model", font=("Arial", 10, "bold")).pack(anchor="w", pady=(12, 2))
        model_var = tk.StringVar(value=self.model)
        models = ["grok-2-1212", "grok-2", "grok-beta"]
        combo = ttk.Combobox(main, textvariable=model_var, values=models, state="readonly")
        combo.pack(fill=tk.X, pady=(0, 12))

        # Temperature
        ttk.Label(main, text="Temperature", font=("Arial", 10, "bold")).pack(anchor="w")
        temp_var = tk.DoubleVar(value=self.temperature)
        ttk.Scale(main, from_=0.0, to=1.0, variable=temp_var, orient="horizontal").pack(fill=tk.X, pady=4)
        temp_lbl = ttk.Label(main, text=f"{temp_var.get():.1f}")
        temp_lbl.pack(anchor="w")
        def update_lbl(*_): temp_lbl.config(text=f"{temp_var.get():.1f}")
        temp_var.trace("w", update_lbl)

        # Max tokens
        ttk.Label(main, text="Max Tokens", font=("Arial", 10, "bold")).pack(anchor="w", pady=(12, 2))
        tokens_var = tk.IntVar(value=self.max_tokens)
        ttk.Spinbox(main, from_=512, to=32768, textvariable=tokens_var, width=15).pack(anchor="w")

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=25)

        def save():
            self.api_key = api_entry.get().strip()
            self.model = model_var.get()
            self.temperature = temp_var.get()
            self.max_tokens = tokens_var.get()

            self.config.update({
                "api_key": self.api_key,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            })
            self.save_config()
            dialog.destroy()

            if hasattr(self.app, 'ai_status_var'):
                self.app.ai_status_var.set(f"Using Grok ({self.model})")

        ttk.Button(btn_frame, text="Save", command=save, width=12).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side="right", padx=5)


def register_plugin(main_app):
    """Called by your plugin loader"""
    return GrokAIPlugin(main_app)
