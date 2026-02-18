"""
Ollama AI Assistant - UI Add-on
Free, local AI chat assistant using Ollama
Category: add-ons (provides AI chat functionality)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import subprocess
import webbrowser
from pathlib import Path

HAS_REQUESTS = False
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'ollama_ai',
    'name': 'Ollama AI (Free Local)',
    'category': 'add-ons',
    'icon': '🦙',
    'version': '2.0',
    'requires': ['requests'],
    'description': 'Free AI assistant running locally on your computer'
}

class OllamaAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Ollama AI"
        self.version = "1.0"

        # Configuration
        self.config_file = Path("config/ollama_ai_config.json")
        self.config = self.load_config()

        # Settings
        self.url = self.config.get("url", "http://localhost:11434")
        self.model = self.config.get("model", "llama2")
        self.temperature = self.config.get("temperature", 0.7)

        # Check if Ollama is running
        self.ollama_running = self._check_ollama()

    def load_config(self):
        """Load plugin configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
        except:
            pass
        return {
            "url": "http://localhost:11434",
            "model": "llama2",
            "temperature": 0.7
        }

    def save_config(self):
        """Save plugin configuration"""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save Ollama config: {e}")

    def _check_ollama(self):
        """Check if Ollama is running"""
        if not HAS_REQUESTS:
            return False
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _get_available_models(self):
        """Get list of models installed in Ollama"""
        if not HAS_REQUESTS:
            return ["llama2", "mistral", "codellama", "gemma", "phi"]
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                if models:
                    return models
        except:
            pass
        return ["llama2", "mistral", "codellama", "gemma", "phi"]

    def query(self, question):
        """Main method called when user asks a question"""
        if not HAS_REQUESTS:
            return "❌ Requests library not installed. Run: pip install requests"

        # Check if Ollama is running
        if not self._check_ollama():
            return (
                "⚠️ **Ollama is not running!**\n\n"
                "To use free local AI:\n"
                "1. Download Ollama from: https://ollama.ai\n"
                "2. Install and run Ollama\n"
                "3. Open terminal/command prompt\n"
                "4. Run: ollama pull llama2\n"
                "5. Start Ollama application\n\n"
                "Click the ⚙️ Settings button for help."
            )

        try:
            # Add basalt context to the prompt
            enhanced_prompt = f"""You are a helpful assistant specialized in basalt provenance, geochemistry, and archaeological geology.
Answer the following question scientifically and accurately:

{question}"""

            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": enhanced_prompt,
                    "stream": False,
                    "temperature": self.temperature
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result["response"]
            else:
                return f"❌ Ollama Error: {response.status_code}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def show_settings(self):
        """Show configuration dialog"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("🦙 Ollama AI Settings")
        dialog.geometry("600x550")
        dialog.transient(self.app.root)
        dialog.grab_set()

        # Main frame
        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main, text="Ollama Local AI Configuration",
                          font=("Arial", 14, "bold"))
        title.pack(pady=(0, 20))

        # Check if Ollama is running
        status_frame = ttk.LabelFrame(main, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)

        self.ollama_running = self._check_ollama()
        if self.ollama_running:
            status_text = "✅ Ollama is RUNNING"
            status_color = "green"
        else:
            status_text = "❌ Ollama is NOT running"
            status_color = "red"

        status_label = ttk.Label(status_frame, text=status_text,
                                 font=("Arial", 11, "bold"),
                                 foreground=status_color)
        status_label.pack()

        # Connection settings
        conn_frame = ttk.LabelFrame(main, text="Connection", padding=10)
        conn_frame.pack(fill=tk.X, pady=10)

        ttk.Label(conn_frame, text="Ollama URL:",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)

        url_entry = ttk.Entry(conn_frame, width=50)
        url_entry.insert(0, self.url)
        url_entry.pack(fill=tk.X, pady=5)

        ttk.Label(conn_frame, text="Default: http://localhost:11434",
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W)

        # Model settings
        model_frame = ttk.LabelFrame(main, text="Model Settings", padding=10)
        model_frame.pack(fill=tk.X, pady=10)

        # Get available models
        available_models = self._get_available_models()

        ttk.Label(model_frame, text="Model:",
                 font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)

        model_var = tk.StringVar(value=self.model)
        model_combo = ttk.Combobox(model_frame, textvariable=model_var,
                                   values=available_models,
                                   state='readonly', width=30)
        model_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        # Temperature
        ttk.Label(model_frame, text="Temperature:",
                 font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)

        temp_var = tk.DoubleVar(value=self.temperature)
        temp_scale = ttk.Scale(model_frame, from_=0.0, to=1.0,
                               variable=temp_var, orient=tk.HORIZONTAL, length=200)
        temp_scale.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        temp_label = ttk.Label(model_frame, text=f"{self.temperature:.1f}")
        temp_label.grid(row=1, column=2, padx=5)

        def update_temp(*args):
            temp_label.config(text=f"{temp_var.get():.1f}")
        temp_var.trace('w', update_temp)

        # Help section
        help_frame = ttk.LabelFrame(main, text="How to set up Ollama", padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        help_text = """1. Download Ollama from: https://ollama.ai
2. Install and run Ollama
3. Open terminal/command prompt
4. Pull a model (examples):
   • ollama pull llama2     (7B model, good for most users)
   • ollama pull mistral    (faster, good for coding)
   • ollama pull gemma:2b   (small, runs on any computer)
5. Keep Ollama running in background

Recommended for basalt questions: llama2 or mistral"""

        help_label = ttk.Label(help_frame, text=help_text,
                               justify=tk.LEFT, wraplength=500)
        help_label.pack(padx=5, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=20)

        def download_ollama():
            webbrowser.open("https://ollama.ai")

        def save_settings():
            self.url = url_entry.get().strip()
            self.model = model_var.get()
            self.temperature = temp_var.get()

            # Update config
            self.config["url"] = self.url
            self.config["model"] = self.model
            self.config["temperature"] = self.temperature

            self.save_config()
            dialog.destroy()

            # Show confirmation
            if hasattr(self.app, 'ai_chat_output'):
                self.app.ai_chat_output.insert(tk.END,
                    f"System: Ollama configured with model {self.model}\n\n",
                    "system")
                self.app.ai_chat_output.see(tk.END)

        ttk.Button(btn_frame, text="Download Ollama",
                  command=download_ollama).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=save_settings,
                  width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                  width=15).pack(side=tk.RIGHT, padx=5)

    def get_status(self):
        """Return plugin status for UI"""
        if not self._check_ollama():
            return "🦙 Ollama (not running)"
        return f"🦙 Ollama ({self.model})"

# Register the plugin
def register_plugin(main_app):
    return OllamaAIPlugin(main_app)
