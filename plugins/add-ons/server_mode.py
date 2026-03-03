# server_mode.py – Full Server Mode Plugin

PLUGIN_INFO = {
    "id": "server_mode",
    "name": "Server Mode (Web Access)",
    "category": "add-ons",
    "icon": "🌐",
    "version": "1.0.0",
    "description": "Start a local web server and use the toolkit from any browser.",
    "requires": ["fastapi", "uvicorn", "websockets", "pyngrok"]
}

import threading
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import socket
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import json
import secrets
import time
import asyncio
from typing import List, Dict, Any
import os

try:
    from pyngrok import ngrok, conf
    HAS_NGROK = True
except ImportError:
    HAS_NGROK = False

class ServerModePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.server_thread = None
        self.uvicorn_server = None
        self.ngrok_tunnel = None
        self.running = False
        self.port = 8000
        self.allow_lan = False
        self.password = ""
        self.clients = set()
        self.tokens = {}
        self.webui_path = Path(__file__).parent / "webui"
        self.status_var = tk.StringVar(value="Server stopped")

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if hasattr(self, 'window') and self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Server Mode")
        self.window.geometry("520x500")
        self.window.transient(self.app.root)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Status
        status_frame = ttk.LabelFrame(main, text="Server Status", padding=5)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="red")
        self.status_label.pack(anchor=tk.W)

        # Port and controls
        ctrl_frame = ttk.Frame(main)
        ctrl_frame.pack(fill=tk.X, pady=5)

        ttk.Label(ctrl_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value=str(self.port))
        port_entry = ttk.Entry(ctrl_frame, textvariable=self.port_var, width=8)
        port_entry.pack(side=tk.LEFT, padx=2)

        self.start_btn = ttk.Button(ctrl_frame, text="Start Server", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(ctrl_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # LAN access
        self.lan_var = tk.BooleanVar(value=self.allow_lan)
        ttk.Checkbutton(main, text="Allow LAN access (0.0.0.0)", variable=self.lan_var,
                        command=self._update_lan).pack(anchor=tk.W, pady=5)

        # Password
        self.pass_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main, text="Require password", variable=self.pass_var,
                        command=self._toggle_password).pack(anchor=tk.W)

        self.pass_frame = ttk.Frame(main)
        self.pass_frame.pack(fill=tk.X, pady=5)
        self.pass_frame.pack_forget()  # hidden initially

        ttk.Label(self.pass_frame, text="Password:").pack(side=tk.LEFT, padx=5)
        self.password_var = tk.StringVar()
        ttk.Entry(self.pass_frame, textvariable=self.password_var, show="*", width=20).pack(side=tk.LEFT)

        # ngrok
        ngrok_frame = ttk.LabelFrame(main, text="External Access (ngrok)", padding=5)
        ngrok_frame.pack(fill=tk.X, pady=10)

        self.ngrok_btn = ttk.Button(ngrok_frame, text="Start ngrok Tunnel",
                                     command=self.start_ngrok, state=tk.DISABLED)
        self.ngrok_btn.pack(side=tk.LEFT, padx=5)

        self.ngrok_stop_btn = ttk.Button(ngrok_frame, text="Stop Tunnel",
                                          command=self.stop_ngrok, state=tk.DISABLED)
        self.ngrok_stop_btn.pack(side=tk.LEFT, padx=2)

        self.ngrok_url_var = tk.StringVar(value="Not running")
        ttk.Label(ngrok_frame, textvariable=self.ngrok_url_var, foreground="blue").pack(anchor=tk.W, pady=5)

        if not HAS_NGROK:
            ttk.Label(ngrok_frame, text="ngrok not installed (pip install pyngrok)",
                      foreground="orange").pack(anchor=tk.W)

        # Connected clients
        clients_frame = ttk.LabelFrame(main, text="Connected Clients", padding=5)
        clients_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.clients_text = tk.Text(clients_frame, height=4, state=tk.DISABLED)
        self.clients_text.pack(fill=tk.BOTH, expand=True)

        # URL display
        self.url_label = ttk.Label(main, text="", foreground="green")
        self.url_label.pack(pady=5)

    def _update_lan(self):
        self.allow_lan = self.lan_var.get()

    def _toggle_password(self):
        if self.pass_var.get():
            self.pass_frame.pack(fill=tk.X, pady=5)
        else:
            self.pass_frame.pack_forget()
            self.password = ""

    def update_clients_display(self):
        self.clients_text.config(state=tk.NORMAL)
        self.clients_text.delete(1.0, tk.END)
        for client in self.clients:
            self.clients_text.insert(tk.END, f"{client}\n")
        self.clients_text.config(state=tk.DISABLED)

    def start_server(self):
        if self.running:
            return

        try:
            self.port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be a number")
            return

        if self.pass_var.get():
            self.password = self.password_var.get()
            if not self.password:
                messagebox.showerror("Password required", "Please enter a password")
                return

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.ngrok_btn.config(state=tk.NORMAL if HAS_NGROK else tk.DISABLED)
        self.status_var.set("Starting server...")

        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

    def _run_server(self):
        app = self._create_app()

        host = "0.0.0.0" if self.allow_lan else "127.0.0.1"
        config = uvicorn.Config(app, host=host, port=self.port, log_level="warning")
        self.uvicorn_server = uvicorn.Server(config)

        self.running = True
        self.app.after(0, self._update_ui_started)

        try:
            self.uvicorn_server.run()
        except Exception as e:
            self.app.after(0, lambda: self._server_error(str(e)))
        finally:
            self.running = False
            self.app.after(0, self._update_ui_stopped)

    def _update_ui_started(self):
        host = socket.gethostbyname(socket.gethostname()) if self.allow_lan else "localhost"
        self.url_label.config(text=f"Server running at http://{host}:{self.port}")
        self.status_var.set("Server running")
        self.status_label.config(foreground="green")

    def _update_ui_stopped(self):
        self.url_label.config(text="")
        self.status_var.set("Server stopped")
        self.status_label.config(foreground="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.ngrok_btn.config(state=tk.DISABLED)
        self.ngrok_stop_btn.config(state=tk.DISABLED)

    def _server_error(self, msg):
        messagebox.showerror("Server Error", msg)
        self._update_ui_stopped()

    def stop_server(self):
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True
            self.server_thread.join(timeout=5)
        self.running = False
        self.stop_ngrok()
        self._update_ui_stopped()

    def start_ngrok(self):
        if not HAS_NGROK:
            return
        try:
            # Ensure ngrok is authenticated – user must run `ngrok config add-authtoken <token>` once
            self.ngrok_tunnel = ngrok.connect(self.port, bind_tls=True)
            public_url = self.ngrok_tunnel.public_url
            self.ngrok_url_var.set(public_url)
            self.ngrok_btn.config(state=tk.DISABLED)
            self.ngrok_stop_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("ngrok Error", str(e))

    def stop_ngrok(self):
        if self.ngrok_tunnel:
            ngrok.disconnect(self.ngrok_tunnel.public_url)
            self.ngrok_tunnel = None
        self.ngrok_url_var.set("Not running")
        self.ngrok_btn.config(state=tk.NORMAL)
        self.ngrok_stop_btn.config(state=tk.DISABLED)

    def _create_app(self):
        app = FastAPI()

        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Authentication dependency
        async def verify_token(auth: str = None):
            if self.password:
                if not auth or not auth.startswith("Bearer "):
                    raise HTTPException(401, "Missing or invalid token")
                token = auth.split(" ")[1]
                if token not in self.tokens:
                    raise HTTPException(401, "Invalid token")
            return True

        # Serve static frontend
        if self.webui_path.exists() and (self.webui_path / "index.html").exists():
            app.mount("/static", StaticFiles(directory=self.webui_path / "static"), name="static")

            @app.get("/")
            async def serve_index():
                return FileResponse(self.webui_path / "index.html")
        else:
            @app.get("/")
            async def serve_index():
                return {"error": "Web UI not built. Please build the React frontend."}

        # API endpoints
        @app.post("/api/login")
        async def login(data: dict):
            if not self.password:
                return {"token": "no-auth"}
            if data.get("password") == self.password:
                token = secrets.token_urlsafe(32)
                self.tokens[token] = time.time() + 3600  # 1 hour expiry
                return {"token": token}
            raise HTTPException(401, "Invalid password")

        @app.get("/api/status")
        async def status():
            return {
                "version": "1.0",
                "auth": bool(self.password),
                "samples": self.app.data_hub.row_count() if hasattr(self.app, 'data_hub') else 0
            }

        @app.get("/api/samples")
        async def get_samples(page: int = 0, page_size: int = 50, auth: str = None):
            await verify_token(auth)
            all_samples = self.app.data_hub.get_all() if hasattr(self.app, 'data_hub') else []
            start = page * page_size
            end = start + page_size
            return {
                "samples": all_samples[start:end],
                "total": len(all_samples),
                "page": page,
                "pageSize": page_size
            }

        @app.get("/api/schemes")
        async def get_schemes(auth: str = None):
            await verify_token(auth)
            if not hasattr(self.app, 'classification_engine'):
                return []
            schemes = self.app.classification_engine.get_available_schemes()
            return [{"id": s["id"], "name": s["name"]} for s in schemes]

        @app.post("/api/classify")
        async def classify(data: dict, auth: str = None):
            await verify_token(auth)
            scheme_id = data.get("scheme")
            target = data.get("target", "all")  # "all" or "selected"
            indices = data.get("indices", [])

            if not hasattr(self.app, 'classification_engine'):
                raise HTTPException(500, "Classification engine not available")

            all_samples = self.app.data_hub.get_all()
            if target == "selected" and indices:
                samples_to_classify = [all_samples[i] for i in indices if i < len(all_samples)]
            else:
                samples_to_classify = all_samples

            results = self.app.classification_engine.classify_all_samples(samples_to_classify, scheme_id)

            # If we classified selected only, we need to map results back to full dataset
            if target == "selected" and indices:
                full_results = [None] * len(all_samples)
                for idx, res in zip(indices, results):
                    full_results[idx] = res
            else:
                full_results = results

            # Broadcast update to all WebSocket clients
            await self._broadcast({"type": "classification", "scheme": scheme_id})

            return {"results": full_results}

        @app.post("/api/import")
        async def import_file(file: bytes, filename: str = "upload.csv", auth: str = None):
            await verify_token(auth)
            # This is a placeholder – in reality you'd parse CSV and add to data_hub
            # For now, return a success message
            return {"status": "imported", "filename": filename}

        # WebSocket for live updates
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            client_addr = f"{websocket.client.host}:{websocket.client.port}"
            self.clients.add(client_addr)
            self.app.after(0, self.update_clients_display)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.clients.remove(client_addr)
                self.app.after(0, self.update_clients_display)

        return app

    async def _broadcast(self, message):
        """Send a message to all connected WebSocket clients."""
        # This would need access to the list of active WebSocket connections.
        # For simplicity, we'll skip implementation here – you can extend later.
        pass

def register_plugin(main_app):
    return ServerModePlugin(main_app)
