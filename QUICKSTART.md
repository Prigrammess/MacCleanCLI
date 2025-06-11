# 🚀 macOS Cleaner - Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/qdenka/MacCleanCLI.git
cd MacCleanCLI

# Install with pip
pip install -e .

# Or install with all development dependencies
make install-dev
```

## First Run

```bash
# Run the application
mac-cleaner

# Or use the short alias
mclean
```

## Basic Workflow

### 1. Initial Scan
- Select option `[1] 🔍 Scan System` from main menu
- Choose `[a]` to scan all categories
- Wait for scan to complete

### 2. Review Results
- The scan will show:
  - Number of files found
  - Total space that can be freed
  - Priority levels (HIGH, MEDIUM, LOW, OPTIONAL)

### 3. Clean Files
- Select option `[2] 🧹 Clean Files`
- Choose `[2]` for Quick Clean (recommended items only)
- Or choose `[1]` to select specific categories
- Confirm the cleaning operation

### 4. Optimize System (Optional)
- Select option `[3] ⚡ Optimize System`
- Choose from:
  - Purge inactive memory
  - Flush DNS cache
  - Manage startup items

## Command Line Options

```bash
# Scan without cleaning
macos-cleaner --scan-only

# Auto mode - clean recommended items without prompts
macos-cleaner --auto

# Dry run - see what would be deleted
macos-cleaner --config dry_run_config.json
```

## Safety Tips

1. **First Time Users**: Run with `--scan-only` to see what would be cleaned
2. **Backup**: Enable backup in settings before first clean
3. **Review**: Always review the scan results before cleaning
4. **Start Small**: Begin with HIGH priority items only

## Common Use Cases

### Quick Daily Cleanup
```bash
mclean --auto
```

### Deep Monthly Clean
1. Run full scan (all categories)
2. Review large and old files
3. Clean selected categories
4. Empty trash
5. Optimize system

### Before System Update
1. Clean all caches
2. Remove temporary files
3. Empty trash
4. Purge memory

## Keyboard Shortcuts

- `q` - Quit/Back
- `a` - Select all
- `c` - Cancel operation
- Numbers `1-9` - Quick selection

## Getting Help

- In-app: Check the Settings menu for configuration options
- Documentation: See README.md for detailed information
- Issues: Report problems on GitHub

## Pro Tips

1. **Schedule Regular Scans**: Run weekly for optimal performance
2. **Check Startup Items**: Disable unnecessary apps from launching at startup
3. **Monitor Disk Space**: Use the system info panel to track usage
4. **Safe Mode**: Enable dry_run in config for testing

Happy Cleaning! 🧹✨