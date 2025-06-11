"""
System scanner module for identifying files to clean
"""

import os
import time
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.scan_result import (
    FileInfo, CategoryResult, ScanResult,
    FileCategory, CleaningPriority, SystemInfo
)
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class SystemScanner:
    """Scans macOS system for cleanable files."""

    def __init__(self, config: Config):
        self.config = config
        self.home_path = Path.home()
        self.library_path = self.home_path / "Library"

        # Define scan paths for each category
        self.scan_paths = {
            FileCategory.SYSTEM_CACHE: [
                Path("/Library/Caches"),
                Path("/System/Library/Caches"),
                self.library_path / "Caches",
            ],
            FileCategory.USER_CACHE: [
                self.library_path / "Caches",
                self.home_path / ".cache",
            ],
            FileCategory.BROWSER_CACHE: [
                self.library_path / "Caches" / "com.apple.Safari",
                self.library_path / "Caches" / "Google" / "Chrome",
                self.library_path / "Caches" / "Firefox",
            ],
            FileCategory.TEMPORARY_FILES: [
                Path("/tmp"),
                Path("/var/tmp"),
                self.home_path / "Downloads" / "*.tmp",
            ],
            FileCategory.LOG_FILES: [
                Path("/var/log"),
                self.library_path / "Logs",
                self.home_path / ".local" / "share" / "logs",
            ],
            FileCategory.DOWNLOADS: [
                self.home_path / "Downloads",
            ],
            FileCategory.TRASH: [
                self.home_path / ".Trash",
            ],
            FileCategory.APP_LEFTOVERS: [
                self.library_path / "Application Support",
                self.library_path / "Preferences",
                self.library_path / "Saved Application State",
            ],
        }

        # File extensions to consider for cleaning
        self.cleanable_extensions = {
            ".tmp", ".temp", ".cache", ".log", ".old",
            ".bak", ".backup", ".crash", ".dump"
        }

    def scan(self, categories: Optional[List[FileCategory]] = None) -> ScanResult:
        """
        Scan system for cleanable files.

        Args:
            categories: Specific categories to scan, or None for all

        Returns:
            ScanResult with found files
        """
        start_time = time.time()
        result = ScanResult()

        if categories is None:
            categories = list(FileCategory)

        logger.info(f"Starting system scan for {len(categories)} categories")

        # Scan each category
        for category in categories:
            if category in self.scan_paths:
                try:
                    category_result = self._scan_category(category)
                    result.add_category_result(category_result)
                except Exception as e:
                    logger.error(f"Error scanning {category.name}: {e}")
                    result.errors.append(f"Failed to scan {category.name}: {str(e)}")

        # Scan for duplicates if requested
        if FileCategory.DUPLICATES in categories:
            try:
                duplicates_result = self._scan_duplicates()
                result.add_category_result(duplicates_result)
            except Exception as e:
                logger.error(f"Error scanning duplicates: {e}")
                result.errors.append(f"Failed to scan duplicates: {str(e)}")

        # Scan for large files if requested
        if FileCategory.LARGE_FILES in categories:
            try:
                large_files_result = self._scan_large_files()
                result.add_category_result(large_files_result)
            except Exception as e:
                logger.error(f"Error scanning large files: {e}")
                result.errors.append(f"Failed to scan large files: {str(e)}")

        # Scan for old files if requested
        if FileCategory.OLD_FILES in categories:
            try:
                old_files_result = self._scan_old_files()
                result.add_category_result(old_files_result)
            except Exception as e:
                logger.error(f"Error scanning old files: {e}")
                result.errors.append(f"Failed to scan old files: {str(e)}")

        result.scan_duration = time.time() - start_time
        logger.info(f"Scan completed in {result.scan_duration:.2f} seconds")

        return result

    def _scan_category(self, category: FileCategory) -> CategoryResult:
        """Scan a specific category."""
        result = CategoryResult(
            category=category,
            priority=self._get_category_priority(category),
            description=self._get_category_description(category)
        )

        paths = self.scan_paths.get(category, [])

        for scan_path in paths:
            if not scan_path.exists():
                continue

            try:
                if scan_path.is_dir():
                    self._scan_directory(scan_path, category, result)
                else:
                    # Handle glob patterns
                    for path in scan_path.parent.glob(scan_path.name):
                        if path.is_file():
                            file_info = self._analyze_file(path, category)
                            if file_info:
                                result.add_file(file_info)
            except PermissionError:
                logger.warning(f"Permission denied: {scan_path}")
            except Exception as e:
                logger.error(f"Error scanning {scan_path}: {e}")

        return result

    def _scan_directory(self, directory: Path, category: FileCategory,
                        result: CategoryResult, max_depth: int = 3):
        """Recursively scan a directory."""
        if max_depth <= 0:
            return

        try:
            for item in directory.iterdir():
                try:
                    if item.is_dir() and not item.is_symlink():
                        # Skip certain system directories
                        if item.name.startswith('.') and category != FileCategory.USER_CACHE:
                            continue

                        self._scan_directory(item, category, result, max_depth - 1)

                    elif item.is_file():
                        file_info = self._analyze_file(item, category)
                        if file_info:
                            result.add_file(file_info)

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            logger.warning(f"Cannot access directory: {directory}")

    def _analyze_file(self, file_path: Path, category: FileCategory) -> Optional[FileInfo]:
        """Analyze a file and determine if it should be cleaned."""
        try:
            stat = file_path.stat()

            # Skip very small files
            if stat.st_size < 1024:  # 1KB
                return None

            # Check if file matches cleanable criteria
            if not self._is_cleanable(file_path, category):
                return None

            return FileInfo(
                path=file_path,
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                accessed_time=datetime.fromtimestamp(stat.st_atime),
                category=category,
                priority=self._get_file_priority(file_path, category),
                is_safe_to_delete=self._is_safe_to_delete(file_path, category),
                description=self._get_file_description(file_path)
            )

        except (OSError, PermissionError):
            return None

    def _is_cleanable(self, file_path: Path, category: FileCategory) -> bool:
        """Check if a file is cleanable based on category and rules."""
        # Category-specific rules
        if category in [FileCategory.SYSTEM_CACHE, FileCategory.USER_CACHE,
                        FileCategory.BROWSER_CACHE]:
            return True

        if category == FileCategory.TEMPORARY_FILES:
            return file_path.suffix.lower() in self.cleanable_extensions

        if category == FileCategory.LOG_FILES:
            return file_path.suffix.lower() in ['.log', '.txt']

        if category == FileCategory.DOWNLOADS:
            # Only old downloads
            stat = file_path.stat()
            age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            return age > timedelta(days=30)

        if category == FileCategory.TRASH:
            return True

        if category == FileCategory.APP_LEFTOVERS:
            # Check if app still exists
            return not self._is_app_installed(file_path)

        return False

    def _is_safe_to_delete(self, file_path: Path, category: FileCategory) -> bool:
        """Determine if a file is safe to delete."""
        # Never delete system-critical files
        critical_paths = [
            "/System", "/Library/Extensions", "/usr/bin", "/usr/sbin"
        ]

        for critical in critical_paths:
            if str(file_path).startswith(critical):
                return False

        # Category-specific safety rules
        if category == FileCategory.SYSTEM_CACHE:
            # Only caches older than 7 days
            stat = file_path.stat()
            age = datetime.now() - datetime.fromtimestamp(stat.st_atime)
            return age > timedelta(days=7)

        return True

    def _scan_duplicates(self) -> CategoryResult:
        """Scan for duplicate files."""
        result = CategoryResult(
            category=FileCategory.DUPLICATES,
            priority=CleaningPriority.LOW,
            description="Duplicate files taking up extra space"
        )

        # Common directories to check for duplicates
        scan_dirs = [
            self.home_path / "Downloads",
            self.home_path / "Documents",
            self.home_path / "Pictures",
            self.home_path / "Desktop",
        ]

        file_hashes: Dict[str, List[Path]] = {}

        for directory in scan_dirs:
            if not directory.exists():
                continue

            self._find_duplicates_in_directory(directory, file_hashes)

        # Process duplicates
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                # Keep the oldest file, mark others as duplicates
                paths.sort(key=lambda p: p.stat().st_mtime)

                for path in paths[1:]:
                    try:
                        stat = path.stat()
                        file_info = FileInfo(
                            path=path,
                            size=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime),
                            accessed_time=datetime.fromtimestamp(stat.st_atime),
                            category=FileCategory.DUPLICATES,
                            priority=CleaningPriority.LOW,
                            is_safe_to_delete=True,
                            description=f"Duplicate of {paths[0].name}"
                        )
                        result.add_file(file_info)
                    except (OSError, PermissionError):
                        continue

        return result

    def _find_duplicates_in_directory(self, directory: Path,
                                      file_hashes: Dict[str, List[Path]]):
        """Find duplicate files in a directory."""
        try:
            for item in directory.rglob("*"):
                if item.is_file() and item.stat().st_size > 1024 * 100:  # > 100KB
                    file_hash = self._get_file_hash(item)
                    if file_hash:
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(item)
        except (PermissionError, OSError):
            pass

    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate file hash for duplicate detection."""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def _scan_large_files(self) -> CategoryResult:
        """Scan for large files."""
        result = CategoryResult(
            category=FileCategory.LARGE_FILES,
            priority=CleaningPriority.OPTIONAL,
            description="Large files that might be unnecessary"
        )

        # Directories to scan for large files
        scan_dirs = [
            self.home_path / "Downloads",
            self.home_path / "Documents",
            self.home_path / "Desktop",
            self.home_path / "Movies",
        ]

        min_size = 100 * 1024 * 1024  # 100MB

        for directory in scan_dirs:
            if not directory.exists():
                continue

            try:
                for item in directory.rglob("*"):
                    if item.is_file():
                        stat = item.stat()
                        if stat.st_size >= min_size:
                            file_info = FileInfo(
                                path=item,
                                size=stat.st_size,
                                modified_time=datetime.fromtimestamp(stat.st_mtime),
                                accessed_time=datetime.fromtimestamp(stat.st_atime),
                                category=FileCategory.LARGE_FILES,
                                priority=CleaningPriority.OPTIONAL,
                                is_safe_to_delete=True,
                                description=f"Large file ({stat.st_size / (1024 ** 3):.1f} GB)"
                            )
                            result.add_file(file_info)
            except (PermissionError, OSError):
                continue

        return result

    def _scan_old_files(self) -> CategoryResult:
        """Scan for old files."""
        result = CategoryResult(
            category=FileCategory.OLD_FILES,
            priority=CleaningPriority.OPTIONAL,
            description="Files not accessed in a long time"
        )

        # Directories to scan
        scan_dirs = [
            self.home_path / "Downloads",
            self.home_path / "Desktop",
        ]

        max_age = timedelta(days=180)  # 6 months

        for directory in scan_dirs:
            if not directory.exists():
                continue

            try:
                for item in directory.rglob("*"):
                    if item.is_file():
                        stat = item.stat()
                        age = datetime.now() - datetime.fromtimestamp(stat.st_atime)

                        if age > max_age:
                            file_info = FileInfo(
                                path=item,
                                size=stat.st_size,
                                modified_time=datetime.fromtimestamp(stat.st_mtime),
                                accessed_time=datetime.fromtimestamp(stat.st_atime),
                                category=FileCategory.OLD_FILES,
                                priority=CleaningPriority.OPTIONAL,
                                is_safe_to_delete=True,
                                description=f"Not accessed for {age.days} days"
                            )
                            result.add_file(file_info)
            except (PermissionError, OSError):
                continue

        return result

    def _is_app_installed(self, file_path: Path) -> bool:
        """Check if an application is still installed."""
        # Extract app name from path
        app_name = None

        if "Application Support" in str(file_path):
            # Get the app folder name
            parts = file_path.parts
            idx = parts.index("Application Support")
            if idx + 1 < len(parts):
                app_name = parts[idx + 1]

        if not app_name:
            return True  # Assume installed if can't determine

        # Check common app locations
        app_locations = [
            Path("/Applications"),
            Path.home() / "Applications",
        ]

        for location in app_locations:
            if (location / f"{app_name}.app").exists():
                return True

        return False

    def _get_category_priority(self, category: FileCategory) -> CleaningPriority:
        """Get priority for a category."""
        priority_map = {
            FileCategory.SYSTEM_CACHE: CleaningPriority.HIGH,
            FileCategory.USER_CACHE: CleaningPriority.HIGH,
            FileCategory.BROWSER_CACHE: CleaningPriority.HIGH,
            FileCategory.TEMPORARY_FILES: CleaningPriority.HIGH,
            FileCategory.LOG_FILES: CleaningPriority.MEDIUM,
            FileCategory.TRASH: CleaningPriority.MEDIUM,
            FileCategory.DOWNLOADS: CleaningPriority.LOW,
            FileCategory.APP_LEFTOVERS: CleaningPriority.MEDIUM,
            FileCategory.DUPLICATES: CleaningPriority.LOW,
            FileCategory.LARGE_FILES: CleaningPriority.OPTIONAL,
            FileCategory.OLD_FILES: CleaningPriority.OPTIONAL,
        }
        return priority_map.get(category, CleaningPriority.MEDIUM)

    def _get_category_description(self, category: FileCategory) -> str:
        """Get description for a category."""
        descriptions = {
            FileCategory.SYSTEM_CACHE: "System cache files that can be safely removed",
            FileCategory.USER_CACHE: "User application caches",
            FileCategory.BROWSER_CACHE: "Web browser cache files",
            FileCategory.TEMPORARY_FILES: "Temporary files no longer needed",
            FileCategory.LOG_FILES: "Old log files taking up space",
            FileCategory.TRASH: "Files in trash waiting to be deleted",
            FileCategory.DOWNLOADS: "Old files in Downloads folder",
            FileCategory.APP_LEFTOVERS: "Files from uninstalled applications",
            FileCategory.DUPLICATES: "Duplicate files taking up extra space",
            FileCategory.LARGE_FILES: "Large files that might be unnecessary",
            FileCategory.OLD_FILES: "Files not accessed in a long time",
        }
        return descriptions.get(category, "")

    def _get_file_priority(self, file_path: Path, category: FileCategory) -> CleaningPriority:
        """Get priority for a specific file."""
        # Use category priority by default
        return self._get_category_priority(category)

    def _get_file_description(self, file_path: Path) -> str:
        """Get description for a specific file."""
        return f"File: {file_path.name}"

    def get_system_info(self) -> SystemInfo:
        """Get current system information."""
        import psutil
        import platform

        disk_usage = psutil.disk_usage('/')
        memory = psutil.virtual_memory()

        return SystemInfo(
            total_disk_space=disk_usage.total,
            used_disk_space=disk_usage.used,
            free_disk_space=disk_usage.free,
            total_memory=memory.total,
            used_memory=memory.used,
            free_memory=memory.available,
            cpu_usage=psutil.cpu_percent(interval=1),
            macos_version=platform.mac_ver()[0]
        )