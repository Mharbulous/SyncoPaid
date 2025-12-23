# Configuration Reference

Complete reference for all [Project Name] configuration options.

## Configuration File Location

[Project Name] reads configuration from the following locations (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file**:
   - **Linux/macOS**: `~/.config/[project-name]/config.[ext]`
   - **Windows**: `%APPDATA%\[project-name]\config.[ext]`
4. **Default values** (lowest priority)

## Configuration File Format

[Project Name] uses [JSON/YAML/TOML/INI] format for configuration.

### Example Configuration

```[format]
{
  "option1": "value",
  "option2": 123,
  "nested": {
    "suboption": true
  }
}
```

### Minimal Configuration

```[format]
{
  "option1": "required-value"
}
```

All other options will use default values.

## Configuration Options

### General Settings

#### `option1`

- **Type**: `string`
- **Default**: `"default-value"`
- **Required**: Yes
- **Environment variable**: `PROJECT_OPTION1`

[Detailed description of what this option controls]

**Example**:
```[format]
"option1": "custom-value"
```

**Valid values**:
- `"value1"`: [What this means and when to use it]
- `"value2"`: [What this means and when to use it]
- `"value3"`: [What this means and when to use it]

**See also**: [Related option](#related-option)

#### `option2`

- **Type**: `number`
- **Default**: `100`
- **Required**: No
- **Environment variable**: `PROJECT_OPTION2`
- **Minimum**: `1`
- **Maximum**: `10000`

[Detailed description]

**Example**:
```[format]
"option2": 500
```

**Tip**: For most users, the default value works well. Only increase this if [specific condition].

**Warning**: Setting this too high may cause [potential issue].

### Network Settings

#### `host`

- **Type**: `string`
- **Default**: `"localhost"`
- **Required**: No
- **Environment variable**: `PROJECT_HOST`

The hostname or IP address to bind to.

**Examples**:
```[format]
"host": "localhost"        # Local access only
"host": "0.0.0.0"          # Accept from any interface
"host": "192.168.1.100"    # Specific IP
```

**Security note**: Using `0.0.0.0` exposes the service to all network interfaces. Only use in trusted networks.

#### `port`

- **Type**: `number`
- **Default**: `8080`
- **Required**: No
- **Environment variable**: `PROJECT_PORT`
- **Valid range**: `1024-65535`

The port number to listen on.

**Example**:
```[format]
"port": 3000
```

**Common ports**:
- `80`: HTTP (requires admin/root)
- `443`: HTTPS (requires admin/root)
- `3000`: Common development port
- `8080`: Common alternative HTTP port

#### `timeout`

- **Type**: `number` (milliseconds)
- **Default**: `30000` (30 seconds)
- **Required**: No
- **Environment variable**: `PROJECT_TIMEOUT`

Request timeout in milliseconds.

**Example**:
```[format]
"timeout": 60000  # 60 seconds
```

### Security Settings

#### `apiKey`

- **Type**: `string`
- **Default**: None
- **Required**: Yes (for production)
- **Environment variable**: `PROJECT_API_KEY`

API key for authentication.

**Example**:
```[format]
"apiKey": "your-secret-api-key-here"
```

**Security best practices**:
- Never commit API keys to version control
- Use environment variables in production
- Rotate keys periodically
- Use different keys for development and production

**Generating an API key**:
```bash
[command to generate key]
```

#### `enableSsl`

- **Type**: `boolean`
- **Default**: `false`
- **Required**: No
- **Environment variable**: `PROJECT_ENABLE_SSL`

Enable HTTPS/SSL connections.

**Example**:
```[format]
"enableSsl": true,
"sslCert": "/path/to/cert.pem",
"sslKey": "/path/to/key.pem"
```

**See also**: [sslCert](#sslcert), [sslKey](#sslkey)

### Logging Settings

#### `logLevel`

- **Type**: `string`
- **Default**: `"info"`
- **Required**: No
- **Environment variable**: `PROJECT_LOG_LEVEL`

Logging verbosity level.

**Valid values** (from least to most verbose):
- `"error"`: Only errors
- `"warn"`: Errors and warnings
- `"info"`: General information (recommended for production)
- `"debug"`: Detailed debugging information
- `"trace"`: Very detailed debugging

**Example**:
```[format]
"logLevel": "debug"
```

**Tip**: Use `"debug"` during development, `"info"` in production.

#### `logFile`

- **Type**: `string`
- **Default**: None (log to console)
- **Required**: No
- **Environment variable**: `PROJECT_LOG_FILE`

Path to log file. If not set, logs to stdout/stderr.

**Example**:
```[format]
"logFile": "/var/log/[project-name]/app.log"
```

**Permissions**: Ensure the application has write access to the log directory.

### Performance Settings

#### `workers`

- **Type**: `number`
- **Default**: CPU core count
- **Required**: No
- **Environment variable**: `PROJECT_WORKERS`

Number of worker processes/threads.

**Example**:
```[format]
"workers": 4
```

**Recommendations**:
- **Development**: 1 (easier debugging)
- **Production**: CPU cores or cores - 1
- **High traffic**: CPU cores × 2

#### `cacheEnabled`

- **Type**: `boolean`
- **Default**: `true`
- **Required**: No
- **Environment variable**: `PROJECT_CACHE_ENABLED`

Enable response caching.

**Example**:
```[format]
"cacheEnabled": true,
"cacheTtl": 3600
```

**See also**: [cacheTtl](#cachettl)

## Environment Variables

All configuration options can be set via environment variables using the `PROJECT_` prefix and uppercase names.

### Examples

```bash
# Linux/macOS
export PROJECT_HOST=0.0.0.0
export PROJECT_PORT=3000
export PROJECT_LOG_LEVEL=debug
[command]

# Windows (Command Prompt)
set PROJECT_HOST=0.0.0.0
set PROJECT_PORT=3000
[command]

# Windows (PowerShell)
$env:PROJECT_HOST="0.0.0.0"
$env:PROJECT_PORT=3000
[command]
```

### Using .env Files

Create a `.env` file in your project directory:

```bash
PROJECT_HOST=localhost
PROJECT_PORT=8080
PROJECT_API_KEY=your-secret-key
PROJECT_LOG_LEVEL=info
```

**Security**: Never commit `.env` files to version control! Add to `.gitignore`.

## Complete Configuration Examples

### Development Configuration

```[format]
{
  "host": "localhost",
  "port": 3000,
  "logLevel": "debug",
  "workers": 1,
  "enableSsl": false,
  "cacheEnabled": false
}
```

**Use when**: Local development, debugging

### Production Configuration

```[format]
{
  "host": "0.0.0.0",
  "port": 8080,
  "logLevel": "warn",
  "logFile": "/var/log/[project]/app.log",
  "workers": 4,
  "enableSsl": true,
  "sslCert": "/etc/ssl/certs/cert.pem",
  "sslKey": "/etc/ssl/private/key.pem",
  "apiKey": "${PROJECT_API_KEY}",  # From environment
  "cacheEnabled": true,
  "cacheTtl": 3600
}
```

**Use when**: Production deployment, high traffic

### Docker Configuration

```[format]
{
  "host": "0.0.0.0",
  "port": 8080,
  "logLevel": "info",
  "workers": 2
}
```

**Use with**: Docker containers, Kubernetes pods

## Validation

To validate your configuration:

```bash
[command] --validate-config
```

This will check:
- Syntax errors in config file
- Invalid option values
- Missing required options
- Port availability
- File permissions (SSL certs, log files)

## Configuration Priority

When the same option is set in multiple places, [Project Name] uses this priority order:

1. **Command-line arguments** (highest)
   ```bash
   [command] --port 9000
   ```

2. **Environment variables**
   ```bash
   export PROJECT_PORT=8000
   ```

3. **Configuration file**
   ```[format]
   "port": 3000
   ```

4. **Default values** (lowest)
   ```
   port = 8080 (built-in default)
   ```

### Example

Given:
- Config file: `"port": 3000`
- Environment: `PROJECT_PORT=8000`
- Command-line: `--port 9000`

The application will use port **9000**.

## Troubleshooting

### "Invalid configuration" Error

**Cause**: Syntax error in configuration file.

**Solution**:
1. Validate JSON/YAML/TOML syntax using an online validator
2. Check for missing commas, brackets, quotes
3. Run with `--validate-config` flag

### "Port already in use" Error

**Cause**: Another process is using the configured port.

**Solution**:
1. Change the port in configuration
2. Stop the conflicting process
3. Use a port-checking tool:
   ```bash
   # Linux/macOS
   lsof -i :[port]

   # Windows
   netstat -ano | findstr :[port]
   ```

### "Permission denied" for Log File

**Cause**: Application doesn't have write access to log directory.

**Solution**:
```bash
# Create log directory with correct permissions
sudo mkdir -p /var/log/[project]
sudo chown [user]:[group] /var/log/[project]
chmod 755 /var/log/[project]
```

### Environment Variables Not Working

**Cause**: Variables not exported or shell not reloaded.

**Solution**:
```bash
# Ensure variables are exported
export PROJECT_PORT=3000  # (not just: PROJECT_PORT=3000)

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc
```

## See Also

- [Getting Started Guide](../getting-started/installation.md) - Basic setup
- [Environment Variables Guide](../guides/environment-variables.md) - Advanced env var usage
- [Security Best Practices](../guides/security.md) - Securing your configuration
- [Docker Deployment](../guides/docker.md) - Configuration for containers

---

**Questions?** See the [FAQ](../troubleshooting/faq.md) or [ask in discussions](https://github.com/[username]/[repo]/discussions).
