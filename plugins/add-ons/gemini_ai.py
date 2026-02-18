"""
Google Gemini AI Assistant - UI Add-on
Powered by Google's Gemini models (using google.genai)
Category: add-ons (provides AI chat functionality)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import webbrowser
from pathlib import Path

HAS_GEMINI = False
try:
    import google.genai as genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'gemini_ai',
    'name': 'Google Gemini',
    'category': 'add-ons',
    'icon': '🔮',
    'version': '3.0',
    'requires': ['google-genai'],
    'description': 'Google Gemini AI assistant (requires API key)'
}

class GeminiAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Google Gemini"
        self.version = "2.0"

        # Configuration
        self.config_file = Path("config/gemini_ai_config.json")
        self.config = self.load_config()

        # Settings
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "gemini-2.0-flash-exp")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def query(self, prompt):
        """Simple query that returns the answer directly"""
        if not HAS_GEMINI:
            return "Error: 'google-genai' not found.\nRun: pip install google-genai"

        if not self.api_key:
            return "Error: API Key missing. Go to Gemini Settings."

        try:
            # Initialize client with API key
            client = genai.Client(api_key=self.api_key)

            # Generate content using the new API
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )

            return response.text

        except Exception as e:
            error_msg = str(e)

            # If model not found, try to list available models
            if "404" in error_msg or "not found" in error_msg.lower():
                try:
                    client = genai.Client(api_key=self.api_key)
                    models = client.models.list()
                    available = []

                    for model in models:
                        if 'generateContent' in str(model.supported_actions):
                            name = model.name.replace('models/', '')
                            available.append(name)

                    if available:
                        return (f"❌ Model '{self.model}' not available.\n\n"
                               f"✅ Working models for your API key:\n" +
                               "\n".join(f"  • {m}" for m in available[:15]))
                    else:
                        return "❌ No working models found for this API key."
                except Exception as list_error:
                    return f"Error listing models: {str(list_error)}"

            return f"Gemini Error: {error_msg}"

    def show_settings(self):
        """Settings UI with API Key link and masked entry"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Gemini Setup")
        dialog.geometry("600x600")
        dialog.transient(self.app.root)
        dialog.grab_set()

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Google Gemini Configuration",
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Check if package is installed
        if not HAS_GEMINI:
            warn_frame = tk.Frame(main, bg="#fff3cd", height=50)
            warn_frame.pack(fill=tk.X, pady=5)
            tk.Label(warn_frame,
                    text="⚠️ google-genai not installed\nRun: pip install google-genai",
                    bg="#fff3cd", fg="#856404", font=("Arial", 9)).pack(pady=8)

        # API Key
        ttk.Label(main, text="API Key:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
        api_key_entry = ttk.Entry(main, width=50, show="*")
        api_key_entry.insert(0, self.api_key)
        api_key_entry.pack(fill=tk.X, pady=(0, 5))

        key_link = ttk.Label(main, text="🔗 Get API Key from Google AI Studio",
                            foreground="blue", cursor="hand2")
        key_link.pack(anchor=tk.W, pady=(0, 15))
        key_link.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        # Model selection
        ttk.Label(main, text="Model:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # Updated model list for google.genai
        models = [
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            "gemini-exp-1206",
            "gemini-2.0-flash-thinking-exp-1219",
            "gemini-2.0-flash-thinking-exp",
            "learnlm-1.5-pro-experimental"
        ]

        model_var = tk.StringVar(value=self.model)
        model_combo = ttk.Combobox(main, textvariable=model_var,
                                   values=models, state="readonly", width=45)
        model_combo.pack(fill=tk.X, pady=(0, 5))

        # Refresh models button
        def refresh_models():
            if not api_key_entry.get().strip():
                messagebox.showwarning("Warning", "Please enter API key first")
                return

            try:
                test_key = api_key_entry.get().strip()
                client = genai.Client(api_key=test_key)
                model_list = client.models.list()
                available_models = []

                for m in model_list:
                    if 'generateContent' in str(m.supported_actions):
                        name = m.name.replace('models/', '')
                        available_models.append(name)

                if available_models:
                    model_combo['values'] = available_models
                    messagebox.showinfo("Success", f"Found {len(available_models)} models")
                else:
                    messagebox.showwarning("Warning", "No models with generateContent found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch models: {str(e)}")

        refresh_btn = ttk.Button(main, text="🔄 Refresh Models", command=refresh_models)
        refresh_btn.pack(anchor=tk.W, pady=(0, 15))

        # Temperature
        ttk.Label(main, text="Temperature:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        temp_frame = ttk.Frame(main)
        temp_frame.pack(fill=tk.X, pady=(0, 5))

        temp_var = tk.DoubleVar(value=self.temperature)
        temp_scale = ttk.Scale(temp_frame, from_=0.0, to=2.0,  # Updated range to match new API
                               variable=temp_var, orient=tk.HORIZONTAL, length=300)
        temp_scale.pack(side=tk.LEFT)

        temp_label = ttk.Label(temp_frame, text=f"{self.temperature:.1f}", width=5)
        temp_label.pack(side=tk.LEFT, padx=10)

        def update_temp(*args):
            temp_label.config(text=f"{temp_var.get():.1f}")
        temp_var.trace('w', update_temp)

        # Max Tokens
        ttk.Label(main, text="Max Tokens:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
        tokens_var = tk.IntVar(value=self.max_tokens)
        tokens_spin = ttk.Spinbox(main, from_=100, to=8192,
                                   textvariable=tokens_var, width=20)
        tokens_spin.pack(anchor=tk.W, pady=(0, 15))

        # Test button
        def test_key():
            test_key = api_key_entry.get().strip()
            if not test_key:
                messagebox.showerror("Error", "Please enter an API key first")
                return

            try:
                client = genai.Client(api_key=test_key)
                models = client.models.list()
                working = 0
                for m in models:
                    if 'generateContent' in str(m.supported_actions):
                        working += 1

                if working > 0:
                    messagebox.showinfo("Success",
                        f"✅ API key works!\nFound {working} available models.")
                else:
                    messagebox.showwarning("Warning",
                        "API key valid but no working models found.")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid API key:\n{str(e)}")

        ttk.Button(main, text="Test API Key", command=test_key).pack(pady=10)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=20)

        def save_settings():
            self.api_key = api_key_entry.get().strip()
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

            if hasattr(self.app, 'ai_chat_output'):
                self.app.ai_chat_output.insert(tk.END,
                    f"System: Gemini updated to {self.model}\n\n", "system")

        ttk.Button(btn_frame, text="Save", command=save_settings, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.RIGHT, padx=5)

    def get_status(self):
        if not HAS_GEMINI:
            return "🔮 Gemini (needs: pip install google-genai)"
        if not self.api_key:
            return "🔮 Gemini (needs API key)"
        return f"🔮 Gemini ({self.model})"

def register_plugin(main_app):
    return GeminiAIPlugin(main_app)
