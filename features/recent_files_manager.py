"""
Recent Files Manager - Track and display recently opened files
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class RecentFilesManager:
    """
    Manages recently opened files list
    """
    def __init__(self, max_recent: int = 10):
        self.max_recent = max_recent
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "recent_files.json"
        self.recent_files: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load recent files from config"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_files = data.get('files', [])
                    # Verify files still exist
                    self.recent_files = [
                        f for f in self.recent_files 
                        if Path(f['path']).exists()
                    ]
            except Exception as e:
                print(f"⚠️ Error loading recent files: {e}")
                self.recent_files = []
    
    def _save(self):
        """Save recent files to config"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'files': self.recent_files}, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving recent files: {e}")
    
    def add(self, filepath: str):
        """Add file to recent files list"""
        filepath = str(Path(filepath).resolve())
        
        # Remove if already exists
        self.recent_files = [f for f in self.recent_files if f['path'] != filepath]
        
        # Add to beginning
        self.recent_files.insert(0, {
            'path': filepath,
            'name': Path(filepath).name,
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim to max
        self.recent_files = self.recent_files[:self.max_recent]
        
        self._save()
    
    def get_all(self) -> List[Dict]:
        """Get all recent files"""
        return self.recent_files.copy()
    
    def clear(self):
        """Clear all recent files"""
        self.recent_files = []
        self._save()
    
    def get_menu_items(self) -> List[Dict]:
        """Get formatted items for menu display"""
        items = []
        for i, file_info in enumerate(self.recent_files):
            items.append({
                'label': f"{i+1}. {file_info['name']}",
                'path': file_info['path'],
                'full_label': f"{i+1}. {file_info['path']}"
            })
        return items
