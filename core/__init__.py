# core/__init__.py
"""
Core functionality for macOS Cleaner
"""

from .scanner import SystemScanner
from .cleaner import SystemCleaner, SafeCleaningContext
from .optimizer import SystemOptimizer

__all__ = ['SystemScanner', 'SystemCleaner', 'SafeCleaningContext', 'SystemOptimizer']

# models/__init__.py
"""
Data models for macOS Cleaner
"""

from .scan_result import (
    FileInfo, CategoryResult, ScanResult, CleaningResult,
    SystemInfo, FileCategory, CleaningPriority
)

__all__ = [
    'FileInfo', 'CategoryResult', 'ScanResult', 'CleaningResult',
    'SystemInfo', 'FileCategory', 'CleaningPriority'
]

# ui/__init__.py
"""
User interface components for macOS Cleaner
"""

from .interface import CleanerInterface
from .components import (
    create_header, create_system_info_panel, create_scan_results_table,
    format_size, format_time
)

__all__ = [
    'CleanerInterface', 'create_header', 'create_system_info_panel',
    'create_scan_results_table', 'format_size', 'format_time'
]

# utils/__init__.py
"""
Utility modules for macOS Cleaner
"""

from .config import Config, load_config
from .logger import setup_logger, get_logger
from .backup import BackupManager

__all__ = ['Config', 'load_config', 'setup_logger', 'get_logger', 'BackupManager']