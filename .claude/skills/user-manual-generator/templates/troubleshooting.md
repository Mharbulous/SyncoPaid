# Troubleshooting Guide

Solutions to common problems with [Project Name].

## Quick Diagnostic

Before diving into specific errors, try these general troubleshooting steps:

1. **Check version**: Ensure you're running the latest version
   ```bash
   [command] --version
   ```

2. **Verify installation**: Confirm all components are installed correctly
   ```bash
   [command] --health-check
   ```

3. **Review logs**: Check for error messages
   ```bash
   # View logs (Linux/macOS)
   tail -f ~/.config/[project]/logs/app.log

   # View logs (Windows)
   type %APPDATA%\[project]\logs\app.log
   ```

4. **Test with defaults**: Try running with minimal configuration
   ```bash
   [command] --use-defaults
   ```

If these don't help, see specific errors below.

## Common Error Messages

### Error: "Connection refused"

**Full error message**:
```
Error: connect ECONNREFUSED 127.0.0.1:8080
```

**Cause**: The application cannot connect to the required service (database, API, etc.).

**Solutions**:

#### Solution 1: Verify service is running

```bash
# Check if service is running
[service-check-command]

# Start the service if needed
[service-start-command]
```

#### Solution 2: Check configuration

Verify the host and port settings in your configuration:

```[format]
"host": "localhost",
"port": 8080
```

Make sure these match the actual service address.

#### Solution 3: Check firewall

Ensure your firewall isn't blocking the connection:

```bash
# Linux
sudo ufw status
sudo ufw allow [port]

# Windows
# Open Windows Defender Firewall with Advanced Security
# Create inbound rule for port [port]
```

### Error: "Permission denied"

**Full error message**:
```
Error: EACCES: permission denied, open '/path/to/file'
```

**Cause**: Insufficient permissions to access a file or directory.

**Solutions**:

#### Solution 1: Run with elevated privileges

**Linux/macOS**:
```bash
sudo [command]
```

**Windows**: Run Command Prompt or PowerShell as Administrator
1. Right-click Command Prompt
2. Select "Run as administrator"

#### Solution 2: Fix file permissions

```bash
# Linux/macOS
chmod +x /path/to/file         # Make executable
chmod 644 /path/to/file         # Read/write for owner, read for others
chown $USER:$USER /path/to/file # Take ownership

# Windows
# Right-click file > Properties > Security > Edit permissions
```

#### Solution 3: Change installation directory

Install to a directory where you have write access:

```bash
[command] --install-dir ~/[project]
```

### Error: "Module not found" or "Cannot find module"

**Full error message**:
```
Error: Cannot find module '[module-name]'
```

**Cause**: Missing dependencies or corrupt installation.

**Solutions**:

#### Solution 1: Reinstall dependencies

```bash
# Node.js projects
npm install

# Python projects
pip install -r requirements.txt

# Go projects
go mod download
```

#### Solution 2: Clear cache and reinstall

```bash
# Node.js
rm -rf node_modules package-lock.json
npm install

# Python
pip cache purge
pip install -r requirements.txt --no-cache-dir

# Go
go clean -modcache
go mod download
```

#### Solution 3: Verify installation

Check that all required packages are installed:

```bash
[command] --verify-dependencies
```

### Error: "Port already in use"

**Full error message**:
```
Error: listen EADDRINUSE: address already in use :::8080
```

**Cause**: Another process is using the configured port.

**Solutions**:

#### Solution 1: Find and stop the conflicting process

**Linux/macOS**:
```bash
# Find process using port 8080
lsof -i :8080

# Stop the process (replace PID with actual process ID)
kill [PID]

# Force stop if needed
kill -9 [PID]
```

**Windows**:
```bash
# Find process using port 8080
netstat -ano | findstr :8080

# Stop the process (replace PID with actual process ID)
taskkill /PID [PID] /F
```

#### Solution 2: Use a different port

Update your configuration to use an available port:

```[format]
"port": 3000
```

Or use command-line option:
```bash
[command] --port 3000
```

#### Solution 3: Check for stuck processes

```bash
# Kill all [project] processes
pkill -f [project-name]

# Or find manually
ps aux | grep [project-name]
kill [PID]
```

### Error: "Timeout" or "Request timeout"

**Full error message**:
```
Error: Request timeout after 30000ms
```

**Cause**: Operation took longer than the configured timeout.

**Solutions**:

#### Solution 1: Increase timeout

Update configuration:

```[format]
"timeout": 60000  # 60 seconds instead of 30
```

#### Solution 2: Check network connectivity

```bash
# Test connectivity
ping [hostname]

# Test specific port
telnet [hostname] [port]

# Or use curl
curl -I [url]
```

#### Solution 3: Optimize the operation

For large data transfers or complex operations:
- Process in smaller batches
- Enable compression
- Use pagination for large datasets

### Error: "Out of memory"

**Full error message**:
```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**Cause**: Application exceeded available memory.

**Solutions**:

#### Solution 1: Increase memory limit

**Node.js**:
```bash
node --max-old-space-size=4096 [script]  # 4GB
```

**Java**:
```bash
java -Xmx4g [arguments]  # 4GB
```

**Python**: Usually uses available system memory automatically

#### Solution 2: Process data in chunks

For large file processing:
- Use streaming instead of loading all at once
- Process in batches
- Enable pagination

#### Solution 3: Check for memory leaks

Monitor memory usage:
```bash
# Linux/macOS
top
htop

# Windows
Task Manager > Performance tab
```

If memory grows continuously, you may have a memory leak. Report this as a bug.

### Error: "Invalid JSON" or "Parse error"

**Full error message**:
```
SyntaxError: Unexpected token } in JSON at position 42
```

**Cause**: Malformed JSON in configuration file or API response.

**Solutions**:

#### Solution 1: Validate JSON syntax

Copy your JSON and paste into a validator:
- https://jsonlint.com/
- https://jsonformatter.org/

Common issues:
- Missing commas between properties
- Trailing commas (not allowed in JSON)
- Unquoted property names
- Single quotes instead of double quotes

#### Solution 2: Check for hidden characters

```bash
# View file with line endings visible
cat -A config.json

# Remove hidden characters
dos2unix config.json  # On Linux/macOS
```

#### Solution 3: Regenerate configuration

Backup and recreate the config file:
```bash
mv config.json config.json.bak
[command] --init-config
```

Then manually copy your custom settings back.

## Installation Issues

### Installation fails on Windows

**Symptoms**: Installer errors, missing dependencies, DLL errors

**Solutions**:

1. **Install Visual C++ Redistributable**:
   - Download from Microsoft: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Install and restart

2. **Run as Administrator**:
   - Right-click installer
   - Select "Run as administrator"

3. **Disable antivirus temporarily**:
   - Some antivirus software blocks installations
   - Disable, install, re-enable

4. **Check system requirements**:
   - Windows 10/11 64-bit
   - [Minimum RAM]
   - [Minimum disk space]

### Installation fails on macOS

**Symptoms**: "Unidentified developer" warning, installation blocked

**Solutions**:

1. **Allow app from unidentified developer**:
   ```bash
   sudo spctl --master-disable
   # Install the app
   sudo spctl --master-enable  # Re-enable after install
   ```

   Or: System Preferences > Security & Privacy > General > "Open Anyway"

2. **Remove quarantine flag**:
   ```bash
   xattr -d com.apple.quarantine /path/to/[app]
   ```

3. **Install Xcode Command Line Tools** (if building from source):
   ```bash
   xcode-select --install
   ```

### Installation fails on Linux

**Symptoms**: Dependency errors, package not found

**Solutions**:

1. **Update package lists**:
   ```bash
   sudo apt update  # Ubuntu/Debian
   sudo dnf update  # Fedora/RHEL
   sudo pacman -Sy  # Arch
   ```

2. **Install missing dependencies**:
   ```bash
   sudo apt install [dependency]
   ```

3. **Add required repositories**:
   Check documentation for any required third-party repositories

4. **Build from source**:
   ```bash
   git clone https://github.com/[username]/[repo].git
   cd [repo]
   ./configure
   make
   sudo make install
   ```

## Configuration Issues

### Configuration not taking effect

**Symptoms**: Changes to config file don't seem to apply

**Solutions**:

1. **Restart the application**:
   ```bash
   # Stop
   [stop-command]

   # Start
   [start-command]
   ```

2. **Verify config file location**:
   ```bash
   [command] --show-config-path
   ```

   Make sure you're editing the correct file.

3. **Check configuration priority**:
   - Command-line arguments override config file
   - Environment variables override config file
   - Remove conflicting overrides

4. **Validate configuration**:
   ```bash
   [command] --validate-config
   ```

### Environment variables not working

**Symptoms**: Environment variables don't override config

**Solutions**:

1. **Ensure variables are exported**:
   ```bash
   export PROJECT_VAR=value  # Correct
   # Not: PROJECT_VAR=value  # Incorrect (not exported)
   ```

2. **Check variable naming**:
   - Use correct prefix: `PROJECT_`
   - Use uppercase: `PROJECT_PORT`, not `project_port`

3. **Verify variables are set**:
   ```bash
   # Linux/macOS/Windows PowerShell
   echo $PROJECT_PORT

   # Windows Command Prompt
   echo %PROJECT_PORT%
   ```

4. **Reload shell**:
   ```bash
   source ~/.bashrc  # or ~/.zshrc, ~/.profile
   ```

## Performance Issues

### Application is slow

**Symptoms**: Slow response times, high latency

**Solutions**:

1. **Enable caching**:
   ```[format]
   "cacheEnabled": true,
   "cacheTtl": 3600
   ```

2. **Increase worker processes**:
   ```[format]
   "workers": 4  # Match your CPU cores
   ```

3. **Check resource usage**:
   ```bash
   # Linux/macOS
   top
   htop

   # Windows
   # Task Manager > Performance tab
   ```

4. **Enable compression**:
   ```[format]
   "compression": true
   ```

5. **Optimize database queries** (if applicable):
   - Add indexes
   - Use pagination
   - Limit result sets

### High CPU usage

**Symptoms**: CPU at 100%, system slowdown

**Solutions**:

1. **Reduce worker count**:
   ```[format]
   "workers": 2  # Lower than default
   ```

2. **Enable rate limiting**:
   ```[format]
   "rateLimit": {
     "enabled": true,
     "max": 100,
     "window": 60000
   }
   ```

3. **Check for infinite loops**:
   - Review application logs
   - Enable debug logging
   - Report if issue persists

4. **Update to latest version**:
   ```bash
   [update-command]
   ```

   Performance improvements are often included in updates.

## Data Issues

### Data not persisting

**Symptoms**: Settings reset, data lost after restart

**Solutions**:

1. **Check file permissions**:
   ```bash
   # Linux/macOS
   ls -la ~/.config/[project]/
   chmod 644 ~/.config/[project]/data.db

   # Windows
   # Verify you have write access to %APPDATA%\[project]
   ```

2. **Verify storage path**:
   ```bash
   [command] --show-data-path
   ```

3. **Check disk space**:
   ```bash
   df -h  # Linux/macOS
   # Windows: File Explorer > This PC
   ```

4. **Disable read-only mode** (if accidentally enabled):
   ```[format]
   "readOnly": false
   ```

### Data corruption

**Symptoms**: "Invalid data" errors, crashes on startup

**Solutions**:

1. **Restore from backup**:
   ```bash
   cp ~/.config/[project]/data.db.bak ~/.config/[project]/data.db
   ```

2. **Reset to defaults** (WARNING: loses data):
   ```bash
   [command] --reset
   ```

3. **Export data before reset**:
   ```bash
   [command] --export backup.json
   # Then reset and import
   [command] --import backup.json
   ```

4. **Contact support** with error logs

## Network Issues

### Cannot connect to API

**Symptoms**: API requests fail, network errors

**Solutions**:

1. **Check internet connectivity**:
   ```bash
   ping google.com
   curl -I https://api.[service].com
   ```

2. **Verify API endpoint**:
   ```[format]
   "apiEndpoint": "https://api.[service].com/v1"
   ```

3. **Check proxy settings** (if behind corporate proxy):
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

4. **Verify API key**:
   - Check key is valid
   - Ensure no extra spaces/characters
   - Regenerate if needed

### SSL/TLS errors

**Symptoms**: Certificate errors, SSL handshake failures

**Solutions**:

1. **Update CA certificates**:
   ```bash
   # Ubuntu/Debian
   sudo apt install ca-certificates
   sudo update-ca-certificates

   # macOS
   # Certificates update automatically with system updates

   # Windows
   # Download and install latest certificates
   ```

2. **Disable SSL verification** (development only, NOT production):
   ```[format]
   "verifySsl": false  # INSECURE - dev only
   ```

3. **Specify custom CA certificate**:
   ```[format]
   "caFile": "/path/to/ca-bundle.crt"
   ```

## Frequently Asked Questions (FAQ)

### General Questions

#### How do I update [Project Name]?

```bash
[update-command]
```

Or download the latest version from [download page].

#### How do I uninstall [Project Name]?

**Linux/macOS**:
```bash
sudo [uninstall-command]
# Remove configuration
rm -rf ~/.config/[project]
```

**Windows**:
- Control Panel > Programs > Uninstall a program
- Or: `[uninstall-command]`

**Remove data**:
```bash
# Windows
rmdir /s %APPDATA%\[project]
```

#### Where are my files stored?

- **Configuration**: `~/.config/[project]/` (Linux/macOS), `%APPDATA%\[project]` (Windows)
- **Data**: `~/.local/share/[project]/` (Linux/macOS), `%LOCALAPPDATA%\[project]` (Windows)
- **Logs**: `~/.config/[project]/logs/` (Linux/macOS), `%APPDATA%\[project]\logs` (Windows)

To see exact paths:
```bash
[command] --show-paths
```

#### Can I run multiple instances?

Yes, use different configuration files:

```bash
[command] --config /path/to/config1.json &
[command] --config /path/to/config2.json &
```

Ensure they use different ports to avoid conflicts.

#### How do I reset to factory defaults?

**WARNING**: This deletes all data and settings.

```bash
# Backup first
[command] --export backup.json

# Reset
[command] --reset
```

### Usage Questions

#### How do I [common task]?

See the [How-To Guides](../guides/common-tasks.md) section.

#### Why is [feature] not working?

1. Check you're using the latest version
2. Verify the feature is enabled in configuration
3. Check logs for errors
4. See relevant guide in documentation

#### Can I use this with [other tool]?

See the [Integrations Guide](../guides/integrations.md) for supported tools.

### Error-Specific Questions

#### What does error code [X] mean?

See the [Error Code Reference](../reference/error-codes.md) for all error codes and their meanings.

#### How do I enable debug logging?

```[format]
"logLevel": "debug"
```

Or via command-line:
```bash
[command] --log-level debug
```

Debug logs will show detailed information to help diagnose issues.

## Getting Help

If you've tried the solutions above and still need help:

### Before Asking for Help

Gather this information:

1. **Version**:
   ```bash
   [command] --version
   ```

2. **Operating System**:
   ```bash
   # Linux
   uname -a
   cat /etc/os-release

   # macOS
   sw_vers

   # Windows
   systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
   ```

3. **Error logs**:
   ```bash
   # Last 50 lines of logs
   tail -50 ~/.config/[project]/logs/app.log
   ```

4. **Configuration** (redact sensitive info like API keys):
   ```bash
   [command] --show-config
   ```

### How to Ask for Help

1. **GitHub Issues** (bugs and feature requests):
   - URL: https://github.com/[username]/[repo]/issues
   - Include: Version, OS, error message, steps to reproduce

2. **GitHub Discussions** (questions and general help):
   - URL: https://github.com/[username]/[repo]/discussions
   - Best for: "How do I...", "Why does...", "Can I..."

3. **Stack Overflow**:
   - Tag: `[project-tag]`
   - Search existing questions first

4. **Email Support**:
   - Email: support@[domain]
   - Include all information listed above

### Community

- **Discord**: [Invite link]
- **Twitter**: [@project]
- **Blog**: [Blog URL]

---

**Still stuck?** [Open an issue](https://github.com/[username]/[repo]/issues/new) and we'll help you troubleshoot.
