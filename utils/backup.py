"""
Backup management for safe file deletion
"""

import shutil
import tarfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup."""
    original_path: Path
    backup_path: Path
    backup_time: datetime
    size: int
    compressed: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_path': str(self.original_path),
            'backup_path': str(self.backup_path),
            'backup_time': self.backup_time.isoformat(),
            'size': self.size,
            'compressed': self.compressed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BackupInfo':
        """Create from dictionary."""
        return cls(
            original_path=Path(data['original_path']),
            backup_path=Path(data['backup_path']),
            backup_time=datetime.fromisoformat(data['backup_time']),
            size=data['size'],
            compressed=data['compressed']
        )


class BackupManager:
    """Manages file backups before deletion."""

    def __init__(self, config: Config):
        self.config = config
        self.backup_dir = config.backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup index file
        self.index_file = self.backup_dir / "backup_index.json"
        self.index = self._load_index()

        # Create today's backup directory
        self.today_dir = self.backup_dir / datetime.now().strftime("%Y-%m-%d")
        self.today_dir.mkdir(exist_ok=True)

    def _load_index(self) -> Dict[str, BackupInfo]:
        """Load backup index from file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)

                return {
                    path: BackupInfo.from_dict(info)
                    for path, info in data.items()
                }

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error loading backup index: {e}")

        return {}

    def _save_index(self):
        """Save backup index to file."""
        data = {
            str(path): info.to_dict()
            for path, info in self.index.items()
        }

        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)

    def backup_file(self, file_path: Path) -> Optional[BackupInfo]:
        """
        Create a backup of a file.

        Args:
            file_path: Path to file to backup

        Returns:
            BackupInfo if successful, None otherwise
        """
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return None

        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%H%M%S")
            backup_name = f"{file_path.name}_{timestamp}"

            if file_path.is_dir():
                backup_name += ".tar.gz" if self.config.compress_backups else ""
                backup_path = self.today_dir / backup_name

                if self.config.compress_backups:
                    # Create compressed archive
                    with tarfile.open(backup_path, "w:gz") as tar:
                        tar.add(file_path, arcname=file_path.name)
                else:
                    # Copy directory
                    shutil.copytree(file_path, backup_path)

            else:
                # Single file
                if self.config.compress_backups:
                    backup_name += ".gz"
                    backup_path = self.today_dir / backup_name

                    # Compress file
                    import gzip
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(backup_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    backup_path = self.today_dir / backup_name
                    shutil.copy2(file_path, backup_path)

            # Get backup size
            if backup_path.is_dir():
                size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            else:
                size = backup_path.stat().st_size

            # Create backup info
            backup_info = BackupInfo(
                original_path=file_path,
                backup_path=backup_path,
                backup_time=datetime.now(),
                size=size,
                compressed=self.config.compress_backups
            )

            # Update index
            self.index[str(file_path)] = backup_info
            self._save_index()

            logger.info(f"Backed up: {file_path} -> {backup_path}")
            return backup_info

        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            return None

    def restore_file(self, original_path: Path) -> bool:
        """
        Restore a file from backup.

        Args:
            original_path: Original path of the file

        Returns:
            True if successful
        """
        backup_key = str(original_path)

        if backup_key not in self.index:
            logger.warning(f"No backup found for: {original_path}")
            return False

        backup_info = self.index[backup_key]

        if not backup_info.backup_path.exists():
            logger.error(f"Backup file missing: {backup_info.backup_path}")
            return False

        try:
            # Ensure parent directory exists
            original_path.parent.mkdir(parents=True, exist_ok=True)

            if backup_info.compressed:
                if backup_info.backup_path.suffix == '.gz':
                    # Decompress single file
                    import gzip
                    with gzip.open(backup_info.backup_path, 'rb') as f_in:
                        with open(original_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                elif backup_info.backup_path.suffix == '.tar.gz':
                    # Extract archive
                    with tarfile.open(backup_info.backup_path, 'r:gz') as tar:
                        tar.extractall(original_path.parent)

            else:
                # Simple copy
                if backup_info.backup_path.is_dir():
                    shutil.copytree(backup_info.backup_path, original_path)
                else:
                    shutil.copy2(backup_info.backup_path, original_path)

            logger.info(f"Restored: {original_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore {original_path}: {e}")
            return False

    def list_backups(self) -> List[BackupInfo]:
        """List all available backups."""
        return list(self.index.values())

    def clean_old_backups(self):
        """Remove backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.config.backup_retention_days)

        removed_count = 0

        for backup_key, backup_info in list(self.index.items()):
            if backup_info.backup_time < cutoff_date:
                try:
                    # Remove backup file
                    if backup_info.backup_path.exists():
                        if backup_info.backup_path.is_dir():
                            shutil.rmtree(backup_info.backup_path)
                        else:
                            backup_info.backup_path.unlink()

                    # Remove from index
                    del self.index[backup_key]
                    removed_count += 1

                except Exception as e:
                    logger.error(f"Failed to remove old backup {backup_info.backup_path}: {e}")

        if removed_count > 0:
            self._save_index()
            logger.info(f"Removed {removed_count} old backups")

        # Remove empty date directories
        for date_dir in self.backup_dir.iterdir():
            if date_dir.is_dir() and date_dir.name != datetime.now().strftime("%Y-%m-%d"):
                try:
                    if not any(date_dir.iterdir()):
                        date_dir.rmdir()
                except Exception:
                    pass

    def get_backup_size(self) -> int:
        """Get total size of all backups."""
        total_size = 0

        for backup_info in self.index.values():
            total_size += backup_info.size

        return total_size

    def verify_backups(self) -> Dict[str, bool]:
        """Verify that all indexed backups exist."""
        results = {}

        for original_path, backup_info in self.index.items():
            results[original_path] = backup_info.backup_path.exists()

        return results