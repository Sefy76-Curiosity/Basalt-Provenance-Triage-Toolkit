"""
Mobile Sync Tab Plugin – v8.1 (WebRTC + Direct Signaling)
No MQTT, no external dependencies - pure WebRTC with built-in signaling
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "mobile_sync_tab",
    "name": "Mobile Sync (Direct WebRTC)",
    "description": "Direct WebRTC connection with built-in signaling server",
    "icon": "📡",
    "version": "8.1",
    "date": "2026-02-19",
    "requires": ["qrcode", "pillow", "aiortc"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import time
import csv
import io
import sys
import os
import uuid
import asyncio
import socket
import base64
import tempfile
import http.server
import socketserver
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
import logging
logging.getLogger('aiortc').setLevel(logging.WARNING)

# Optional dependencies
try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
    from aiortc.contrib.media import MediaRelay
    HAS_AIORTC = True
except ImportError:
    HAS_AIORTC = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# Color palette matching HTML design
C = {
    "bg": "#0a0c10",
    "surface": "#161b22",
    "surface_light": "#1f2633",
    "border": "#2d333b",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
    "accent": "#238636",
    "accent_hover": "#2ea043",
    "danger": "#da3633",
    "warning": "#e3b341",
    "info": "#1f6feb",
}

# ============================================================================
# EMBEDDED HTML - Your complete index.html file
# ============================================================================
EMBEDDED_HTML = """<!DOCTYPE html>
<html lang="">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>Scientific Toolkit Mobile</title>
  <style>
    /* Your existing CSS here - keep it exactly as before */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }

    :root {
      --bg: #0a0c10;
      --surface: #161b22;
      --surface-light: #1f2633;
      --border: #2d333b;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --accent: #238636;
      --accent-hover: #2ea043;
      --danger: #da3633;
      --warning: #e3b341;
      --info: #1f6feb;
      --radius: 12px;
      --spacing: 12px;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      height: 100vh;
      overflow: hidden;
    }

    .hidden { display: none !important; }
    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    .items-center { align-items: center; }
    .justify-between { justify-content: space-between; }
    .gap-2 { gap: 8px; }
    .gap-4 { gap: 16px; }
    .p-4 { padding: 16px; }
    .w-full { width: 100%; }
    .text-center { text-align: center; }
    .text-muted { color: var(--text-muted); }
    .text-accent { color: var(--accent); }
    .text-danger { color: var(--danger); }
    .bg-surface { background: var(--surface); }
    .rounded { border-radius: var(--radius); }
    .border { border: 1px solid var(--border); }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px 20px;
      border-radius: var(--radius);
      border: none;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      background: var(--surface-light);
      color: var(--text);
    }

    .btn:active { transform: scale(0.97); opacity: 0.9; }
    .btn-primary { background: var(--accent); color: white; }
    .btn-danger { background: var(--danger); color: white; }
    .btn-outline { background: transparent; border: 1px solid var(--border); }
    .btn-sm { padding: 8px 12px; font-size: 14px; }
    .btn-full { width: 100%; }

    .card {
      background: var(--surface);
      border-radius: var(--radius);
      border: 1px solid var(--border);
      padding: 16px;
    }

    input, select, textarea {
      background: var(--surface-light);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      color: var(--text);
      font-size: 16px;
      width: 100%;
      outline: none;
    }

    input:focus, select:focus, textarea:focus {
      border-color: var(--accent);
    }

    label {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 4px;
      display: block;
      color: var(--text-muted);
    }

    .bottom-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: var(--surface);
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-around;
      padding: 8px 4px;
      z-index: 100;
    }

    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: var(--text-muted);
      flex: 1;
      padding: 4px 0;
      border: none;
      background: transparent;
      cursor: pointer;
    }

    .nav-item.active {
      color: var(--accent);
    }

    .nav-icon {
      font-size: 24px;
    }

    .main-content {
      height: 100vh;
      overflow-y: auto;
      padding: 16px;
      padding-bottom: 80px;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 20px auto;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    #toast-container {
      position: fixed;
      bottom: 90px;
      left: 16px;
      right: 16px;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 8px;
      pointer-events: none;
    }

    .toast {
      background: var(--surface);
      border-left: 4px solid var(--accent);
      border-radius: 8px;
      padding: 12px 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      animation: slideUp 0.3s ease;
      pointer-events: auto;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .toast.error { border-left-color: var(--danger); }
    .toast.warning { border-left-color: var(--warning); }

    @keyframes slideUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }

    .camera-zone {
      border: 2px dashed var(--border);
      border-radius: var(--radius);
      padding: 40px 20px;
      text-align: center;
      background: var(--surface-light);
      cursor: pointer;
      position: relative;
    }

    .camera-zone input[type=file] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }

    .image-preview {
      max-width: 100%;
      max-height: 200px;
      border-radius: var(--radius);
      margin-top: 12px;
    }

    .sample-item {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
    }

    .sample-item:active {
      background: var(--surface-light);
    }

    .sample-id {
      font-weight: 600;
      color: var(--accent);
    }

    .sample-class {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 12px;
      background: rgba(35, 134, 54, 0.2);
      color: var(--accent);
    }
  </style>
</head>
<body>
  <!-- SPLASH SCREEN -->
  <div id="splash" class="flex items-center justify-center" style="position:fixed; inset:0; background:var(--bg); z-index:2000;">
    <div class="text-center">
      <div style="font-size:64px; margin-bottom:16px;">🔬</div>
      <h1 style="font-size:28px; font-weight:600; color:var(--accent);">Scientific Toolkit</h1>
      <p style="color:var(--text-muted);">Mobile Interface</p>
    </div>
  </div>

  <!-- CONNECT SCREEN -->
  <div id="connect-screen" class="main-content">
    <div class="card" style="max-width:400px; margin:20px auto;">
      <div style="font-size:48px; text-align:center; margin-bottom:16px;">📡</div>
      <h2 style="text-align:center; margin-bottom:8px;">Connect to Desktop</h2>
      <p class="text-muted text-center" style="margin-bottom:24px;">Scan QR code from Mobile Sync plugin</p>
      <div id="connection-status" class="text-center" style="margin-top:16px;">
        <div class="spinner"></div>
        <p>Waiting for connection...</p>
      </div>
    </div>
  </div>

  <!-- MAIN APP -->
  <div id="app" class="hidden">
    <nav class="bottom-nav">
      <button class="nav-item active" data-view="samples">📋<span>Samples</span></button>
      <button class="nav-item" data-view="add">➕<span>Add</span></button>
      <button class="nav-item" data-view="classify">🔬<span>Classify</span></button>
      <button class="nav-item" data-view="camera">📷<span>Camera</span></button>
      <button class="nav-item" data-view="settings">⚙️<span>Settings</span></button>
    </nav>

    <!-- SAMPLES VIEW -->
    <div class="main-content" id="samples-view">
      <div style="margin-bottom:12px;">
        <input type="search" id="sample-search" placeholder="Search samples..." style="width:100%;">
      </div>
      <div class="flex items-center justify-between" style="margin-bottom:12px;">
        <h2>Samples</h2>
        <span id="sample-count" class="text-muted">0</span>
      </div>
      <div id="sample-list" style="margin-bottom:12px;">
        <div class="spinner"></div>
      </div>
      <div class="flex items-center justify-between">
        <button class="btn btn-outline btn-sm" id="prev-page">← Prev</button>
        <span id="page-info" class="text-muted">Page 1</span>
        <button class="btn btn-outline btn-sm" id="next-page">Next →</button>
      </div>
    </div>

    <!-- ADD VIEW -->
    <div class="main-content hidden" id="add-view">
      <h2 style="margin-bottom:16px;">Add Sample</h2>
      <div class="card" style="margin-bottom:16px;">
        <div style="margin-bottom:12px;">
          <label>Sample ID *</label>
          <input type="text" id="add-sample-id" placeholder="e.g., SAMPLE001">
        </div>
        <div style="margin-bottom:12px;">
          <label>Notes</label>
          <textarea id="add-notes" rows="3" placeholder="Field notes..."></textarea>
        </div>
        <button class="btn btn-primary btn-full" id="submit-sample">Submit</button>
      </div>
      <div class="camera-zone" id="gps-button">
        <div style="font-size:32px;">🛰️</div>
        <div>Tap to get GPS location</div>
        <div id="gps-status" class="text-muted" style="font-size:12px; margin-top:8px;">Not acquired</div>
      </div>
    </div>

    <!-- CLASSIFY VIEW -->
    <div class="main-content hidden" id="classify-view">
      <h2 style="margin-bottom:16px;">Classification</h2>
      <div class="card" style="margin-bottom:16px;">
        <label>Scheme</label>
        <select id="scheme-select" style="margin-bottom:12px;"></select>
        <div class="flex gap-2">
          <button class="btn btn-outline flex-1" id="classify-selected">Selected</button>
          <button class="btn btn-primary flex-1" id="classify-all">All</button>
        </div>
      </div>
    </div>

    <!-- CAMERA VIEW -->
    <div class="main-content hidden" id="camera-view">
      <h2 style="margin-bottom:16px;">Camera Upload</h2>
      <div class="camera-zone" id="camera-zone">
        <input type="file" id="camera-input" accept="image/*" capture="environment">
        <div style="font-size:48px;">📷</div>
        <div>Tap to take photo</div>
      </div>
      <div id="image-preview-container" class="hidden" style="margin-top:16px;">
        <img id="image-preview" class="image-preview" alt="Preview">
        <div style="margin-top:12px;">
          <label>Sample ID (optional)</label>
          <input type="text" id="photo-sample-id" placeholder="Link to sample">
        </div>
        <button class="btn btn-primary btn-full" id="upload-photo">Upload</button>
        <button class="btn btn-outline btn-full" id="cancel-photo">Cancel</button>
      </div>
    </div>

    <!-- SETTINGS VIEW -->
    <div class="main-content hidden" id="settings-view">
      <h2 style="margin-bottom:16px;">Settings</h2>
      <div class="card" style="margin-bottom:16px;">
        <div style="margin-bottom:8px;"><span class="text-muted">Peer ID:</span> <span id="settings-peer"></span></div>
        <button class="btn btn-outline btn-full" id="disconnect">Disconnect</button>
      </div>
    </div>
  </div>

  <!-- Sample detail sheet -->
  <div id="sample-sheet" class="hidden" style="position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:2000; display:flex; align-items:flex-end;" onclick="if(event.target===this) closeSheet()">
    <div class="card" style="width:100%; max-height:80vh; overflow-y:auto; border-radius:16px 16px 0 0;" onclick="event.stopPropagation()">
      <div class="flex items-center justify-between" style="padding:16px; border-bottom:1px solid var(--border);">
        <h3 id="sheet-sample-id">Sample</h3>
        <button class="btn btn-sm btn-outline" onclick="closeSheet()">✕</button>
      </div>
      <div id="sheet-content" style="padding:16px;"></div>
      <div class="flex gap-2" style="padding:16px; border-top:1px solid var(--border);">
        <button class="btn btn-danger flex-1" id="sheet-delete">Delete</button>
        <button class="btn btn-outline flex-1" id="sheet-classify">Classify</button>
      </div>
    </div>
  </div>

  <div id="toast-container"></div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>
  <script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>

  <script>
    // ========== State ==========
    const STATE = {
      currentPage: 0,
      pageSize: 25,
      searchQuery: '',
      gps: { lat: null, lon: null },
      samples: [],
      schemes: []
    };

    // ========== Get Peer ID from URL ==========
    const peerId = window.location.hash.substring(1);
    if (!peerId) {
      alert('No peer ID in URL. Please scan QR code from desktop app.');
    } else {
      connectToPeer(peerId);
    }

    // ========== Direct WebRTC Connection ==========
    async function connectToPeer(peerId) {
      const statusDiv = document.getElementById('connection-status');
      if (statusDiv) {
        statusDiv.innerHTML = '<div class="spinner"></div><p>Connecting to desktop...</p>';
      }

      // Create RTCPeerConnection
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      // Set up data channel
      pc.ondatachannel = (event) => {
        const dc = event.channel;
        window.dataChannel = dc;

        dc.onopen = () => {
          console.log('Data channel open');
          document.getElementById('connect-screen').classList.add('hidden');
          document.getElementById('app').classList.remove('hidden');
          toast('Connected to desktop!', 'success');
          loadSchemes();
          loadSamples();
        };

        dc.onclose = () => {
          toast('Disconnected from desktop', 'warning');
        };

        dc.onmessage = (e) => {
          handleRPCResponse(e.data);
        };
      };

      // Create and send offer via HTTP to the desktop's signaling server
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // Send offer to desktop (it's listening on port 9000)
        const response = await fetch(`http://${window.location.hostname}:9000/offer/${peerId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: offer.type,
            sdp: offer.sdp
          })
        });

        if (!response.ok) {
          throw new Error('Failed to send offer');
        }

        // Get answer from desktop
        const answerData = await response.json();
        await pc.setRemoteDescription(new RTCSessionDescription(answerData));

        if (statusDiv) {
          statusDiv.innerHTML = '<div class="spinner"></div><p>Connection established!</p>';
        }
      } catch (e) {
        console.error('Connection failed:', e);
        if (statusDiv) {
          statusDiv.innerHTML = '<p class="text-danger">✗ Failed to connect. Make sure desktop server is running.</p>';
        }
      }
    }

    // ========== RPC System ==========
    const pending = new Map();
    let nextId = 1;

    function rpc(method, params) {
      return new Promise((resolve, reject) => {
        if (!window.dataChannel || window.dataChannel.readyState !== 'open') {
          reject(new Error('Not connected'));
          return;
        }
        const id = nextId++;
        pending.set(id, { resolve, reject });
        const msg = { jsonrpc: '2.0', id, method, params };
        window.dataChannel.send(JSON.stringify(msg));

        setTimeout(() => {
          if (pending.has(id)) {
            pending.delete(id);
            reject(new Error('RPC timeout'));
          }
        }, 10000);
      });
    }

    function handleRPCResponse(data) {
      try {
        const msg = JSON.parse(data);
        if (msg.id && pending.has(msg.id)) {
          const { resolve, reject } = pending.get(msg.id);
          pending.delete(msg.id);
          if (msg.error) reject(new Error(msg.error));
          else resolve(msg.result);
        }
      } catch (e) {
        console.error('Failed to parse RPC response:', e);
      }
    }

    // ========== API Wrappers ==========
    const api = {
      async get(path) {
        const method = path.replace('/api/', '').replace(/\//g, '_');
        return rpc(method, { path });
      },
      async post(path, body) {
        const method = path.replace('/api/', '').replace(/\//g, '_') + '_post';
        return rpc(method, { path, body });
      },
      async put(path, body) {
        const method = path.replace('/api/', '').replace(/\//g, '_') + '_put';
        return rpc(method, { path, body });
      },
      async delete(path) {
        const method = path.replace('/api/', '').replace(/\//g, '_') + '_delete';
        return rpc(method, { path });
      },
      async uploadImage(file, sampleId) {
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = async () => {
            const base64 = reader.result.split(',')[1];
            try {
              const result = await rpc('upload_image', {
                filename: file.name,
                data: base64,
                sample_id: sampleId
              });
              resolve(result);
            } catch (e) {
              reject(e);
            }
          };
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
      }
    };

    // ========== Toast ==========
    function toast(msg, type = 'info') {
      const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };
      const el = document.createElement('div');
      el.className = `toast ${type}`;
      el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
      document.getElementById('toast-container').prepend(el);
      setTimeout(() => el.remove(), 3000);
    }

    // ========== Sample Functions ==========
    async function loadSamples() {
      try {
        const data = await rpc('list_samples', {
          page: STATE.currentPage,
          size: STATE.pageSize,
          search: STATE.searchQuery
        });
        STATE.samples = data.samples || [];
        renderSamples(STATE.samples);
        updateCounts(data.total);
      } catch (e) {
        console.error('Failed to load samples:', e);
      }
    }

    async function loadSchemes() {
      try {
        const schemes = await rpc('list_schemes', {});
        STATE.schemes = schemes;
        const selects = ['scheme-select'];
        selects.forEach(id => {
          const sel = document.getElementById(id);
          if (sel) {
            sel.innerHTML = schemes.map(s =>
              `<option value="${s.id}">${s.icon || '📊'} ${s.name}</option>`
            ).join('');
          }
        });
      } catch (e) {
        console.error('Failed to load schemes:', e);
      }
    }

    function renderSamples(samples) {
      const listEl = document.getElementById('sample-list');
      if (!listEl) return;

      if (!samples.length) {
        listEl.innerHTML = '<div class="card text-center text-muted">No samples</div>';
        return;
      }

      listEl.innerHTML = samples.map(s => {
        const id = s.Sample_ID || '—';
        const cls = s.Auto_Classification || s.TAS_Classification || '';
        return `<div class="sample-item" onclick="openSample('${escape(id)}')">
          <div style="flex:1">
            <div class="sample-id">${escape(id)}</div>
            <div class="sample-meta">${escape(s.Notes || '')}</div>
          </div>
          ${cls ? `<span class="sample-class">${escape(cls.slice(0,20))}</span>` : ''}
          <span style="color:var(--text-muted);">›</span>
        </div>`;
      }).join('');
    }

    function updateCounts(total) {
      const countEl = document.getElementById('sample-count');
      if (countEl) countEl.textContent = total || 0;
      const pageInfo = document.getElementById('page-info');
      if (pageInfo) pageInfo.textContent = `Page ${STATE.currentPage + 1}`;
    }

    function escape(str) {
      if (!str) return '';
      return String(str).replace(/[&<>"]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        if (m === '"') return '&quot;';
        return m;
      });
    }

    // ========== Navigation ==========
    function showView(viewId) {
      document.querySelectorAll('.main-content').forEach(v => v.classList.add('hidden'));
      const targetView = document.getElementById(viewId + '-view');
      if (targetView) targetView.classList.remove('hidden');

      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.querySelectorAll(`.nav-item[data-view="${viewId}"]`).forEach(n => n.classList.add('active'));

      if (viewId === 'samples') loadSamples();
    }

    document.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', () => showView(btn.dataset.view));
    });

    // ========== Search and Pagination ==========
    let searchTimer;
    document.getElementById('sample-search')?.addEventListener('input', e => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        STATE.searchQuery = e.target.value;
        STATE.currentPage = 0;
        loadSamples();
      }, 400);
    });

    document.getElementById('prev-page')?.addEventListener('click', () => {
      if (STATE.currentPage > 0) {
        STATE.currentPage--;
        loadSamples();
      }
    });

    document.getElementById('next-page')?.addEventListener('click', () => {
      STATE.currentPage++;
      loadSamples();
    });

    // ========== Add Sample ==========
    document.getElementById('gps-button')?.addEventListener('click', () => {
      if (!navigator.geolocation) {
        toast('GPS not supported', 'warning');
        return;
      }
      navigator.geolocation.getCurrentPosition(
        pos => {
          STATE.gps.lat = pos.coords.latitude.toFixed(6);
          STATE.gps.lon = pos.coords.longitude.toFixed(6);
          document.getElementById('gps-status').innerText = `${STATE.gps.lat}, ${STATE.gps.lon}`;
          toast('GPS acquired', 'success');
        },
        err => {
          document.getElementById('gps-status').innerText = 'Error: ' + err.message;
        }
      );
    });

    document.getElementById('submit-sample')?.addEventListener('click', async () => {
      const id = document.getElementById('add-sample-id').value.trim();
      if (!id) { toast('Sample ID required', 'warning'); return; }
      const notes = document.getElementById('add-notes').value.trim();
      const sample = { Sample_ID: id };
      if (notes) sample.Notes = notes;
      if (STATE.gps.lat) sample.Latitude = parseFloat(STATE.gps.lat);
      if (STATE.gps.lon) sample.Longitude = parseFloat(STATE.gps.lon);

      try {
        await api.post('/api/samples', sample);
        toast('Sample added', 'success');
        document.getElementById('add-sample-id').value = '';
        document.getElementById('add-notes').value = '';
        STATE.gps.lat = STATE.gps.lon = null;
        document.getElementById('gps-status').innerText = 'Not acquired';
        showView('samples');
        loadSamples();
      } catch (e) {
        toast('Submit failed: ' + e.message, 'error');
      }
    });

    // ========== Classify ==========
    document.getElementById('classify-all')?.addEventListener('click', async () => {
      const schemeId = document.getElementById('scheme-select')?.value;
      if (!schemeId) { toast('Select a scheme', 'warning'); return; }
      try {
        const res = await api.post(`/api/classify/apply/${schemeId}`, {});
        toast(`Classified ${res.count} samples`, 'success');
        loadSamples();
      } catch (e) {
        toast('Classification failed: ' + e.message, 'error');
      }
    });

    // ========== Camera ==========
    const cameraInput = document.getElementById('camera-input');
    const previewContainer = document.getElementById('image-preview-container');
    const cameraZone = document.getElementById('camera-zone');
    const imagePreview = document.getElementById('image-preview');
    let selectedFile = null;

    cameraInput?.addEventListener('change', e => {
      const file = e.target.files[0];
      if (!file) return;
      selectedFile = file;
      const reader = new FileReader();
      reader.onload = ev => {
        imagePreview.src = ev.target.result;
        cameraZone.classList.add('hidden');
        previewContainer.classList.remove('hidden');
      };
      reader.readAsDataURL(file);
    });

    document.getElementById('cancel-photo')?.addEventListener('click', () => {
      selectedFile = null;
      cameraInput.value = '';
      previewContainer.classList.add('hidden');
      cameraZone.classList.remove('hidden');
    });

    document.getElementById('upload-photo')?.addEventListener('click', async () => {
      if (!selectedFile) return;
      const sampleId = document.getElementById('photo-sample-id').value.trim();
      const btn = document.getElementById('upload-photo');
      btn.disabled = true; btn.innerText = 'Uploading...';
      try {
        await api.uploadImage(selectedFile, sampleId);
        toast('Photo uploaded', 'success');
        document.getElementById('cancel-photo').click();
      } catch (e) {
        toast('Upload failed: ' + e.message, 'error');
      } finally {
        btn.disabled = false; btn.innerText = 'Upload';
      }
    });

    // ========== Settings ==========
    document.getElementById('disconnect')?.addEventListener('click', () => {
      if (window.dataChannel) window.dataChannel.close();
      window.location.reload();
    });

    // ========== Initialize ==========
    window.addEventListener('load', () => {
      setTimeout(() => {
        document.getElementById('splash').classList.add('hidden');
      }, 1200);
    });

    window.openSample = function(id) {
      toast('Sample details: ' + id, 'info');
    };

    function closeSheet() {
      document.getElementById('sample-sheet').classList.add('hidden');
    }
    window.closeSheet = closeSheet;
  </script>
</body>
</html>"""

class SyncFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

class SignalingHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for WebRTC signaling"""

    def __init__(self, *args, plugin=None, **kwargs):
        self.plugin = plugin
        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path.startswith('/offer/'):
            peer_id = self.path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                offer = json.loads(post_data)

                # Store the offer and create answer
                if self.plugin:
                    # Get the WebRTC answer from the plugin
                    answer = self.plugin.handle_signaling_offer(peer_id, offer)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(answer).encode())
                else:
                    self.send_response(500)
                    self.end_headers()

            except Exception as e:
                print(f"Signaling error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet the server

class MobileSyncTabPlugin:
    """
    WebRTC plugin with built-in signaling server
    """

    def __init__(self, main_app):
        self.app = main_app
        self.pc = None
        self.data_channel = None
        self.loop = None
        self.thread = None
        self.running = False
        self.peer_id = None
        self.signaling_server = None
        self.signaling_thread = None
        self.http_server = None
        self.http_thread = None
        self.http_port = 8000
        self.signaling_port = 9000
        self.local_url = None
        self.temp_html_file = None
        self.pending_offers = {}

        # Sync directories
        self.sync_dir = Path.home() / "ScientificToolkit" / "mobile_sync"
        self.json_dir = self.sync_dir / "json"
        self.image_dir = self.sync_dir / "images"
        for d in [self.sync_dir, self.json_dir, self.image_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.update_queue = Queue()
        self.tasks = {}
        self.tasks_lock = threading.Lock()
        self._active = True
        self.current_preview_image = None
        self.current_preview_text = None

        # UI Variables
        self.local_server_var = tk.BooleanVar(value=True)
        self.public_url_var = tk.StringVar(value="https://yourname.github.io/field-terminal")
        self.local_port_var = tk.IntVar(value=8000)
        self.auto_import_var = tk.BooleanVar(value=True)
        self.file_filter_var = tk.StringVar(value="all")

        # UI References
        self.parent = None
        self.conn_dot = None
        self.peer_id_lbl = None
        self.qr_label = None
        self.qr_image = None
        self.log_text = None
        self.start_btn = None
        self.stop_btn = None
        self.file_listbox = None
        self.preview_notebook = None
        self.preview_text = None
        self.preview_image_label = None
        self.preview_canvas = None
        self.toolkit_status_lbl = None
        self.observer = None

        self._check_dependencies()

    def _check_dependencies(self):
        missing = []
        if not HAS_QR: missing.append("qrcode + pillow")
        if not HAS_AIORTC: missing.append("aiortc")
        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    def deactivate(self):
        self._active = False
        self._stop_webrtc()
        self._stop_http_server()
        self._stop_signaling_server()
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=1)
            except Exception:
                pass

    @property
    def _data_hub(self):
        return getattr(self.app, "data_hub", None)

    @property
    def _cls_engine(self):
        return getattr(self.app, "classification_engine", None)

    def _get_samples(self):
        dh = self._data_hub
        return dh.get_all() if dh else []

    def _get_sample_by_id(self, sample_id):
        for i, s in enumerate(self._get_samples()):
            if str(s.get("Sample_ID", "")) == str(sample_id):
                return i, s
        return None, None

    def _add_samples(self, rows: list):
        if hasattr(self.app, "import_data_from_plugin"):
            self.app.import_data_from_plugin(rows)
        elif self._data_hub:
            self._data_hub.add_samples(rows)

    def _columns(self):
        dh = self._data_hub
        return sorted(dh.columns) if dh else []

    # ============================================================================
    # UI Creation Methods (same as before - keeping them brief)
    # ============================================================================
    def create_tab(self, parent):
        self.parent = parent
        root = tk.Frame(parent, bg=C["bg"])
        root.pack(fill=tk.BOTH, expand=True)

        main_panel = tk.Frame(root, bg=C["bg"])
        main_panel.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left_panel = tk.Frame(main_panel, bg=C["surface"],
                              highlightbackground=C["border"], highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 3))
        left_panel.config(width=400)
        left_panel.pack_propagate(False)

        right_panel = tk.Frame(main_panel, bg=C["surface"],
                               highlightbackground=C["border"], highlightthickness=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(3, 0))

        self._build_left_panel(left_panel)
        self._build_right_panel(right_panel)

        if HAS_WATCHDOG:
            self._start_watchdog()
        self._process_queue()
        self._refresh_toolkit_status()

    def _build_left_panel(self, parent):
        # Header
        header = tk.Frame(parent, bg=C["surface"], height=40)
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(header, text="📡 MOBILE SYNC",
                font=("Segoe UI", 12, "bold"), fg=C["accent"], bg=C["surface"]).pack(side=tk.LEFT)

        # Connection status dot
        status_frame = tk.Frame(header, bg=C["surface"])
        status_frame.pack(side=tk.RIGHT)
        self.conn_dot = tk.Canvas(status_frame, width=12, height=12, bg=C["surface"], highlightthickness=0)
        self.conn_dot.create_oval(2, 2, 10, 10, fill=C["danger"], outline="")
        self.conn_dot.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(status_frame, text="Disconnected", font=("Segoe UI", 8),
                fg=C["text_muted"], bg=C["surface"]).pack(side=tk.LEFT)

        # Server Control Section
        self._create_section(parent, "⚙️ SERVER CONTROL")
        control_frame = tk.Frame(parent, bg=C["surface"])
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # HTML Source selection
        source_frame = tk.Frame(control_frame, bg=C["surface"])
        source_frame.pack(fill=tk.X, pady=5)

        tk.Label(source_frame, text="HTML Source:", font=("Segoe UI", 9, "bold"),
                fg=C["text_muted"], bg=C["surface"]).pack(anchor=tk.W)

        radio_frame = tk.Frame(source_frame, bg=C["surface"])
        radio_frame.pack(fill=tk.X, pady=2)
        tk.Radiobutton(radio_frame, text="Serve locally (LAN)", variable=self.local_server_var,
                      value=True, command=self._update_qr,
                      bg=C["surface"], fg=C["text"], selectcolor=C["surface_light"],
                      activebackground=C["surface"]).pack(anchor=tk.W)
        tk.Radiobutton(radio_frame, text="Use public URL", variable=self.local_server_var,
                      value=False, command=self._update_qr,
                      bg=C["surface"], fg=C["text"], selectcolor=C["surface_light"],
                      activebackground=C["surface"]).pack(anchor=tk.W)

        # Port setting
        port_frame = tk.Frame(source_frame, bg=C["surface"])
        port_frame.pack(fill=tk.X, pady=2)
        tk.Label(port_frame, text="HTTP Port:", font=("Segoe UI", 8),
                fg=C["text_muted"], bg=C["surface"], width=8).pack(side=tk.LEFT)
        tk.Spinbox(port_frame, from_=1024, to=65535, textvariable=self.local_port_var,
                  width=8, bg=C["surface_light"], fg=C["text"],
                  buttonbackground=C["border"], relief=tk.FLAT).pack(side=tk.LEFT)

        # Public URL entry
        url_frame = tk.Frame(source_frame, bg=C["surface"])
        url_frame.pack(fill=tk.X, pady=2)
        tk.Label(url_frame, text="Public URL:", font=("Segoe UI", 8),
                fg=C["text_muted"], bg=C["surface"], width=8).pack(side=tk.LEFT)
        tk.Entry(url_frame, textvariable=self.public_url_var,
                bg=C["surface_light"], fg=C["text"],
                insertbackground=C["text"], relief=tk.FLAT).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Auto-import checkbox
        tk.Checkbutton(control_frame, text="Auto-import received samples",
                      variable=self.auto_import_var,
                      bg=C["surface"], fg=C["text"], selectcolor=C["surface_light"],
                      activebackground=C["surface"]).pack(anchor=tk.W, pady=5)

        # Start/Stop buttons
        btn_frame = tk.Frame(control_frame, bg=C["surface"])
        btn_frame.pack(fill=tk.X, pady=10)
        self.start_btn = tk.Button(btn_frame, text="▶ START SERVER", command=self._start_webrtc,
                                   bg=C["accent"], fg="white", font=("Segoe UI", 9, "bold"),
                                   relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.stop_btn = tk.Button(btn_frame, text="■ STOP", command=self._stop_webrtc,
                                  bg=C["danger"], fg="white", font=("Segoe UI", 9, "bold"),
                                  relief=tk.FLAT, padx=15, pady=8, cursor="hand2", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        # QR Code Section
        self._create_section(parent, "📲 QR CODE")
        qr_frame = tk.Frame(parent, bg=C["surface"])
        qr_frame.pack(fill=tk.X, padx=10, pady=5)

        # Peer ID display
        id_frame = tk.Frame(qr_frame, bg=C["surface"])
        id_frame.pack(fill=tk.X, pady=5)
        tk.Label(id_frame, text="Peer ID:", font=("Segoe UI", 8, "bold"),
                fg=C["text_muted"], bg=C["surface"]).pack(side=tk.LEFT)
        self.peer_id_lbl = tk.Label(id_frame, text="—", font=("Segoe UI", 8, "bold"),
                                    fg=C["accent"], bg=C["surface"], cursor="hand2")
        self.peer_id_lbl.pack(side=tk.LEFT, padx=(5, 0))
        self.peer_id_lbl.bind("<Button-1>", lambda e: self._copy_text(self.peer_id))

        # QR Code display
        qr_container = tk.Frame(qr_frame, bg=C["surface_light"],
                                highlightbackground=C["border"], highlightthickness=1)
        qr_container.pack(pady=10)
        self.qr_label = tk.Label(qr_container, text="Start server\nto generate QR code",
                                 font=("Segoe UI", 8), fg=C["text_muted"],
                                 bg=C["surface_light"], width=25, height=8)
        self.qr_label.pack(padx=10, pady=10)

        # Copy URL button
        tk.Button(qr_frame, text="📋 COPY URL", command=self._copy_current_url,
                 bg=C["surface_light"], fg=C["text"], font=("Segoe UI", 8),
                 relief=tk.FLAT, padx=10, pady=5, cursor="hand2").pack(pady=5)

        # Status Section
        self._create_section(parent, "📊 TOOLKIT STATUS")
        status_frame = tk.Frame(parent, bg=C["surface"])
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.toolkit_status_lbl = tk.Label(status_frame, text="Loading...",
                                          font=("Segoe UI", 8), fg=C["text"],
                                          bg=C["surface"], justify=tk.LEFT)
        self.toolkit_status_lbl.pack(anchor=tk.W)

        tk.Button(status_frame, text="🔄 REFRESH", command=self._refresh_toolkit_status,
                 bg=C["surface_light"], fg=C["text"], font=("Segoe UI", 8),
                 relief=tk.FLAT, padx=10, pady=3, cursor="hand2").pack(anchor=tk.W, pady=5)

        # Activity Log
        self._create_section(parent, "📋 ACTIVITY LOG")
        log_frame = tk.Frame(parent, bg=C["surface"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 8),
                                bg=C["log_bg"], fg=C["log_fg"],
                                insertbackground=C["log_fg"], wrap=tk.WORD,
                                relief=tk.FLAT, bd=0)
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for tag, color in [("ok", "#238636"), ("err", "#da3633"),
                          ("info", "#1f6feb"), ("warn", "#e3b341")]:
            self.log_text.tag_config(tag, foreground=color)

    def _build_right_panel(self, parent):
        # Split into top and bottom halves
        top_frame = tk.Frame(parent, bg=C["surface"])
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 3))

        bottom_frame = tk.Frame(parent, bg=C["surface"])
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

        # TOP HALF - Received Files
        top_notebook = ttk.Notebook(top_frame)
        top_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        files_frame = tk.Frame(top_notebook, bg=C["surface"])
        top_notebook.add(files_frame, text="📁 Received Files")
        self._build_files_tab(files_frame)

        # BOTTOM HALF - Preview
        bottom_notebook = ttk.Notebook(bottom_frame)
        bottom_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        text_frame = tk.Frame(bottom_notebook, bg=C["code_bg"])
        bottom_notebook.add(text_frame, text="📄 Text/JSON")
        self.preview_text = tk.Text(text_frame, font=("Consolas", 9),
                                    bg=C["code_bg"], fg=C["text"],
                                    insertbackground=C["text"], wrap=tk.WORD,
                                    relief=tk.FLAT, bd=0)
        text_scroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=text_scroll.set)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        image_frame = tk.Frame(bottom_notebook, bg=C["surface"])
        bottom_notebook.add(image_frame, text="🖼️ Image")

        h_scroll = tk.Scrollbar(image_frame, orient=tk.HORIZONTAL)
        v_scroll = tk.Scrollbar(image_frame, orient=tk.VERTICAL)
        self.preview_canvas = tk.Canvas(image_frame, bg=C["surface"],
                                        xscrollcommand=h_scroll.set,
                                        yscrollcommand=v_scroll.set,
                                        highlightthickness=0)
        h_scroll.config(command=self.preview_canvas.xview)
        v_scroll.config(command=self.preview_canvas.yview)

        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)

        self.preview_image_label = tk.Label(self.preview_canvas, bg=C["surface"])
        self.preview_canvas.create_window(0, 0, window=self.preview_image_label, anchor="nw")

    def _build_files_tab(self, parent):
        filter_frame = tk.Frame(parent, bg=C["surface"])
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(filter_frame, text="Show:", font=("Segoe UI", 8),
                fg=C["text_muted"], bg=C["surface"]).pack(side=tk.LEFT, padx=(0, 5))

        for text, value in [("All", "all"), ("JSON", "json"), ("Images", "images")]:
            tk.Radiobutton(filter_frame, text=text, variable=self.file_filter_var,
                          value=value, command=self._refresh_file_list,
                          bg=C["surface"], fg=C["text"], selectcolor=C["surface_light"],
                          activebackground=C["surface"]).pack(side=tk.LEFT, padx=5)

        list_frame = tk.Frame(parent, bg=C["surface"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.file_listbox = tk.Listbox(list_frame, font=("Consolas", 9),
                                       bg=C["surface_light"], fg=C["text"],
                                       selectbackground=C["accent"], selectforeground="white",
                                       relief=tk.FLAT, bd=0, selectmode=tk.EXTENDED)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_select)

        btn_frame = tk.Frame(parent, bg=C["surface"])
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        buttons = [
            ("⬇ Import", self._import_selected, C["accent"]),
            ("⬇ All", self._import_all, C["accent"]),
            ("🗑 Delete", self._delete_selected, C["danger"]),
            ("📂 Folder", self._open_folder, C["surface_light"]),
            ("🔄 Refresh", self._refresh_file_list, C["surface_light"])
        ]

        for text, cmd, color in buttons:
            btn = tk.Button(btn_frame, text=text, command=cmd,
                           bg=color, fg="white" if color != C["surface_light"] else C["text"],
                           font=("Segoe UI", 8), relief=tk.FLAT,
                           padx=8, pady=4, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2)

    def _create_section(self, parent, title):
        frame = tk.Frame(parent, bg=C["surface"])
        frame.pack(fill=tk.X, padx=10, pady=(10, 2))
        tk.Label(frame, text=title, font=("Segoe UI", 8, "bold"),
                fg=C["accent"], bg=C["surface"]).pack(anchor=tk.W)
        separator = tk.Frame(parent, bg=C["border"], height=1)
        separator.pack(fill=tk.X, padx=10)

    # ============================================================================
    # Signaling Server
    # ============================================================================
    def _start_signaling_server(self):
        """Start a simple HTTP server for WebRTC signaling"""
        try:
            # Create a custom handler that has access to this plugin instance
            handler = lambda *args, **kwargs: SignalingHandler(*args, plugin=self, **kwargs)
            self.signaling_server = socketserver.TCPServer(("", self.signaling_port), handler)
            self.signaling_thread = threading.Thread(target=self.signaling_server.serve_forever, daemon=True)
            self.signaling_thread.start()
            self._log(f"Signaling server started on port {self.signaling_port}", "ok")
        except Exception as e:
            self._log(f"Failed to start signaling server: {e}", "err")

    def _stop_signaling_server(self):
        if self.signaling_server:
            self.signaling_server.shutdown()
            self.signaling_server.server_close()
            self.signaling_server = None

    def handle_signaling_offer(self, peer_id, offer):
        """Handle incoming WebRTC offer and return answer"""
        # This will be called when the mobile sends an offer
        # We need to create an answer using aiortc
        if not self.pc:
            # Create peer connection if it doesn't exist
            self.pc = RTCPeerConnection()
            self.data_channel = None

            @self.pc.on("datachannel")
            def on_datachannel(channel):
                self.data_channel = channel
                @channel.on("message")
                def on_message(message):
                    asyncio.run_coroutine_threadsafe(self._handle_rpc(message), self.loop)
                self.app.root.after(0, self._on_connection)

        # Set remote description from offer
        rd = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])

        # Create a future to wait for the answer
        future = asyncio.run_coroutine_threadsafe(
            self._create_answer(rd), self.loop
        )
        answer = future.result(timeout=10)

        return {"type": answer.type, "sdp": answer.sdp}

    async def _create_answer(self, offer):
        """Create WebRTC answer from offer"""
        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        return answer

    # ============================================================================
    # HTTP Server (serves embedded HTML)
    # ============================================================================
    def _start_http_server(self):
        if not self.local_server_var.get():
            return

        port = self.local_port_var.get()
        try:
            # Create temporary HTML file
            self.temp_html_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            self.temp_html_file.write(EMBEDDED_HTML)
            self.temp_html_file.close()
            html_path = self.temp_html_file.name
            html_filename = os.path.basename(html_path)

            # Custom handler that properly serves HTML
            class Handler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    self.html_filename = html_filename
                    super().__init__(*args, **kwargs)

                def do_GET(self):
                    if self.path == '/':
                        self.send_response(302)
                        self.send_header('Location', f'/{self.html_filename}')
                        self.end_headers()
                        return

                    if self.path == f'/{self.html_filename}':
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html; charset=utf-8')
                        self.end_headers()

                        with open(self.html_filename, 'rb') as f:
                            self.wfile.write(f.read())
                        return

                    return super().do_GET()

                def log_message(self, format, *args):
                    pass

            os.chdir(os.path.dirname(html_path))

            self.http_server = socketserver.TCPServer(("", port), Handler)
            self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
            self.http_thread.start()

            ip = self._get_local_ip()
            self.local_url = f"http://{ip}:{port}"
            self._log(f"HTML server running at {self.local_url}", "ok")
            self._update_qr()

        except Exception as e:
            self._log(f"Failed to start HTTP server: {e}", "err")
            self.local_url = None

    def _stop_http_server(self):
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            self.http_server = None
        if self.temp_html_file:
            try:
                os.unlink(self.temp_html_file.name)
            except:
                pass

    # ============================================================================
    # WebRTC Core
    # ============================================================================
    async def _webrtc_task(self):
        """Asyncio task that sets up WebRTC peer connection"""
        self.peer_id = str(uuid.uuid4())[:8]
        self.app.root.after(0, self._on_peer_created)

        # Create RTCPeerConnection (will be used when mobile connects)
        self.pc = RTCPeerConnection()

        # We'll wait for the mobile to initiate connection via signaling
        while self.running:
            await asyncio.sleep(1)

    def _start_webrtc(self):
        if not self.dependencies_met:
            messagebox.showerror("Missing", f"Install: {', '.join(self.missing_deps)}")
            return

        # Start servers
        self._start_http_server()
        self._start_signaling_server()

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_async, daemon=True)
        self.thread.start()
        self._log("Starting WebRTC server…", "info")

    def _run_async(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._webrtc_task())

    def _on_peer_created(self):
        self.peer_id_lbl.config(text=self.peer_id, fg=C["accent"])
        self._update_qr()
        self._set_connection_status("waiting")
        self._log(f"Peer ID: {self.peer_id}", "ok")

    def _on_connection(self):
        self._set_connection_status("connected")
        self._log("Mobile connected!", "ok")

    def _stop_webrtc(self):
        if self.pc:
            asyncio.run_coroutine_threadsafe(self.pc.close(), self.loop)

        self.running = False
        self.pc = None
        self.data_channel = None
        self.peer_id = None

        self._stop_http_server()
        self._stop_signaling_server()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.peer_id_lbl.config(text="—", fg=C["text_muted"])
        self.qr_label.config(image="", text="Start server\nto generate QR code")
        self._set_connection_status("disconnected")
        self._log("Server stopped.", "warn")

    def _set_connection_status(self, status):
        colors = {
            "disconnected": C["danger"],
            "waiting": C["warning"],
            "connected": C["accent"]
        }
        texts = {
            "disconnected": "Disconnected",
            "waiting": "Waiting for connection",
            "connected": "Connected"
        }
        if self.conn_dot:
            self.conn_dot.delete("all")
            self.conn_dot.create_oval(2, 2, 10, 10, fill=colors.get(status, C["danger"]), outline="")
        for widget in self.conn_dot.master.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(text=texts.get(status, "Disconnected"))

    def _update_qr(self):
        if not self.peer_id:
            return

        if self.local_server_var.get() and self.local_url:
            base = self.local_url
        else:
            base = self.public_url_var.get().rstrip('/')

        url = f"{base}#{self.peer_id}"
        self._generate_qr(url)

    def _generate_qr(self, url):
        if not HAS_QR:
            self.qr_label.config(text="QR module not installed\npip install qrcode[pil] pillow")
            return

        try:
            qr = qrcode.QRCode(box_size=4, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color=C["accent"], back_color=C["surface_light"])
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            self.qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.qr_image, text="")
        except Exception as e:
            self.qr_label.config(text=f"QR failed: {str(e)[:30]}")

    # ============================================================================
    # RPC Handlers
    # ============================================================================
    async def _handle_rpc(self, data):
        try:
            req = json.loads(data)
            method = req.get("method")
            params = req.get("params", {})
            req_id = req.get("id")
        except Exception as e:
            self._log(f"Invalid RPC: {e}", "err")
            return

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._dispatch_rpc, method, params)

        if req_id is not None and self.data_channel and self.data_channel.readyState == "open":
            response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            self.data_channel.send(json.dumps(response))

    def _dispatch_rpc(self, method, params):
        try:
            if method.endswith('_post'):
                path = params.get('path', '')
                body = params.get('body', {})
                return self._handle_rest_post(path, body)
            elif method.endswith('_put'):
                path = params.get('path', '')
                body = params.get('body', {})
                return self._handle_rest_put(path, body)
            elif method.endswith('_delete'):
                path = params.get('path', '')
                return self._handle_rest_delete(path)
            elif method == 'list_samples':
                return self._rpc_list_samples(
                    params.get('page', 0),
                    params.get('size', 50),
                    params.get('search', '')
                )
            elif method == 'list_schemes':
                return self._rpc_list_schemes()
            elif method == 'upload_image':
                return self._rpc_upload_image(params)
            elif method == 'get_status':
                return self._rpc_get_status()
            else:
                path = params.get('path', '')
                if path:
                    return self._handle_rest_get(path)
                return {"error": f"Unknown method: {method}"}
        except Exception as e:
            self._log(f"RPC error {method}: {e}", "err")
            return {"error": str(e)}

    def _handle_rest_get(self, path):
        if path == '/ping':
            return {"status": "ok", "server": "ScientificToolkit MobileSync v8.1"}
        elif path == '/api/status':
            return self._rpc_get_status()
        elif path.startswith('/api/samples/export/csv'):
            return self._rpc_export_csv()
        elif path.startswith('/api/samples/'):
            sample_id = path.split('/')[-1]
            return self._rpc_get_sample(sample_id)
        elif path == '/api/samples':
            return self._rpc_list_samples(0, 50, '')
        elif path == '/api/columns':
            return self._rpc_get_columns()
        elif path == '/api/classify/schemes':
            return self._rpc_list_schemes()
        elif path.startswith('/api/classify/schemes/'):
            scheme_id = path.split('/')[-1]
            return self._rpc_scheme_info(scheme_id)
        else:
            return {"error": f"Unknown path: {path}"}

    def _handle_rest_post(self, path, body):
        if path == '/api/samples':
            samples = body if isinstance(body, list) else [body]
            return self._rpc_add_samples(samples)
        elif path == '/api/classify/sample':
            scheme_id = body.pop('scheme_id', None)
            return self._rpc_classify_sample(body, scheme_id)
        elif path.startswith('/api/classify/apply/'):
            scheme_id = path.split('/')[-1]
            return self._rpc_apply_scheme_all(scheme_id)
        else:
            return {"error": f"Unknown POST path: {path}"}

    def _handle_rest_put(self, path, body):
        if path.startswith('/api/samples/'):
            sample_id = path.split('/')[-1]
            return self._rpc_update_sample(sample_id, body)
        return {"error": f"Unknown PUT path: {path}"}

    def _handle_rest_delete(self, path):
        if path.startswith('/api/samples/'):
            sample_id = path.split('/')[-1]
            return self._rpc_delete_sample(sample_id)
        return {"error": f"Unknown DELETE path: {path}"}

    # RPC Implementation methods
    def _rpc_get_status(self):
        dh = self._data_hub
        ce = self._cls_engine
        return {
            "rows": len(dh.get_all()) if dh else 0,
            "columns": self._columns(),
            "engine": getattr(self.app, "current_engine_name", None),
            "classification_schemes": (
                [s["id"] for s in ce.get_available_schemes()] if ce else []),
            "timestamp": datetime.now().isoformat()
        }

    def _rpc_list_samples(self, page, size, search):
        samples = self._get_samples()
        if search:
            search = search.lower()
            samples = [s for s in samples if any(search in str(v).lower() for v in s.values())]
        total = len(samples)
        start = page * size
        chunk = samples[start:start + size]
        return {
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "samples": chunk
        }

    def _rpc_get_sample(self, sample_id):
        idx, s = self._get_sample_by_id(sample_id)
        if s is None:
            return {"error": "Not found"}
        return s

    def _rpc_add_samples(self, samples):
        if not samples:
            return {"error": "No samples"}
        rows = samples if isinstance(samples, list) else [samples]
        ts = datetime.now().isoformat()
        for r in rows:
            r.setdefault("_source", "mobile_p2p")
            r.setdefault("_synced", ts)

        fn = self.json_dir / f"p2p_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fn, "w") as f:
            json.dump(rows, f, indent=2)

        self.app.root.after(0, lambda: self._add_samples(rows))
        self.update_queue.put({"type": "new_file"})
        return {"status": "accepted", "count": len(rows), "ids": [r.get("Sample_ID") for r in rows]}

    def _rpc_update_sample(self, sample_id, updates):
        idx, existing = self._get_sample_by_id(sample_id)
        if existing is None:
            return {"error": "Not found"}
        updates["_updated_via"] = "mobile_p2p"
        updates["_updated_at"] = datetime.now().isoformat()
        dh = self._data_hub
        if dh:
            self.app.root.after(0, lambda: dh.update_row(idx, updates))
        return {"status": "updated", "Sample_ID": sample_id}

    def _rpc_delete_sample(self, sample_id):
        idx, existing = self._get_sample_by_id(sample_id)
        if existing is None:
            return {"error": "Not found"}
        dh = self._data_hub
        if dh:
            self.app.root.after(0, lambda: dh.delete_rows([idx]))
        return {"status": "deleted", "Sample_ID": sample_id}

    def _rpc_export_csv(self):
        samples = self._get_samples()
        if not samples:
            return {"error": "No samples"}
        cols = self._columns()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(samples)
        return {"csv": output.getvalue(), "filename": f"samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}

    def _rpc_get_columns(self):
        return {"columns": self._columns(), "count": len(self._columns())}

    def _rpc_list_schemes(self):
        ce = self._cls_engine
        if not ce:
            return {"error": "Engine not loaded"}
        return ce.get_available_schemes()

    def _rpc_scheme_info(self, scheme_id):
        ce = self._cls_engine
        if not ce:
            return {"error": "Engine not loaded"}
        info = ce.get_scheme_info(scheme_id)
        if not info:
            return {"error": "Scheme not found"}
        return info

    def _rpc_classify_sample(self, sample, scheme_id):
        ce = self._cls_engine
        if not ce:
            return {"error": "Engine not loaded"}
        classification, confidence, color = ce.classify_sample(sample, scheme_id)
        return {
            "Sample_ID": sample.get("Sample_ID"),
            "scheme_id": scheme_id,
            "classification": classification,
            "confidence": confidence,
            "color": color
        }

    def _rpc_apply_scheme_all(self, scheme_id):
        ce = self._cls_engine
        dh = self._data_hub
        if not ce:
            return {"error": "Engine not loaded"}
        if not dh:
            return {"error": "DataHub not available"}
        samples = dh.get_all()
        if not samples:
            return {"error": "No samples loaded"}
        ce.classify_all_samples(samples, scheme_id)
        def _notify():
            dh._rebuild_columns()
            dh.mark_unsaved()
            dh._notify("samples_updated")
        self.app.root.after(0, _notify)
        return {"status": "classified", "scheme_id": scheme_id, "count": len(samples)}

    def _rpc_upload_image(self, params):
        filename = params.get("filename", "image.jpg")
        data_b64 = params.get("data")
        sample_id = params.get("sample_id", "unknown")
        if not data_b64:
            return {"error": "No image data"}
        try:
            img_data = base64.b64decode(data_b64)
            safe = "".join(c for c in sample_id if c.isalnum() or c in ("-", "_")).rstrip()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = Path(filename).suffix
            if not ext:
                ext = ".jpg"
            new_filename = f"{safe}_{ts}{ext}"
            filepath = self.image_dir / new_filename
            with open(filepath, "wb") as f:
                f.write(img_data)
            meta = {"sample_id": sample_id, "filename": new_filename,
                    "timestamp": ts, "_source": "mobile_p2p"}
            with open(self.json_dir / f"{safe}_{ts}_meta.json", "w") as f:
                json.dump(meta, f, indent=2)
            self.update_queue.put({"type": "new_file"})
            return {"status": "accepted", "filename": new_filename}
        except Exception as e:
            return {"error": str(e)}

    # ============================================================================
    # File Management
    # ============================================================================
    def _refresh_file_list(self):
        if not self.file_listbox:
            return
        self.file_listbox.delete(0, tk.END)
        self.file_listbox.file_paths = []

        ft = self.file_filter_var.get()
        files = []

        if ft in ("all", "json"):
            files += sorted(self.json_dir.glob("*.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
        if ft in ("all", "images"):
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"]:
                files += sorted(self.image_dir.glob(ext),
                               key=lambda p: p.stat().st_mtime, reverse=True)

        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for f in files:
            icon = "🖼️" if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"] else "📄"
            size = f.stat().st_size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024/1024:.1f}MB"

            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M")
            self.file_listbox.insert(tk.END, f" {icon} {f.name:<40} {size_str:>8} {mtime}")
            self.file_listbox.file_paths.append(f)

    def _get_selected_paths(self):
        sel = self.file_listbox.curselection()
        paths = getattr(self.file_listbox, "file_paths", [])
        return [paths[i] for i in sel if i < len(paths)]

    def _on_file_select(self, event):
        sel = self._get_selected_paths()
        if not sel:
            self.preview_text.delete(1.0, tk.END)
            self.preview_image_label.config(image="")
            return
        fp = sel[0]
        if fp.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            self._preview_image(fp)
        else:
            self._preview_text(fp)

    def _preview_text(self, fp):
        if self.preview_notebook:
            self.preview_notebook.select(0)
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                if fp.suffix == '.json':
                    data = json.load(f)
                    content = json.dumps(data, indent=2)
                else:
                    content = f.read()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
        except Exception as e:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Error loading preview: {e}")

    def _preview_image(self, fp):
        if self.preview_notebook:
            self.preview_notebook.select(1)
        try:
            img = Image.open(fp)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            self.current_preview_image = ImageTk.PhotoImage(img)
            self.preview_image_label.config(image=self.current_preview_image)
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        except Exception as e:
            self._log(f"Preview error: {e}", "err")

    def _import_selected(self):
        for fp in self._get_selected_paths():
            self._import_sample_file(fp)
        self._refresh_file_list()

    def _import_all(self):
        for fp in getattr(self.file_listbox, "file_paths", []):
            self._import_sample_file(fp)
        self._refresh_file_list()

    def _import_sample_file(self, fp):
        try:
            if fp.suffix.lower() == '.json':
                with open(fp, 'r') as f:
                    data = json.load(f)
                rows = data if isinstance(data, list) else [data]
                self._add_samples(rows)
                self._log(f"Imported {fp.name} ({len(rows)} rows)", "ok")
            elif fp.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                self._add_samples([{
                    "Sample_ID": fp.stem,
                    "Image_File": str(fp),
                    "Image_Size": fp.stat().st_size,
                }])
                self._log(f"Imported image ref: {fp.name}", "ok")
        except Exception as e:
            self._log(f"Import failed: {fp.name} - {e}", "err")

    def _delete_selected(self):
        paths = self._get_selected_paths()
        if not paths:
            return
        if messagebox.askyesno("Delete", f"Delete {len(paths)} file(s)?"):
            for fp in paths:
                try:
                    fp.unlink()
                    self._log(f"Deleted: {fp.name}", "warn")
                except Exception as e:
                    self._log(f"Delete error: {e}", "err")
            self._refresh_file_list()

    def _open_folder(self):
        path = str(self.sync_dir)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["open", path])
        else:
            import subprocess
            subprocess.run(["xdg-open", path])

    def _start_watchdog(self):
        handler = SyncFileHandler(self._on_file_created)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.sync_dir), recursive=True)
        self.observer.start()

    def _on_file_created(self, filepath):
        self.app.root.after(0, self._refresh_file_list)
        self._log(f"File received: {Path(filepath).name}", "ok")

    # ============================================================================
    # Utilities
    # ============================================================================
    def _process_queue(self):
        if not self._active:
            return
        try:
            while True:
                msg = self.update_queue.get_nowait()
                if msg.get("type") == "log":
                    self._log(msg.get("message", ""), msg.get("level", "info"))
                elif msg.get("type") == "new_file":
                    self._refresh_file_list()
                    self._refresh_toolkit_status()
        except Empty:
            pass
        finally:
            self.app.root.after(150, self._process_queue)

    def _log(self, message, level="info"):
        if not self.log_text:
            return
        icons = {"ok": "✅", "err": "❌", "info": "ℹ️", "warn": "⚠️"}
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {icons.get(level, '•')} {message}\n", level)
        self.log_text.see(tk.END)

    def _copy_text(self, text):
        if text and self.parent:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            self._log("Copied to clipboard", "info")

    def _copy_current_url(self):
        if not self.peer_id:
            return
        if self.local_server_var.get() and self.local_url:
            base = self.local_url
        else:
            base = self.public_url_var.get().rstrip('/')
        url = f"{base}#{self.peer_id}"
        self._copy_text(url)

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except:
            return "127.0.0.1"
        finally:
            s.close()

    def _refresh_toolkit_status(self):
        if not self.toolkit_status_lbl:
            return
        dh = self._data_hub
        ce = self._cls_engine
        rows = len(dh.get_all()) if dh else 0
        cols = len(self._columns())
        engine = getattr(self.app, "current_engine_name", "—")
        schemes = len(ce.schemes) if ce else 0
        self.toolkit_status_lbl.config(
            text=f"📊 Samples: {rows}\n"
                 f"📋 Columns: {cols}\n"
                 f"🔬 Engine: {engine}\n"
                 f"📐 Schemes: {schemes}"
        )

# ============================================================================
# Plugin Registration
# ============================================================================
def register_plugin(main_app):
    _ATTR = "_mobile_sync_tab_instance"
    existing = getattr(main_app, _ATTR, None)
    if existing is not None:
        try:
            existing._refresh_toolkit_status()
            print("🔄 Mobile Sync tab: refreshed on existing instance")
        except Exception as e:
            print(f"⚠️ Mobile Sync tab refresh failed: {e}")
        return None

    plugin = MobileSyncTabPlugin(main_app)
    if hasattr(main_app.center, "add_tab_plugin"):
        main_app.center.add_tab_plugin(
            plugin_id="mobile_sync_tab",
            plugin_name="Mobile Sync (Direct WebRTC)",
            plugin_icon="📡",
            plugin_instance=plugin
        )
        setattr(main_app, _ATTR, plugin)
        print("✅ Mobile Sync Direct WebRTC v8.1 registered")
    else:
        print("⚠️ CenterPanel does not have add_tab_plugin")
    return None
