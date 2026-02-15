"""
Claude AI Assistant - UI Add-on
Powered by Anthropic's Claude models
Category: add-ons (provides AI chat functionality)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import webbrowser
from pathlib import Path

HAS_ANTHROPIC = False
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'claude_ai',
    'name': 'Claude (Anthropic)',
    'category': 'add-ons',
    'icon': '🤖',
    'requires': ['anthropic'],
    'description': 'Claude AI assistant by Anthropic (requires API key)'
}

class ClaudeAIPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Claude AI"
        self.version = "1.0"

        # Configuration
        self.config_file = Path("config/claude_ai_config.json")
        self.config = self.load_config()

        # Settings
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "claude-sonnet-4-5-20250929")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)

    def load_config(self):
        """Load plugin configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self):
        """Save plugin configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def query(self, prompt):
        """Main method called when user asks a question"""
        if not HAS_ANTHROPIC:
            return "Error: 'anthropic' package not installed.\nRun: pip install anthropic"

        if not self.api_key:
            return "Error: API Key missing. Go to Claude Settings."

        try:
            client = Anthropic(api_key=self.api_key)

            # Add basalt context to system prompt
            system_prompt = """You are Claude, a helpful AI assistant specialized in basalt provenance,
geochemistry, and archaeological geology. Provide accurate, scientific responses based on
geochemical data and established research in Levantine and Egyptian Bronze Age basalt sources."""

            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return "❌ Invalid API key. Please check your Claude API key in Settings."
            elif "rate_limit" in error_msg.lower():
                return "❌ Rate limit reached. Please wait a moment and try again."
            else:
                return f"Claude Error: {error_msg}"

    def show_settings(self):
        """Show configuration dialog"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Claude AI Settings")
        dialog.geometry("550x580")
        dialog.transient(self.app.root)
        dialog.grab_set()

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🤖 Claude AI Configuration",
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Check if package is installed
        if not HAS_ANTHROPIC:
            warn_frame = tk.Frame(main, bg="#fff3cd", height=50)
            warn_frame.pack(fill=tk.X, pady=5)
            tk.Label(warn_frame,
                    text="⚠️ anthropic package not installed\nRun: pip install anthropic",
                    bg="#fff3cd", fg="#856404", font=("Arial", 9)).pack(pady=8)

        # API Key
        ttk.Label(main, text="API Key:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
        api_key_entry = ttk.Entry(main, width=50, show="*")
        api_key_entry.insert(0, self.api_key)
        api_key_entry.pack(fill=tk.X, pady=(0, 5))

        key_link = ttk.Label(main, text="🔗 Get API Key from Anthropic Console",
                            foreground="blue", cursor="hand2")
        key_link.pack(anchor=tk.W, pady=(0, 15))
        key_link.bind("<Button-1>", lambda e: webbrowser.open("https://console.anthropic.com/settings/keys"))

        # Model
        ttk.Label(main, text="Model:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        model_var = tk.StringVar(value=self.model)
        models = [
            "claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 (current)
            "claude-opus-4-5-20251101",    # Claude Opus 4.5 (most capable)
            "claude-haiku-4-5-20251001",   # Claude Haiku 4.5 (fastest)
            "claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet
            "claude-3-5-haiku-20241022"    # Claude 3.5 Haiku
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

        # Info section
        info_frame = ttk.LabelFrame(main, text="About Claude", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        info_text = """Claude is an AI assistant by Anthropic, designed to be:
• Helpful, harmless, and honest
• Excellent at analysis and reasoning
• Specialized in scientific and technical topics
• Expert in basalt provenance and geochemistry

Model recommendations:
• Sonnet 4.5: Best balance of speed and capability
• Opus 4.5: Most capable, best for complex analysis
• Haiku 4.5: Fastest, good for quick questions"""

        info_label = ttk.Label(info_frame, text=info_text,
                               justify=tk.LEFT, wraplength=500)
        info_label.pack(padx=5, pady=5)

        # Test button
        def test_key():
            test_key = api_key_entry.get().strip()
            if not test_key:
                messagebox.showerror("Error", "Please enter an API key first")
                return

            try:
                client = Anthropic(api_key=test_key)
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=100,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                messagebox.showinfo("Success", "✅ API key is valid!\nClaude responded successfully.")
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
                model_name = self.model.split('-')[1].title() + " " + self.model.split('-')[2]
                self.app.ai_chat_output.insert(tk.END,
                    f"System: Claude AI configured with {model_name}\n\n", "system")
                self.app.ai_chat_output.see(tk.END)

        ttk.Button(btn_frame, text="Save", command=save_settings, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.RIGHT, padx=5)

    def get_status(self):
        """Return plugin status for UI"""
        if not HAS_ANTHROPIC:
            return "🤖 Claude (needs: pip install anthropic)"
        if not self.api_key:
            return "🤖 Claude (needs API key)"

        # Show friendly model name
        model_display = self.model.split('-')[1].title() + " " + self.model.split('-')[2]
        return f"🤖 Claude {model_display}"

def register_plugin(main_app):
    """Register this plugin with the main application"""
    return ClaudeAIPlugin(main_app)
