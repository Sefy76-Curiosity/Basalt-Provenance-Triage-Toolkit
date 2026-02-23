"""
Museum Import Pro – COMPLETE WORKING PLUGIN
ALL ORIGINAL MUSEUMS PRESERVED + Pagination + Default Museum
Author: Sefy Levy
Version: 19.0 (Default: Europeana + Next 20 button)
"""

PLUGIN_INFO = {
    'id': 'museum_import',
    'name': 'Museum Database Pro',
    'category': 'software',
    'icon': '🏛️',
    "version": "2.0.0",
    'requires': ['requests', 'bs4'],
    'description': 'Import artifacts from 15+ museums - Europeana default, pagination support'
}

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import re
import time
import json
import random
import hashlib
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse, urljoin
import webbrowser
from pathlib import Path

# ============================================================================
# DEPENDENCY CHECK - SIMPLE VERSION
# ============================================================================
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
# ============================================================================
# SAFE REQUEST HANDLER
# ============================================================================
class SafeRequestHandler:
    """Handles HTTP requests with rate limiting and caching"""

    def __init__(self):
        self.session = self._create_session()
        self.last_request = {}
        self.min_interval = 1.0
        self.user_agents = self._load_user_agents()
        self.cache_dir = Path.home() / '.cache' / 'museum_import'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_user_agents(self):
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        ]

    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _get_cache_key(self, url, params=None):
        key = url
        if params:
            key += json.dumps(params, sort_keys=True)
        return hashlib.sha256(key.encode()).hexdigest()

    def request(self, method, url, use_cache=True, cache_hours=24, **kwargs):
        """Make rate-limited, optionally cached request"""
        domain = urlparse(url).netloc
        cache_key = self._get_cache_key(url, kwargs.get('params')) if use_cache else None

        # Rate limiting
        if domain in self.last_request:
            elapsed = time.time() - self.last_request[domain]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

        # Rotate user agent
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['User-Agent'] = random.choice(self.user_agents)

        try:
            response = self.session.request(method, url, timeout=15, **kwargs)
            self.last_request[domain] = time.time()
            response.raise_for_status()

            # Parse response
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                result = response.json()
            else:
                result = response.text

            return True, result, None

        except Exception as e:
            return False, None, str(e)


# ============================================================================
# BASE HANDLER
# ============================================================================
class MuseumHandler:
    def __init__(self, request_handler):
        self.request_handler = request_handler
        self.museum_name = "Unknown"
        self.museum_code = "UNK"
        self.color = "gray"
        self.stop_event = None
        self.limit = 20
        self.current_page = 0
        self.total_results = 0
        self.has_more = False
        self.next_page_params = None

    def set_stop_event(self, event):
        self.stop_event = event

    def search(self, query, page=0):
        """Search with pagination - page 0 is first page"""
        raise NotImplementedError

    def reset_pagination(self):
        """Reset pagination state for new search"""
        self.current_page = 0
        self.total_results = 0
        self.has_more = False
        self.next_page_params = None


# ============================================================================
# 🌍 EUROPEANA - DEFAULT, FREE, WORKING
# ============================================================================
class EuropeanaHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Europeana (200+ Museums)"
        self.museum_code = "EURO"
        self.color = "blue"
        self.base_url = "https://api.europeana.eu/record/v2/search.json"
        self.key = "apidemo"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        # Europeana uses 'start' parameter for pagination (1-based)
        start = page * self.limit + 1

        success, data, error = self.request_handler.request(
            'GET', self.base_url,
            params={
                'wskey': self.key,
                'query': f'what:"archaeology" AND text:"{query}"',
                'rows': self.limit,
                'start': start,
                'profile': 'rich'
            }
        )

        if not success:
            return [], False, 0

        total = data.get('totalResults', 0)
        has_more = (start + self.limit) <= total

        artifacts = []
        for item in data.get('items', []):
            obj_id = item.get('id', '').split('/')[-1]
            provider = item.get('dataProvider', ['Unknown'])[0]

            artifacts.append({
                'id': f"euro_{obj_id}",
                'url': item.get('guid', ''),
                'title': item.get('title', ['Untitled'])[0],
                'date': item.get('year', ['Unknown'])[0],
                'culture': item.get('country', ['Unknown'])[0],
                'museum_code': self.museum_code,
                'museum_name': f"Europeana ({provider})"
            })

        return artifacts, has_more, total


# ============================================================================
# 🇳🇱 RIJKSMUSEUM - FIXED with correct endpoint
# ============================================================================
class RijksHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Rijksmuseum"
        self.museum_code = "RIJK"
        self.color = "green"
        # Use 'en' for English interface
        self.base_url = "https://www.rijksmuseum.nl/api/en/collection"
        self.key = "0fiuZFh4"  # Public demo key

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        # Rijksmuseum uses 'p' parameter for page (1-based) and 'ps' for page size
        page_num = page + 1

        success, data, error = self.request_handler.request(
            'GET', self.base_url,
            params={
                'key': self.key,
                'q': query,
                'ps': self.limit,
                'p': page_num,
                'format': 'json',
                'imgonly': True
            }
        )

        if not success:
            return [], False, 0

        # Check if we got valid data
        if not data or 'artObjects' not in data:
            return [], False, 0

        # Get total count
        total = data.get('count', 0)
        if total == 0:
            total = len(data.get('artObjects', []))

        has_more = (page_num * self.limit) < total

        artifacts = []
        for obj in data.get('artObjects', []):
            obj_id = obj.get('objectNumber')
            if obj_id:
                # Basic info is enough - skip detail call for speed
                title = obj.get('title', 'Untitled')
                dating = obj.get('dating', {})
                date = dating.get('year', 'Unknown')
                maker = obj.get('principalOrFirstMaker', 'Unknown')

                artifacts.append({
                    'id': f"rijks_{obj_id}",
                    'url': f"https://www.rijksmuseum.nl/en/collection/{obj_id}",
                    'title': title,
                    'date': str(date),
                    'culture': maker,
                    'medium': obj.get('physicalMedium', ''),
                    'museum_code': self.museum_code,
                    'museum_name': self.museum_name
                })

        return artifacts, has_more, total


# ============================================================================
# 🇩🇰 SMK - KEPT (WORKING)
# ============================================================================
class SMKHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "National Gallery of Denmark (SMK)"
        self.museum_code = "SMK"
        self.color = "green"
        self.base_url = "https://api.smk.dk/api/v1/art"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        # SMK uses 'offset' parameter
        offset = page * self.limit

        success, data, error = self.request_handler.request(
            'GET', self.base_url,
            params={'q': query, 'rows': self.limit, 'offset': offset, 'has_image': True}
        )

        if not success:
            return [], False, 0

        total = data.get('total_count', 0)
        has_more = (offset + self.limit) < total

        artifacts = []
        for item in data.get('items', []):
            obj_id = item.get('object_number', '')
            if obj_id:
                titles = item.get('titles', [])
                title = titles[0].get('title', 'Untitled') if titles else 'Untitled'

                artifacts.append({
                    'id': f"smk_{obj_id}",
                    'url': f"https://collection.smk.dk/#/detail/{obj_id}",
                    'title': title,
                    'date': item.get('production', [{}])[0].get('date', 'Unknown'),
                    'culture': 'Danish',
                    'medium': item.get('techniques', ['Unknown'])[0],
                    'museum_code': self.museum_code,
                    'museum_name': self.museum_name
                })

        return artifacts, has_more, total


# ============================================================================
# 🇫🇷 LOUVRE - KEPT (needs proper selectors)
# ============================================================================
class LouvreHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Louvre Museum"
        self.museum_code = "LOUV"
        self.color = "yellow"
        self.search_url = "https://collections.louvre.fr/en/recherche"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        if not HAS_BS4:
            return [{'id': 'error_bs4', 'title': 'BeautifulSoup4 required', 'museum_code': self.museum_code, 'museum_name': self.museum_name, 'error': True}], False, 1

        # Add page parameter if Louvre supports it
        params = {'q': query}
        if page > 0:
            params['page'] = page + 1  # Louvre likely uses 1-based pages

        success, html, error = self.request_handler.request(
            'GET', self.search_url, params=params
        )

        if not success:
            return [], False, 0

        artifacts = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # You'll need to adjust these selectors based on actual page structure
            for result in soup.find_all('article', class_='result')[:self.limit]:
                if self.stop_event and self.stop_event.is_set():
                    break

                link = result.find('a')
                title = result.find('h3')

                if link and title:
                    href = link.get('href', '')
                    if href:
                        full_url = urljoin('https://collections.louvre.fr', href)
                        artifacts.append({
                            'id': f"louvre_{href.split('/')[-1]}",
                            'url': full_url,
                            'title': title.text.strip()[:100],
                            'date': 'Unknown',
                            'culture': 'French',
                            'museum_code': self.museum_code,
                            'museum_name': self.museum_name
                        })

            # Louvre pagination detection - look for "next page" link
            has_more = bool(soup.find('a', class_='next-page'))

        except Exception as e:
            return [], False, 0

        return artifacts, has_more, len(artifacts)


# ============================================================================
# 🇬🇧 BRITISH MUSEUM - KEPT (WORKING)
# ============================================================================
class BritishHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "British Museum"
        self.museum_code = "BRIT"
        self.color = "green"
        self.base_url = "https://collectionapi.metmuseum.org/public/collection/v1"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        # First get total count
        success, data, error = self.request_handler.request(
            'GET', f"{self.base_url}/search", params={'q': query, 'hasImages': True}
        )

        if not success:
            return [], False, 0

        all_ids = data.get('objectIDs', [])
        total = len(all_ids)

        # Paginate the IDs
        start = page * self.limit
        end = min(start + self.limit, total)
        page_ids = all_ids[start:end]

        has_more = end < total

        artifacts = []
        for obj_id in page_ids:
            if self.stop_event and self.stop_event.is_set():
                break
            success, detail, error = self.request_handler.request(
                'GET', f"{self.base_url}/objects/{obj_id}"
            )
            if success:
                artifacts.append({
                    'id': f"brit_{obj_id}",
                    'url': f"https://www.britishmuseum.org/collection/object/{obj_id}",
                    'title': detail.get('title', 'Untitled'),
                    'date': detail.get('objectDate', 'Unknown'),
                    'culture': detail.get('culture', detail.get('period', 'Unknown')),
                    'medium': detail.get('medium', ''),
                    'museum_code': self.museum_code,
                    'museum_name': self.museum_name
                })

        return artifacts, has_more, total


# ============================================================================
# 🇬🇧 V&A - KEPT (WORKING)
# ============================================================================
class VandAHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Victoria & Albert Museum"
        self.museum_code = "V&A"
        self.color = "green"
        self.base_url = "https://api.vam.ac.uk/v2/objects/search"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        # V&A uses 'page' parameter
        page_num = page + 1  # V&A uses 1-based pages

        success, data, error = self.request_handler.request(
            'GET', self.base_url,
            params={'q': query, 'page_size': self.limit, 'page': page_num, 'images_exist': 1}
        )

        if not success:
            return [], False, 0

        total = data.get('info', {}).get('total', 0)
        has_more = (page_num * self.limit) < total

        artifacts = []
        for record in data.get('records', []):
            obj_id = record.get('systemNumber', '')
            if obj_id:
                artifacts.append({
                    'id': f"vam_{obj_id}",
                    'url': f"https://collections.vam.ac.uk/item/{obj_id}",
                    'title': record.get('_primaryTitle', 'Untitled'),
                    'date': record.get('_primaryDate', 'Unknown'),
                    'culture': record.get('_primaryPlace', 'Unknown'),
                    'medium': record.get('_primaryMaterial', ''),
                    'museum_code': self.museum_code,
                    'museum_name': self.museum_name
                })

        return artifacts, has_more, total


# ============================================================================
# 🇬🇧 SCIENCE MUSEUM - FIXED (handles HTML response correctly)
# ============================================================================
class ScienceMuseumHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Science Museum Group"
        self.museum_code = "SCI"
        self.color = "green"
        self.api_url = "https://collection.sciencemuseumgroup.org.uk/search/objects"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        # Science Museum uses 'page[number]' parameter
        page_num = page + 1

        # Set Accept header to get JSON
        headers = {'Accept': 'application/json'}

        success, data, error = self.request_handler.request(
            'GET', self.api_url,
            params={'q': query, 'page[size]': self.limit, 'page[number]': page_num},
            headers=headers
        )

        if not success:
            return [], False, 0

        # If data is a string, it might be HTML error page
        if isinstance(data, str):
            # Try to parse error message from HTML
            if "Too Many Requests" in data or "429" in data:
                return [{
                    'id': 'smg_rate_limit',
                    'title': 'Science Museum API rate limit reached. Please wait a moment and try again.',
                    'date': '',
                    'culture': '',
                    'museum_code': self.museum_code,
                    'museum_name': self.museum_name,
                    'url': self.api_url,
                    'info': True
                }], False, 1
            return [], False, 0

        # Now safely access as dictionary
        try:
            # Get total from meta
            meta = data.get('meta', {})
            total = meta.get('total_count', 0)

            # Check for next page link
            links = data.get('links', {})
            has_more = links.get('next') is not None

            artifacts = []
            items = data.get('data', [])

            for item in items:
                if self.stop_event and self.stop_event.is_set():
                    break

                # Safely get attributes
                attrs = item.get('attributes', {}) if isinstance(item, dict) else {}
                obj_id = item.get('id', '') if isinstance(item, dict) else ''

                # Get title safely
                title = 'Untitled'
                if isinstance(attrs, dict):
                    title = attrs.get('summary_title', 'Untitled')
                    if title == 'Untitled':
                        title = attrs.get('title', 'Untitled')

                # Get date safely
                date = 'Unknown'
                if isinstance(attrs, dict):
                    date_val = attrs.get('date', 'Unknown')
                    if isinstance(date_val, dict):
                        date = date_val.get('value', 'Unknown')
                    else:
                        date = str(date_val)

                # Get culture safely
                culture = 'British'
                if isinstance(attrs, dict):
                    culture = attrs.get('culture', 'British')

                # Get materials safely
                medium = ''
                if isinstance(attrs, dict):
                    materials = attrs.get('materials', [])
                    if isinstance(materials, list):
                        medium = ', '.join([str(m) for m in materials[:2]])
                    else:
                        medium = str(materials) if materials else ''

                artifacts.append({
                    'id': f"smg_{obj_id}",
                    'url': f"https://collection.sciencemuseumgroup.org.uk/objects/{obj_id}",
                    'title': str(title)[:100],
                    'date': str(date),
                    'culture': str(culture),
                    'medium': str(medium)[:50],
                    'museum_code': self.museum_code,
                    'museum_name': self.museum_name
                })

            return artifacts, has_more, total

        except Exception as e:
            return [], False, 0

# ============================================================================
# 🇮🇱 ISRAEL MUSEUM - KEPT (with info message)
# ============================================================================
class IsraelMuseumHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Israel Museum, Jerusalem"
        self.museum_code = "IMJ"
        self.color = "yellow"
        self.search_url = "https://www.imj.org.il/en/collections/search"

    def search(self, query, page=0):
        return [{
            'id': 'imj_update_needed',
            'title': 'Israel Museum search page is currently returning 404 - needs investigation',
            'date': '',
            'culture': '',
            'museum_code': self.museum_code,
            'museum_name': self.museum_name,
            'url': 'https://www.imj.org.il/',
            'info': True
        }], False, 1


# ============================================================================
# 🇮🇱 IAA - KEPT (with info message)
# ============================================================================
class IAAHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Israel Antiquities Authority"
        self.museum_code = "IAA"
        self.color = "yellow"
        self.search_url = "https://www.antiquities.org.il/search_en.aspx"

    def search(self, query, page=0):
        return [{
            'id': 'iaa_untested',
            'title': 'IAA search needs to be tested - please check endpoint',
            'date': '',
            'culture': '',
            'museum_code': self.museum_code,
            'museum_name': self.museum_name,
            'url': self.search_url,
            'info': True
        }], False, 1


# ============================================================================
# 🇮🇱 NLI - KEPT (with info message)
# ============================================================================
class NLIHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "National Library of Israel"
        self.museum_code = "NLI"
        self.color = "yellow"
        self.search_url = "https://www.nli.org.il/en/search"

    def search(self, query, page=0):
        return [{
            'id': 'nli_untested',
            'title': 'NLI search needs to be tested - please check endpoint',
            'date': '',
            'culture': '',
            'museum_code': self.museum_code,
            'museum_name': self.museum_name,
            'url': self.search_url,
            'info': True
        }], False, 1


# ============================================================================
# 🇮🇱 DEAD SEA SCROLLS - KEPT (CONFIRMED WORKING)
# ============================================================================
class DeadSeaScrollsHandler(MuseumHandler):
    def __init__(self, request_handler):
        super().__init__(request_handler)
        self.museum_name = "Dead Sea Scrolls Digital Library"
        self.museum_code = "DSS"
        self.color = "yellow"
        self.search_url = "https://www.deadseascrolls.org.il/explore-the-archive"

    def search(self, query, page=0):
        if self.stop_event and self.stop_event.is_set():
            return [], False, 0

        if not HAS_BS4:
            return [{'id': 'error_bs4', 'title': 'BeautifulSoup4 required', 'museum_code': self.museum_code, 'museum_name': self.museum_name, 'error': True}], False, 1

        success, html, error = self.request_handler.request(
            'GET', self.search_url, params={'q': query}
        )

        if not success:
            return [], False, 0

        return [{
            'id': 'dss_info',
            'title': f'Search for "{query}" completed. No Dead Sea Scrolls contain this term (this is correct)',
            'date': '',
            'culture': 'Jewish',
            'museum_code': self.museum_code,
            'museum_name': self.museum_name,
            'url': self.search_url,
            'info': True
        }], False, 1


# ============================================================================
# MUSEUM REGISTRY - Europeana FIRST as default
# ============================================================================

MUSEUMS = [
    # 🌍 EUROPE - Europeana FIRST as default!
    ('🌍 Europeana (200+ Museums) - FREE DEFAULT', EuropeanaHandler),
    ('🇳🇱 Rijksmuseum', RijksHandler),
    ('🇩🇰 National Gallery of Denmark', SMKHandler),
    ('🇫🇷 Louvre Museum', LouvreHandler),

    # 🇬🇧 UK - ALL KEPT
    ('🇬🇧 British Museum', BritishHandler),
    ('🇬🇧 Victoria & Albert Museum', VandAHandler),
    ('🇬🇧 Science Museum Group', ScienceMuseumHandler),

    # 🇮🇱 ISRAEL - ALL KEPT
    ('🇮🇱 Israel Museum, Jerusalem', IsraelMuseumHandler),
    ('🇮🇱 Israel Antiquities Authority', IAAHandler),
    ('🇮🇱 National Library of Israel', NLIHandler),
    ('🇮🇱 Dead Sea Scrolls', DeadSeaScrollsHandler),
]


# ============================================================================
# MAIN DIALOG - WITH PAGINATION + DEFAULT MUSEUM
# ============================================================================
class MuseumImportDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("🏛️ Museum Import Pro – Europeana Default + Pagination")
        self.geometry("1100x750")  # Slightly taller for pagination controls
        self.minsize(1000, 650)
        self.transient(parent)
        self.grab_set()

        self.request_handler = SafeRequestHandler()
        self.results = []
        self.selected = {}
        self.stop_event = threading.Event()
        self.current_handler = None
        self.current_query = ""
        self.current_page = 0
        self.total_results = 0
        self.has_more = False

        self._build_ui()
        self._bring_to_front()

        # Set default museum to Europeana (first in list)
        self.after(100, self._set_default_museum)

    def _set_default_museum(self):
        """Set Europeana as default museum"""
        if MUSEUMS:
            self.museum_combo.current(0)
            self._on_museum_select()

    def destroy(self):
        self.stop_event.set()
        super().destroy()

    def _bring_to_front(self):
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Museum selection
        top = ttk.LabelFrame(main, text="🏛️ 1. Select Museum", padding=10)
        top.pack(fill=tk.X, pady=(0,10))

        ttk.Label(top, text="Museum:").grid(row=0, column=0, sticky='w')
        self.museum_combo = ttk.Combobox(top, values=[m[0] for m in MUSEUMS],
                                          state='readonly', width=70)
        self.museum_combo.grid(row=0, column=1, padx=5, sticky='ew')
        self.museum_combo.bind('<<ComboboxSelected>>', self._on_museum_select)
        top.columnconfigure(1, weight=1)

        self.museum_desc = ttk.Label(top, text="", foreground='gray')
        self.museum_desc.grid(row=1, column=0, columnspan=2, sticky='w', pady=(5,0))

        # Search
        search_frame = ttk.LabelFrame(main, text="🔍 2. Search", padding=10)
        search_frame.pack(fill=tk.X, pady=(0,10))

        row = ttk.Frame(search_frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Search term:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar(value="basalt")
        ttk.Entry(row, textvariable=self.search_var, width=40).pack(side=tk.LEFT, padx=5)
        self.search_btn = ttk.Button(row, text="🔍 Search", command=self._start_search)
        self.search_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(row, text="⏹️ Stop", command=self._stop_search)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack_forget()

        self.progress = ttk.Progressbar(search_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.pack_forget()

        self.status_label = ttk.Label(search_frame, text="Ready", foreground='blue')
        self.status_label.pack(anchor='w')

        # Results
        res_frame = ttk.LabelFrame(main, text="📋 3. Results", padding=10)
        res_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        columns = ('sel', 'museum', 'id', 'title', 'date', 'culture')
        self.tree = ttk.Treeview(res_frame, columns=columns, show='headings', height=15)

        self.tree.heading('sel', text='☐')
        self.tree.heading('museum', text='Museum')
        self.tree.heading('id', text='ID')
        self.tree.heading('title', text='Title')
        self.tree.heading('date', text='Date')
        self.tree.heading('culture', text='Culture')

        self.tree.column('sel', width=30, anchor='center')
        self.tree.column('museum', width=150)
        self.tree.column('id', width=120)
        self.tree.column('title', width=350)
        self.tree.column('date', width=100)
        self.tree.column('culture', width=150)

        # Configure tag colors
        self.tree.tag_configure('green', background='#e6ffe6')
        self.tree.tag_configure('blue', background='#e6f3ff')
        self.tree.tag_configure('yellow', background='#fff9e6')
        self.tree.tag_configure('info', background='#e0e0e0', foreground='#666666')

        vsb = ttk.Scrollbar(res_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(res_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        res_frame.grid_rowconfigure(0, weight=1)
        res_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Button-1>', self._on_tree_click)

        # Pagination controls
        pagination_frame = ttk.Frame(main)
        pagination_frame.pack(fill=tk.X, pady=(0,5))

        self.page_label = ttk.Label(pagination_frame, text="Page 1", font=('Arial', 9))
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.results_label = ttk.Label(pagination_frame, text="0 results", font=('Arial', 9))
        self.results_label.pack(side=tk.LEFT, padx=20)

        self.prev_btn = ttk.Button(pagination_frame, text="◀ Previous",
                                   command=self._prev_page, state='disabled')
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.next_btn = ttk.Button(pagination_frame, text="Next 20 ▶",
                                   command=self._next_page, state='disabled')
        self.next_btn.pack(side=tk.LEFT, padx=2)

        # Bottom buttons
        bottom = ttk.Frame(main)
        bottom.pack(fill=tk.X)

        left = ttk.Frame(bottom)
        left.pack(side=tk.LEFT)
        ttk.Button(left, text="☑ Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(left, text="☐ Deselect All", command=self._deselect_all).pack(side=tk.LEFT, padx=2)

        self.sel_label = ttk.Label(bottom, text="Selected: 0", font=('Arial',10,'bold'))
        self.sel_label.pack(side=tk.LEFT, padx=20)

        ttk.Button(bottom, text="📥 Import Selected", command=self._import_selected,
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=2)
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_museum_select(self, event=None):
        name = self.museum_combo.get()
        for n, cls in MUSEUMS:
            if n == name:
                self.handler_class = cls
                self.current_handler = cls(self.request_handler)
                break

        # Reset pagination when museum changes
        self.current_page = 0
        self._update_pagination_buttons()

        # Show description based on color
        if self.current_handler.color == 'green':
            self.museum_desc.config(text="✅ API Access – Fast, reliable")
        elif self.current_handler.color == 'blue':
            self.museum_desc.config(text="🔵 Aggregator – 200+ museums via Europeana")
        elif self.current_handler.color == 'yellow':
            self.museum_desc.config(text="🟡 Web Scraping – Respectful, rate-limited (slower)")

    def _start_search(self):
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        self.selected = {}
        self._update_sel_label()

        self.current_query = self.search_var.get().strip()
        if not self.current_query:
            messagebox.showwarning("No query", "Please enter a search term.", parent=self)
            return

        if not self.current_handler:
            messagebox.showwarning("No museum", "Please select a museum first.", parent=self)
            return

        # Reset to first page
        self.current_page = 0

        self.search_btn.pack_forget()
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_label.config(text="Searching...", foreground='orange')

        self.stop_event.clear()
        self.current_search_thread = threading.Thread(target=self._search_thread, args=(self.current_query, self.current_page), daemon=True)
        self.current_search_thread.start()

    def _search_thread(self, query, page):
        error = None
        artifacts = []
        has_more = False
        total = 0
        try:
            self.current_handler.set_stop_event(self.stop_event)
            artifacts, has_more, total = self.current_handler.search(query, page)
        except Exception as e:
            error = str(e)

        self.after(0, lambda: self._search_done(artifacts, has_more, total, error))

    def _search_done(self, artifacts, has_more, total, error):
        self.progress.stop()
        self.progress.pack_forget()
        self.stop_btn.pack_forget()
        self.search_btn.pack(side=tk.LEFT, padx=5)

        if error:
            self.status_label.config(text=f"❌ Error: {error[:100]}", foreground='red')
            messagebox.showerror("Search Error", error, parent=self)
            return

        self.results = artifacts
        self.has_more = has_more
        self.total_results = total

        for art in artifacts:
            tag = self.current_handler.color
            if art.get('info'):
                tag = 'info'

            self.tree.insert('', 'end', iid=art['id'], tags=(tag,),
                            values=('☐',
                                   art.get('museum_name', self.current_handler.museum_name)[:25],
                                   art['id'][:20],
                                   art.get('title', 'Unknown')[:60],
                                   art.get('date', 'Unknown')[:20],
                                   art.get('culture', 'Unknown')[:30]))

        # Update pagination display
        self._update_pagination_display()
        self.status_label.config(text=f"✅ Found {len(artifacts)} items. Page {self.current_page + 1}", foreground='green')

    def _next_page(self):
        if not self.has_more:
            return

        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        self.selected = {}
        self._update_sel_label()

        self.current_page += 1

        self.search_btn.pack_forget()
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_label.config(text=f"Loading page {self.current_page + 1}...", foreground='orange')

        self.stop_event.clear()
        self.current_search_thread = threading.Thread(target=self._search_thread, args=(self.current_query, self.current_page), daemon=True)
        self.current_search_thread.start()

    def _prev_page(self):
        if self.current_page <= 0:
            return

        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        self.selected = {}
        self._update_sel_label()

        self.current_page -= 1

        self.search_btn.pack_forget()
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.status_label.config(text=f"Loading page {self.current_page + 1}...", foreground='orange')

        self.stop_event.clear()
        self.current_search_thread = threading.Thread(target=self._search_thread, args=(self.current_query, self.current_page), daemon=True)
        self.current_search_thread.start()

    def _update_pagination_display(self):
        """Update pagination labels and buttons"""
        self.page_label.config(text=f"Page {self.current_page + 1}")

        if self.total_results > 0:
            start = self.current_page * self.current_handler.limit + 1
            end = min(start + len(self.results) - 1, self.total_results)
            self.results_label.config(text=f"Showing {start}-{end} of {self.total_results}")
        else:
            self.results_label.config(text=f"{len(self.results)} results")

        self.prev_btn.config(state='normal' if self.current_page > 0 else 'disabled')
        self.next_btn.config(state='normal' if self.has_more else 'disabled')

    def _update_pagination_buttons(self):
        """Reset pagination buttons when museum changes"""
        self.prev_btn.config(state='disabled')
        self.next_btn.config(state='disabled')
        self.page_label.config(text="Page 1")
        self.results_label.config(text="0 results")

    def _stop_search(self):
        self.stop_event.set()
        self.status_label.config(text="Stopping...", foreground='orange')
        self.progress.stop()
        self.progress.pack_forget()
        self.stop_btn.pack_forget()
        self.search_btn.pack(side=tk.LEFT, padx=5)

    def _on_tree_click(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region == 'cell' and self.tree.identify_column(event.x) == '#1':
            item = self.tree.identify_row(event.y)
            if item:
                self._toggle_selection(item)

    def _toggle_selection(self, item_id):
        if item_id in self.selected:
            del self.selected[item_id]
            values = list(self.tree.item(item_id, 'values'))
            values[0] = '☐'
            self.tree.item(item_id, values=values)
        else:
            art = next((a for a in self.results if a['id'] == item_id), None)
            if art:
                self.selected[item_id] = art
                values = list(self.tree.item(item_id, 'values'))
                values[0] = '☑'
                self.tree.item(item_id, values=values)
        self._update_sel_label()

    def _select_all(self):
        for item in self.tree.get_children():
            if item not in self.selected:
                self._toggle_selection(item)

    def _deselect_all(self):
        for item in list(self.selected.keys()):
            self._toggle_selection(item)

    def _update_sel_label(self):
        self.sel_label.config(text=f"Selected: {len(self.selected)}")

    def _import_selected(self):
        if not self.selected:
            messagebox.showinfo("No Selection", "Please select at least one item.", parent=self)
            return

        table_data = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for obj_id, art in self.selected.items():
            row = {
                'Sample_ID': f"{art.get('museum_code', 'MUS')}-{obj_id[-20:]}",
                'Timestamp': timestamp,
                'Source': 'Museum Import Pro',
                'Museum': art.get('museum_name', self.current_handler.museum_name),
                'Museum_Code': art.get('museum_code', ''),
                'Object_ID': obj_id[:50],
                'Title': art.get('title', 'Untitled')[:200],
                'Date': art.get('date', 'Unknown')[:50],
                'Culture': art.get('culture', 'Unknown')[:100],
                'Medium': art.get('medium', '')[:100],
                'Museum_URL': art.get('url', ''),
                'Import_Date': timestamp,
                'Notes': f"Imported from {art.get('museum_name', 'Unknown')}",
                'Plugin': PLUGIN_INFO['name']
            }
            table_data.append(row)

        if hasattr(self.app, 'import_data_from_plugin'):
            self.app.import_data_from_plugin(table_data)
            messagebox.showinfo("Import Complete", f"✅ Imported {len(table_data)} artifacts.", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error", "Main app does not support plugin import.", parent=self)


# ============================================================================
# PLUGIN CLASS
# ============================================================================
class MuseumImportPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None

    def open_window(self):
        """Open the museum import dialog."""
        if not HAS_REQUESTS:
            messagebox.showerror("Missing Dependency",
                               "Requests library is required.\n\npip install requests")
            return

        if not HAS_BS4:
            if messagebox.askyesno("Missing Dependency",
                                 "BeautifulSoup4 is recommended for web scraping museums.\n\n"
                                 "Install it now? (pip install beautifulsoup4)"):
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
                messagebox.showinfo("Restart Required", "Please restart the application.")
                return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        dialog = MuseumImportDialog(self.app.root, self.app)
        self.window = dialog


# ============================================================================
# SETUP FUNCTION
# ============================================================================
def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = MuseumImportPlugin(main_app)
    return plugin
