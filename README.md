# 🍎 macOS Cleaner

A beautiful and efficient console application for cleaning and optimizing macOS systems.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)

## ✨ Features

- **🔍 Smart Scanning**: Intelligently identifies unnecessary files across your system
- **🧹 Safe Cleaning**: Removes only safe-to-delete files with backup options
- **⚡ System Optimization**: Memory purging, DNS flushing, and startup item management
- **🎨 Beautiful UI**: Rich console interface with colors, progress bars, and animations
- **🛡️ Safety First**: Built-in protections and confirmation prompts
- **📊 Detailed Reports**: Comprehensive scan results and cleaning summaries

## 📋 Supported Cleaning Categories

- **System & User Caches**: Clear application and system cache files
- **Browser Caches**: Remove browser temporary files
- **Temporary Files**: Clean up system temporary directories
- **Log Files**: Remove old log files
- **Downloads**: Identify old files in Downloads folder
- **Trash**: Empty system trash
- **Duplicate Files**: Find and remove duplicate files
- **Large Files**: Identify unusually large files
- **Old Files**: Find files not accessed in months
- **App Leftovers**: Remove files from uninstalled applications

## 🚀 Installation

### Using pip

```bash
pip install mac-clean-cli
```

### Using Homebrew (coming soon)

```bash
brew install mac-clean-cli
```

### From Source

```bash
git clone https://github.com/qdenka/MacCleanCLI.git
cd MacCleanCLI
pip install -e .
```

## 📖 Usage

### Basic Usage

```bash
# Run interactive mode
mac-clean

# Or use the short alias
mclean
```

### Command Line Options

```bash
# Scan only, don't clean
mac-clean --scan-only

# Automatic mode (clean recommended items)
mac-clean --auto

# Use custom config file
mac-clean --config ~/myconfig.json

# Enable verbose output
mac-clean --verbose
```

## 🎮 Interactive Mode

The interactive mode provides a user-friendly menu system:

1. **Scan System**: Choose categories to scan
2. **Clean Files**: Select and clean identified files
3. **Optimize System**: Run system optimization tasks
4. **Settings**: Configure application behavior

## ⚙️ Configuration

Configuration file is stored at `~/.MacCleanCLI/config.json`

### Key Settings

```json
{
  "dry_run": false,
  "enable_backup": true,
  "verify_cleaning": true,
  "remove_empty_dirs": true,
  "max_workers": 4,
  "backup_retention_days": 7
}
```

## 🛡️ Safety Features

- **Protected Paths**: System-critical directories are never touched
- **Backup System**: Optional backup before deletion
- **Dry Run Mode**: Preview what would be deleted without actually removing files
- **Confirmation Prompts**: Require user confirmation for destructive operations
- **Verification**: Post-cleaning verification of file removal

## 🏗️ Architecture

The application follows SOLID principles and clean architecture:

```
MacCleanCLI/
├── main.py              # Entry point
├── core/               # Core business logic
│   ├── scanner.py      # System scanning
│   ├── cleaner.py      # File cleaning
│   └── optimizer.py    # System optimization
├── models/             # Data models
│   └── scan_result.py  # Result structures
├── ui/                 # User interface
│   ├── interface.py    # Main UI logic
│   └── components.py   # UI components
└── utils/              # Utilities
    ├── config.py       # Configuration
    ├── logger.py       # Logging
    └── backup.py       # Backup management
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/qdenka/MacCleanCLI.git
cd MacCleanCLI

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_scanner.py
```

### Code Style

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .
```

## 📊 Performance

- **Multi-threaded scanning**: Utilizes multiple CPU cores for faster scanning
- **Efficient file operations**: Batch operations for improved performance
- **Memory efficient**: Streams large files instead of loading into memory
- **Progress indication**: Real-time progress updates during operations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal UI
- Uses [psutil](https://github.com/giampaolo/psutil) for system information
- Inspired by various macOS cleaning utilities

## ⚠️ Disclaimer

This software is provided as-is. Always ensure you have backups of important data before running system cleaning operations. The authors are not responsible for any data loss.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/qdenka/MacCleanCLI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/macos/MacCleanCLI/discussions)
- **Wiki**: [Documentation Wiki](https://github.com/macos/MacCleanCLI/wiki)