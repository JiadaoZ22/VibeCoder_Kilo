# Fix: Failed to obtain server version. Unable to check client-server compatibility.

## Problem
Error message: "Failed to obtain server version. Unable to check client-server compatibility. Set checkCompatibility=false to skip version check"

## Actual Root Cause
This warning comes from the **Qdrant vector database client** embedded within Kilo. When Kilo starts code indexing, it initializes a Qdrant client that tries to connect to a local Qdrant server (default: `http://localhost:6333`) to check version compatibility.

**This is NOT related to Kilo cloud connectivity (`app.kilo.ai`) - that was a misunderstanding.**

The Qdrant client has a `checkCompatibility` parameter that defaults to `true`, but Kilo doesn't expose this configuration option.

## IMPORTANT: What Does NOT Work
1. **`checkCompatibility: false` in kilo.json** - This is a Qdrant client parameter, not a Kilo config option. Kilo doesn't pass this to the Qdrant client internally.
2. **Changing API keys or base URLs** - Unrelated to this Qdrant client warning.
3. **Network fixes for `app.kilo.ai`** - The warning is about Qdrant (port 6333), not Kilo's cloud.

## Working Solutions

### Solution 1 (Recommended)
**Ignore the warning** - It does NOT affect Kilo functionality. Code indexing uses LanceDB (file-based vector DB) by default, not Qdrant. The Qdrant client initialization failure is harmless.

### Solution 2 (Disable Code Indexing)
If you want to completely eliminate the warning, disable code indexing in your `kilo.json`:

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "indexing": {
    "enabled": false
  }
}
```

This will disable all vector database initialization, including the Qdrant client check.

### Solution 3 (Run a Local Qdrant Server - Eliminate Warning)
If you want the warning gone AND keep indexing enabled, run a local Qdrant server:

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or using Qdrant binary (if installed)
qdrant
```

The Qdrant client will successfully connect and the warning will disappear.

### Solution 4 (Upgrade Kilo)
Newer versions of Kilo may have fixed this by either:
1. Disabling the Qdrant version check by default
2. Using only LanceDB without initializing Qdrant

```bash
# Check current version
kilo --version

# Upgrade Kilo to latest version
npm install -g @kilocode/cli

# Verify upgrade
kilo --version
```

## Related Issue: ENOSPC Error
If you also see "ENOSPC: no space left on device" errors, this is caused by inotify watcher limit being exceeded. Fix with:

```bash
# Kill all existing Kilo processes
pkill -f "kilo\|.kilo"

# Increase inotify watcher limit (until reboot)
sudo sysctl -w fs.inotify.max_user_watches=524288

# Make it permanent (survives reboot)
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Configuration Location
Global Kilo configuration: `~/.config/kilo/kilo.json` or `/home/<user>/.config/kilo/kilo.json`

Project-level configuration: `.kilo/kilo.json` in your project directory

## Kilo Version Tested
7.3.41

## Date
2026-06-10
