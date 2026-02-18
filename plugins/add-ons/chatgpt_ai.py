"""
ChatGPT AI Assistant - UI Add-on
Powered by OpenAI models
Category: add-ons (provides AI chat functionality)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import webbrowser
from pathlib import Path

HAS_OPENAI = False
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    pass


PLUGIN_INFO = {
    "id": "chatgpt_ai",
    "name": "ChatGPT",
    "category": "add-ons",
    "icon": "🤖",
    'version': '2.0',
    "requires": ["openai"],
    "description": "ChatGPT AI assistant (requires OpenAI API key)"
}


class ChatGPTAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "ChatGPT"
        self.version = "1.0"

        self.config_file = Path("config/chatgpt_ai_config.json")
        self.config = self.load_config()

        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "gpt-4o-mini")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)

    # --------------------------------------------------
    # Config
    # --------------------------------------------------

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
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    # --------------------------------------------------
    # Core Query
    # --------------------------------------------------

    def query(self, prompt):
        if not HAS_OPENAI:
            return "Error: openai package not installed.\nRun: pip install openai"

        if not self.api_key:
            return "Error: API Key missing. Go to ChatGPT Settings."

        try:
            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"ChatGPT Error: {str(e)}"

    # --------------------------------------------------
    # Settings UI
    # --------------------------------------------------

    def show_settings(self):
        dialog = tk.Toplevel(self.app.root)
        dialog.title("ChatGPT Setup")
        dialog.geometry("550x520")
        dialog.transient(self.app.root)
        dialog.grab_set()

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main,
            text="ChatGPT Configuration",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))

        if not HAS_OPENAI:
            warn = tk.Frame(main, bg="#fff3cd")
            warn.pack(fill=tk.X, pady=5)
            tk.Label(
                warn,
                text="⚠️ openai not installed\nRun: pip install openai",
                bg="#fff3cd",
                fg="#856404",
                font=("Arial", 9)
            ).pack(pady=8)

        # API Key
        ttk.Label(main, text="API Key:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        api_entry = ttk.Entry(main, show="*")
        api_entry.insert(0, self.api_key)
        api_entry.pack(fill=tk.X, pady=(0, 5))

        link = ttk.Label(
            main,
            text="🔗 Get API Key from OpenAI",
            foreground="blue",
            cursor="hand2"
        )
        link.pack(anchor=tk.W, pady=(0, 15))
        link.bind("<Button-1>", lambda e: webbrowser.open("https://platform.openai.com/api-keys"))

        # Model
        ttk.Label(main, text="Model:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        model_var = tk.StringVar(value=self.model)
        models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-3.5-turbo"
        ]
        ttk.Combobox(
            main,
            textvariable=model_var,
            values=models,
            state="readonly"
        ).pack(fill=tk.X, pady=(0, 15))

        # Temperature
        ttk.Label(main, text="Temperature:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        temp_var = tk.DoubleVar(value=self.temperature)
        ttk.Scale(main, from_=0.0, to=1.0, variable=temp_var).pack(fill=tk.X)

        # Max Tokens
        ttk.Label(main, text="Max Tokens:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
        tokens_var = tk.IntVar(value=self.max_tokens)
        ttk.Spinbox(main, from_=100, to=8192, textvariable=tokens_var).pack(anchor=tk.W)

        # Test
        def test_key():
            try:
                client = OpenAI(api_key=api_entry.get().strip())
                client.models.list()
                messagebox.showinfo("Success", "✅ API key is valid")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(main, text="Test API Key", command=test_key).pack(pady=10)

        # Save / Cancel
        btns = ttk.Frame(main)
        btns.pack(fill=tk.X, pady=20)

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

        ttk.Button(btns, text="Save", command=save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def get_status(self):
        if not HAS_OPENAI:
            return "🤖 ChatGPT (needs: pip install openai)"
        if not self.api_key:
            return "🤖 ChatGPT (needs API key)"
        return f"🤖 ChatGPT ({self.model})"


def register_plugin(main_app):
    return ChatGPTAIPlugin(main_app)
