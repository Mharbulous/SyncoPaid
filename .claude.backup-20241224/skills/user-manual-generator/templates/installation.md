# Template: Installation Guide

Use this template for creating installation documentation.

---

```markdown
# Installation

## Prerequisites

Before installing [Project Name], ensure you have:

- [Requirement 1] (version X.X or higher)
- [Requirement 2]
- [Operating System requirements]

## Installation Steps

### Windows

1. Download the installer from [link]
2. Run the installer
3. Follow the setup wizard
4. Verify installation:
   ```bash
   [command] --version
   ```

   You should see: `[Project Name] vX.X.X`

### macOS

[Installation steps for macOS]

### Linux

[Installation steps for Linux]

## Docker Installation (Optional)

For containerized deployment:

```bash
docker pull [image]
docker run -d -p [port]:[port] [image]
```

## Verify Installation

Test that everything works:

```bash
[test command]
```

Expected output:
```
[sample output]
```

## Next Steps

- [Quick Start Guide](quick-start.md) - Get up and running in 5 minutes
- [Configuration](../reference/configuration.md) - Customize your setup

## Troubleshooting

**Problem**: [Common installation issue]
**Solution**: [How to fix]
```

---

## Template Notes

- Include platform-specific instructions (Windows, macOS, Linux)
- Always show verification steps with expected output
- Link to quick start and configuration pages
- Include at least one common installation troubleshooting item
