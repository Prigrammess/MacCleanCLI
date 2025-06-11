"""
Tests for the SystemScanner module
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from core.scanner import SystemScanner
from models.scan_result import FileCategory, CleaningPriority
from utils.config import Config


class TestSystemScanner:
    """Test cases for SystemScanner."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            dry_run=True,
            scan_hidden_files=False,
            min_file_size_mb=0.001  # 1KB for testing
        )

    @pytest.fixture
    def scanner(self, config):
        """Create scanner instance."""
        return SystemScanner(config)

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_scanner_initialization(self, scanner):
        """Test scanner is properly initialized."""
        assert scanner is not None
        assert scanner.config is not None
        assert isinstance(scanner.scan_paths, dict)

    def test_scan_empty_categories(self, scanner):
        """Test scanning with no categories."""
        result = scanner.scan([])
        assert result is not None
        assert result.total_files_found == 0
        assert result.total_size_found == 0

    def test_scan_nonexistent_category(self, scanner):
        """Test scanning handles missing paths gracefully."""
        # Create a scanner with non-existent paths
        scanner.scan_paths[FileCategory.TEMPORARY_FILES] = [Path("/nonexistent/path")]

        result = scanner.scan([FileCategory.TEMPORARY_FILES])
        assert result is not None
        assert len(result.errors) == 0  # Should handle gracefully

    def test_analyze_file(self, scanner, temp_dir):
        """Test file analysis."""
        # Create a test file
        test_file = temp_dir / "test.tmp"
        test_file.write_text("test content")

        file_info = scanner._analyze_file(test_file, FileCategory.TEMPORARY_FILES)

        assert file_info is not None
        assert file_info.path == test_file
        assert file_info.size > 0
        assert file_info.category == FileCategory.TEMPORARY_FILES

    def test_is_cleanable(self, scanner, temp_dir):
        """Test cleanable file detection."""
        # Test temporary file
        tmp_file = temp_dir / "test.tmp"
        tmp_file.touch()
        assert scanner._is_cleanable(tmp_file, FileCategory.TEMPORARY_FILES) is True

        # Test log file
        log_file = temp_dir / "test.log"
        log_file.touch()
        assert scanner._is_cleanable(log_file, FileCategory.LOG_FILES) is True

        # Test regular file in temp category
        regular_file = temp_dir / "test.txt"
        regular_file.touch()
        assert scanner._is_cleanable(regular_file, FileCategory.TEMPORARY_FILES) is False

    def test_is_safe_to_delete(self, scanner):
        """Test safe deletion checks."""
        # System paths should not be safe
        system_file = Path("/System/Library/test.txt")
        assert scanner._is_safe_to_delete(system_file, FileCategory.SYSTEM_CACHE) is False

        # User cache should be safe
        user_cache = Path.home() / "Library/Caches/test.cache"
        assert scanner._is_safe_to_delete(user_cache, FileCategory.USER_CACHE) is True

    def test_get_file_hash(self, scanner, temp_dir):
        """Test file hash calculation."""
        # Create test file with known content
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        hash1 = scanner._get_file_hash(test_file)
        assert hash1 is not None
        assert len(hash1) == 32  # MD5 hash length

        # Same content should produce same hash
        test_file2 = temp_dir / "test2.txt"
        test_file2.write_text("Hello, World!")
        hash2 = scanner._get_file_hash(test_file2)

        assert hash1 == hash2

    def test_scan_duplicates(self, scanner, temp_dir):
        """Test duplicate file detection."""
        # Create duplicate files
        content = "This is duplicate content"
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"

        file1.write_text(content)
        file2.write_text(content)
        file3.write_text("Different content")

        # Override scan directory
        scanner.scan_paths[FileCategory.DUPLICATES] = [temp_dir]

        # Mock the _scan_duplicates method to use our temp directory
        original_dirs = [
            scanner.home_path / "Downloads",
            scanner.home_path / "Documents",
            scanner.home_path / "Pictures",
            scanner.home_path / "Desktop",
        ]

        # Temporarily replace scan directories
        scanner.home_path = temp_dir.parent
        result = scanner._scan_duplicates()

        # At least one duplicate should be found
        assert result.file_count >= 1

    def test_get_category_priority(self, scanner):
        """Test category priority assignment."""
        assert scanner._get_category_priority(FileCategory.SYSTEM_CACHE) == CleaningPriority.HIGH
        assert scanner._get_category_priority(FileCategory.LARGE_FILES) == CleaningPriority.OPTIONAL
        assert scanner._get_category_priority(FileCategory.LOG_FILES) == CleaningPriority.MEDIUM

    def test_scan_large_files(self, scanner, temp_dir):
        """Test large file detection."""
        # Create a large file (mock)
        large_file = temp_dir / "large.bin"
        # Create file with specific size
        size = 150 * 1024 * 1024  # 150MB
        large_file.write_bytes(b'0' * 1024)  # Write 1KB for testing

        # Mock file size
        import os
        original_stat = os.stat

        def mock_stat(path):
            if str(path) == str(large_file):
                stat_result = original_stat(path)
                # Mock the size
                class MockStat:
                    st_size = size
                    st_mtime = stat_result.st_mtime
                    st_atime = stat_result.st_atime
                return MockStat()
            return original_stat(path)

        # Temporarily override scan directory
        scanner.home_path = temp_dir.parent

        from unittest.mock import patch

        with patch('pathlib.Path.stat', side_effect=mock_stat):
            result = scanner._scan_large_files()

        # Should find at least one large file
        assert result.category == FileCategory.LARGE_FILES

    def test_get_system_info(self, scanner):
        """Test system information retrieval."""
        system_info = scanner.get_system_info()

        assert system_info is not None
        assert system_info.total_disk_space > 0
        assert system_info.total_memory > 0
        assert 0 <= system_info.cpu_usage <= 100
        assert system_info.macos_version != ""


class TestScanResult:
    """Test cases for ScanResult model."""

    def test_scan_result_initialization(self):
        """Test ScanResult initialization."""
        result = ScanResult()
        assert result.total_files_found == 0
        assert result.total_size_found == 0
        assert len(result.categories) == 0
        assert len(result.errors) == 0

    def test_add_category_result(self):
        """Test adding category results."""
        scan_result = ScanResult()
        category_result = CategoryResult(category=FileCategory.SYSTEM_CACHE)

        # Add some files
        from models.scan_result import FileInfo
        file_info = FileInfo(
            path=Path("/test/file"),
            size=1024,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.SYSTEM_CACHE,
            priority=CleaningPriority.HIGH
        )
        category_result.add_file(file_info)

        scan_result.add_category_result(category_result)

        assert scan_result.total_files_found == 1
        assert scan_result.total_size_found == 1024
        assert FileCategory.SYSTEM_CACHE in scan_result.categories

    def test_get_safe_to_clean_size(self):
        """Test calculation of safe-to-clean size."""
        scan_result = ScanResult()
        category_result = CategoryResult(category=FileCategory.SYSTEM_CACHE)

        # Add safe and unsafe files
        from models.scan_result import FileInfo
        safe_file = FileInfo(
            path=Path("/test/safe"),
            size=1024,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.SYSTEM_CACHE,
            priority=CleaningPriority.HIGH,
            is_safe_to_delete=True
        )

        unsafe_file = FileInfo(
            path=Path("/test/unsafe"),
            size=2048,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.SYSTEM_CACHE,
            priority=CleaningPriority.HIGH,
            is_safe_to_delete=False
        )

        category_result.add_file(safe_file)
        category_result.add_file(unsafe_file)
        scan_result.add_category_result(category_result)

        assert scan_result.get_safe_to_clean_size() == 1024


if __name__ == "__main__":
    pytest.main([__file__])