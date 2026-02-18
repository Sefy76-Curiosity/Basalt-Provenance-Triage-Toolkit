"""
DeepSeek AI Assistant - UI Add-on
AI-powered chat assistant using DeepSeek API
Category: add-ons (provides AI chat functionality)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from pathlib import Path

HAS_REQUESTS = False
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'deepseek_ai',
    'name': 'DeepSeek AI Assistant',
    'category': 'add-ons',
    'icon': '🧠',
    'version': '2.0',
    'requires': ['requests'],
    'description': 'AI chat assistant powered by DeepSeek'
}

class DeepSeekAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "DeepSeek AI"
        self.version = "1.0"

        # Configuration
        self.config_file = Path("config/deepseek_ai_config.json")
        self.config = self.load_config()

        # API settings
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "deepseek-chat")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2000)

    def load_config(self):
        """Load plugin configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
        except:
            pass
        return {
            "api_key": "",
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 2000
        }

    def save_config(self):
        """Save plugin configuration"""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save DeepSeek config: {e}")

    def query(self, question):
        """Main method called when user asks a question"""
        if not HAS_REQUESTS:
            return "❌ Requests library not installed. Run: pip install requests"

        if not self.api_key:
            return "⚠️ DeepSeek API key not configured. Click the gear icon ⚙️ to set it up."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant specialized in basalt provenance, geochemistry, and archaeological geology. Provide accurate, scientific responses."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"❌ DeepSeek API Error: {response.status_code}\n{response.text}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def show_settings(self):
        """Show configuration dialog"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("🧠 DeepSeek AI Settings")
        dialog.geometry("600x500")
        dialog.transient(self.app.root)
        dialog.grab_set()

        # Main frame
        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main, text="DeepSeek AI Configuration",
                          font=("Arial", 14, "bold"))
        title.pack(pady=(0, 20))

        # API Key
        key_frame = ttk.LabelFrame(main, text="API Key", padding=10)
        key_frame.pack(fill=tk.X, pady=10)

        ttk.Label(key_frame, text="DeepSeek API Key:",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)

        api_key_entry = ttk.Entry(key_frame, width=60, show="*")
        api_key_entry.insert(0, self.api_key)
        api_key_entry.pack(fill=tk.X, pady=5)

        ttk.Label(key_frame, text="Get your API key from: https://platform.deepseek.com/",
                 font=("Arial", 8), foreground="blue").pack(anchor=tk.W)

        # Model Settings
        model_frame = ttk.LabelFrame(main, text="Model Settings", padding=10)
        model_frame.pack(fill=tk.X, pady=10)

        # Model selection
        model_row = ttk.Frame(model_frame)
        model_row.pack(fill=tk.X, pady=5)

        ttk.Label(model_row, text="Model:", width=15).pack(side=tk.LEFT)

        model_var = tk.StringVar(value=self.model)
        model_combo = ttk.Combobox(model_row, textvariable=model_var,
                                   values=["deepseek-chat", "deepseek-coder"],
                                   state="readonly", width=30)
        model_combo.pack(side=tk.LEFT)

        # Temperature
        temp_row = ttk.Frame(model_frame)
        temp_row.pack(fill=tk.X, pady=5)

        ttk.Label(temp_row, text="Temperature:", width=15).pack(side=tk.LEFT)

        temp_var = tk.DoubleVar(value=self.temperature)
        temp_scale = ttk.Scale(temp_row, from_=0.0, to=1.0,
                               variable=temp_var, orient=tk.HORIZONTAL, length=200)
        temp_scale.pack(side=tk.LEFT, padx=5)

        temp_label = ttk.Label(temp_row, text=f"{self.temperature:.1f}")
        temp_label.pack(side=tk.LEFT, padx=5)

        def update_temp(*args):
            temp_label.config(text=f"{temp_var.get():.1f}")
        temp_var.trace('w', update_temp)

        # Max Tokens
        tokens_row = ttk.Frame(model_frame)
        tokens_row.pack(fill=tk.X, pady=5)

        ttk.Label(tokens_row, text="Max Tokens:", width=15).pack(side=tk.LEFT)

        tokens_var = tk.IntVar(value=self.max_tokens)
        tokens_spin = ttk.Spinbox(tokens_row, from_=100, to=4000,
                                   textvariable=tokens_var, width=20)
        tokens_spin.pack(side=tk.LEFT)

        # System Prompt Info
        info_frame = ttk.LabelFrame(main, text="About", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        info_text = """DeepSeek AI Assistant is specialized in:
• Basalt provenance classification
• Geochemical data interpretation
• Archaeological geology
• Egyptian, Sinai, and Levantine sources
• Major/trace element geochemistry
• Ratio analysis (Zr/Nb, Cr/Ni, Ba/Rb)

The AI will provide scientific, research-focused responses
tailored to your basalt provenance questions."""

        info_label = ttk.Label(info_frame, text=info_text,
                               justify=tk.LEFT, wraplength=500)
        info_label.pack(padx=5, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=20)

        def save_settings():
            self.api_key = api_key_entry.get().strip()
            self.model = model_var.get()
            self.temperature = temp_var.get()
            self.max_tokens = tokens_var.get()

            # Update config
            self.config["api_key"] = self.api_key
            self.config["model"] = self.model
            self.config["temperature"] = self.temperature
            self.config["max_tokens"] = self.max_tokens

            self.save_config()
            dialog.destroy()

            # Show confirmation in chat if available
            if hasattr(self.app, 'ai_chat_output'):
                self.app.ai_chat_output.insert(tk.END,
                    f"System: DeepSeek AI configured with model {self.model}\n\n",
                    "system")
                self.app.ai_chat_output.see(tk.END)

        ttk.Button(btn_frame, text="Save", command=save_settings,
                  width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                  width=15).pack(side=tk.RIGHT, padx=5)

    def get_status(self):
        """Return plugin status for UI"""
        if not self.api_key:
            return "🧠 DeepSeek (needs API key)"
        return f"🧠 DeepSeek ({self.model})"

# This is what the plugin manager looks for
def register_plugin(main_app):
    """Register this plugin with the main application"""
    return DeepSeekAIPlugin(main_app)
