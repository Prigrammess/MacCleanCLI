# 🔧 macOS Cleaner - Troubleshooting Guide

## Common Issues and Solutions

### 1. Browser Cache Not Found or Empty

**Problem**: Browser cache scan returns 0 files or shows "No accessible caches"

**Solutions**:

1. **Check Permissions**:
   ```bash
   # Grant Terminal/app full disk access
   System Preferences > Security & Privacy > Privacy > Full Disk Access
   # Add Terminal.app or iTerm2.app
   ```

2. **Browser-Specific Locations**:
   - **Chrome**: Cache might be in `~/Library/Application Support/Google/Chrome/Default/Cache`
   - **Firefox**: Look in `~/Library/Application Support/Firefox/Profiles/*/cache2`
   - **Brave**: Check `~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Cache`

3. **Manual Permission Fix**:
   ```bash
   # Check if you can access the cache directory
   ls -la ~/Library/Caches/
   
   # If permission denied, try:
   sudo chmod -R u+r ~/Library/Caches/
   ```

### 2. Cannot Disable Startup Items

**Problem**: "Cannot disable protected item" or "Failed to disable" errors

**Solutions**:

1. **VPN Services**: The app now supports common VPN services. For others:
   - Use the force disable option when prompted
   - Or manually disable in System Preferences > Users & Groups > Login Items

2. **System Integrity Protection (SIP)**:
   - Some system services cannot be disabled due to SIP
   - These are protected for system stability

3. **Manual Removal**:
   ```bash
   # List all launch agents
   ls -la ~/Library/LaunchAgents/
   ls -la /Library/LaunchAgents/
   
   # Remove specific service (example)
   launchctl unload ~/Library/LaunchAgents/com.example.service.plist
   rm ~/Library/LaunchAgents/com.example.service.plist
   ```

### 3. Permission Denied Errors

**Problem**: "Permission denied" when scanning or cleaning

**Solutions**:

1. **Run with sudo** (not recommended for regular use):
   ```bash
   sudo mac-cleaner
   ```

2. **Fix Permissions**:
   ```bash
   # Reset home directory permissions
   sudo chown -R $(whoami) ~
   chmod -R u+rwX ~
   ```

3. **Check System Integrity**:
   ```bash
   # Verify disk permissions
   diskutil verifyPermissions /
   ```

### 4. No Files Found During Scan

**Problem**: Scan completes but finds 0 files

**Possible Causes**:

1. **Already Clean**: Your system might already be clean
2. **Wrong Paths**: The app might be looking in wrong locations
3. **Hidden Files**: Try enabling hidden file scanning in settings

**Solutions**:
```bash
# Check if cache directories exist
ls -la ~/Library/Caches/
ls -la /var/folders/

# Manually check for large files
find ~ -type f -size +100M 2>/dev/null | head -20
```

### 5. Application Crashes or Freezes

**Problem**: App crashes during scan or clean

**Solutions**:

1. **Check Logs**:
   ```bash
   # View application logs
   cat ~/.mac-cleaner/logs/cleaner_*.log
   ```

2. **Clear Config**:
   ```bash
   # Reset to default configuration
   rm ~/.mac-cleaner/config.json
   mac-cleaner
   ```

3. **Reinstall**:
   ```bash
   pip uninstall mac-cleaner
   pip install --upgrade mac-cleaner
   ```

### 6. Memory Optimization Fails

**Problem**: "Failed to purge memory" error

**Solutions**:

1. **Requires Admin**:
   ```bash
   # Memory purge requires sudo
   sudo purge
   ```

2. **Alternative Method**:
   - Open Activity Monitor
   - View > Dock Icon > Show Memory Pressure
   - Close memory-intensive apps

### 7. Spotlight Rebuild Issues

**Problem**: Spotlight rebuild doesn't work or search is still slow

**Solutions**:

1. **Manual Rebuild**:
   ```bash
   # Stop Spotlight
   sudo mdutil -a -i off
   
   # Delete index
   sudo rm -rf /.Spotlight-V100
   
   # Restart Spotlight
   sudo mdutil -a -i on
   ```

2. **Check Status**:
   ```bash
   # View indexing status
   sudo mdutil -s /
   ```

## Debug Mode

Run with verbose logging for troubleshooting:

```bash
# Create debug config
cat > ~/.mac-cleaner/debug_config.json << EOF
{
  "dry_run": true,
  "verbose": true,
  "log_level": "DEBUG"
}
EOF

# Run with debug config
mac-cleaner --config ~/.mac-cleaner/debug_config.json --verbose
```

## Getting Help

1. **Check Logs**: `~/.mac-cleaner/logs/`
2. **GitHub Issues**: Report bugs with log files
3. **Safe Mode**: Always use `--dry-run` first
4. **Backup**: Enable backup option before cleaning

## Performance Tips

1. **First Scan**: Initial scan might be slow
2. **Exclude Folders**: Large external drives can slow scanning
3. **Regular Cleaning**: Weekly cleaning is faster than monthly
4. **Close Apps**: Close browsers before cleaning their cache

## Known Limitations

1. **SIP Protected Files**: Cannot clean System Integrity Protection files
2. **iCloud Files**: Downloaded iCloud files might reappear
3. **Active Files**: Cannot delete files in use
4. **Permissions**: Some system caches require admin access

## Emergency Recovery

If something goes wrong:

1. **Restore from Backup**:
   ```bash
   # List available backups
   ls -la ~/.mac-cleaner/backups/
   
   # Restore files manually
   cp -r ~/.mac-cleaner/backups/2024-01-01/* /original/location/
   ```

2. **Time Machine**: Use macOS Time Machine to restore
3. **Restart**: Many issues resolve after restart