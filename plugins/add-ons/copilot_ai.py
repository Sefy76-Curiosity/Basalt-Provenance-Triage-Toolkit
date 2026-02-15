"""
Copilot AI Assistant - UI Add-on
Powered by OpenAI-compatible Copilot models
Category: add-ons (provides AI chat functionality)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from pathlib import Path

HAS_REQUESTS = False
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'copilot_ai',
    'name': 'Microsoft Copilot',
    'category': 'add-ons',
    'icon': '🅲',
    'requires': ['requests'],
    'description': 'Copilot AI assistant (requires API key)'
}

class CopilotAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Microsoft Copilot"
        self.version = "1.0"

        # Configuration
        self.config_file = Path("config/copilot_ai_config.json")
        self.config = self.load_config()

        # Settings
        self.api_key = self.config.get("api_key", "")
        self.api_base = self.config.get("api_base", "https://api.openai.com/v1/chat/completions")
        self.model = self.config.get("model", "gpt-4.1")
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
        if not HAS_REQUESTS:
            return "Error: 'requests' not installed.\nRun: pip install requests"

        if not self.api_key:
            return "Error: API Key missing. Go to Copilot Settings."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are Copilot, a helpful and knowledgeable AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            response = requests.post(
                self.api_base,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                return f"Copilot API Error: {response.status_code}\n{response.text}"

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            return f"Copilot Error: {str(e)}"

    def show_settings(self):
        """Settings UI similar to Gemini plugin"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Copilot Setup")
        dialog.geometry("550x550")
        dialog.transient(self.app.root)
        dialog.grab_set()

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Microsoft Copilot Configuration",
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # API Key
        ttk.Label(main, text="API Key:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
        api_key_entry = ttk.Entry(main, width=50, show="*")
        api_key_entry.insert(0, self.api_key)
        api_key_entry.pack(fill=tk.X, pady=(0, 5))

        # Link to get API key
        key_link = ttk.Label(
            main, text="🔗 Get an OpenAI‑compatible API key",
            foreground="blue",
            cursor="hand2"
        )
        key_link.pack(anchor=tk.W, pady=(0, 5))
        key_link.bind("<Button-1>", lambda e: webbrowser.open("https://platform.openai.com/api-keys"))

        # API Base URL
        ttk.Label(main, text="API Base URL:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
        api_base_entry = ttk.Entry(main, width=50)
        api_base_entry.insert(0, self.api_base)
        api_base_entry.pack(fill=tk.X, pady=(0, 5))

        # Model
        ttk.Label(main, text="Model:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        model_var = tk.StringVar(value=self.model)
        models = [
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4o",
            "gpt-4.0"
        ]
        model_combo = ttk.Combobox(main, textvariable=model_var,
                                   values=models, state="readonly", width=45)
        model_combo.pack(fill=tk.X, pady=(0, 15))

        # Temperature
        ttk.Label(main, text="Temperature:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        temp_frame = ttk.Frame(main)
        temp_frame.pack(fill=tk.X, pady=(0, 5))

        temp_var = tk.DoubleVar(value=self.temperature)
        temp_scale = ttk.Scale(temp_frame, from_=0.0, to=1.0,
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

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=20)

        def save_settings():
            self.api_key = api_key_entry.get().strip()
            self.api_base = api_base_entry.get().strip()
            self.model = model_var.get()
            self.temperature = temp_var.get()
            self.max_tokens = tokens_var.get()

            self.config.update({
                "api_key": self.api_key,
                "api_base": self.api_base,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            })
            self.save_config()
            dialog.destroy()

            if hasattr(self.app, 'ai_chat_output'):
                self.app.ai_chat_output.insert(
                    tk.END,
                    f"System: Copilot updated to {self.model}\n\n",
                    "system"
                )

        ttk.Button(btn_frame, text="Save", command=save_settings, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.RIGHT, padx=5)

    def get_status(self):
        if not HAS_REQUESTS:
            return "🅲 Copilot (needs: pip install requests)"
        if not self.api_key:
            return "🅲 Copilot (needs API key)"
        return f"🅲 Copilot ({self.model})"

def register_plugin(main_app):
    return CopilotAIPlugin(main_app)
