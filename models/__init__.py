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