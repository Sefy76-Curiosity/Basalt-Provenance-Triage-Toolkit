"""
Enhanced Features Package for Scientific Toolkit
Contains all new productivity and workflow features
"""

from .tooltip_manager import ToolTip, ToolTipManager
from .recent_files_manager import RecentFilesManager
from .macro_recorder import MacroRecorder, MacroManagerDialog
from .project_manager import ProjectManager
from .script_exporter import ScriptExporter

__all__ = [
    'ToolTip',
    'ToolTipManager',
    'RecentFilesManager',
    'MacroRecorder',
    'MacroManagerDialog',
    'ProjectManager',
    'ScriptExporter',
]

__version__ = '1.0.0'
__author__ = 'Enhanced by Claude (Anthropic)'
