# Template: CLI Reference

Use this template for creating CLI command reference documentation.

---

```markdown
# CLI Reference

Complete reference for all [Project Name] commands.

## Global Options

These options work with all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help |
| `--version` | `-v` | Show version |
| `--config <file>` | `-c` | Use custom config file |
| `--verbose` | | Enable detailed output |
| `--quiet` | `-q` | Suppress non-error output |

## Commands

### `project init`

Initialize a new project.

**Usage**:
```bash
project init [options] [directory]
```

**Arguments**:

| Argument | Required | Description |
|----------|----------|-------------|
| `directory` | No | Target directory (default: current) |

**Options**:

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--template <name>` | `-t` | `basic` | Use a template (`basic`, `advanced`, `minimal`) |
| `--name <name>` | `-n` | | Project name |
| `--force` | `-f` | | Overwrite existing files |

**Examples**:

```bash
# Initialize in current directory
project init

# Initialize with template
project init --template advanced my-project

# Force overwrite
project init --force
```

**Output**:

```
✓ Created project structure
✓ Installed dependencies
✓ Initialized configuration

Project ready! Run 'project start' to begin.
```

### `project build`

Build the project for production.

**Usage**:
```bash
project build [options]
```

**Options**:

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output <dir>` | `-o` | `dist` | Output directory |
| `--minify` | | `true` | Minify output |
| `--sourcemap` | | `false` | Generate source maps |

**Examples**:

```bash
# Standard build
project build

# Build with source maps
project build --sourcemap

# Custom output directory
project build --output ./public
```

### `project serve`

Start development server.

**Usage**:
```bash
project serve [options]
```

**Options**:

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port <number>` | `-p` | `3000` | Server port |
| `--host <address>` | | `localhost` | Server host |
| `--open` | `-o` | | Open browser automatically |

**Examples**:

```bash
# Start on default port
project serve

# Start on custom port and open browser
project serve --port 8080 --open
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Configuration error |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_CONFIG` | Config file path | `./config.json` |
| `PROJECT_DEBUG` | Enable debug mode | `false` |
| `PROJECT_LOG_LEVEL` | Log verbosity | `info` |
```

---

## Template Notes

- List global options that apply to all commands
- Document every command with usage, arguments, options
- Include examples for each command
- Show expected output
- Include exit codes table
- Document relevant environment variables
