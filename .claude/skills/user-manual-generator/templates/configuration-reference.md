# Template: Configuration Reference

Use this template for creating configuration reference documentation.

---

```markdown
# Configuration Reference

Complete reference for all [Project Name] configuration options.

## Configuration File

[Project Name] looks for configuration in:

- **Linux/macOS**: `~/.config/[project]/config.json`
- **Windows**: `%APPDATA%\[project]\config.json`

## Configuration Format

```json
{
  "option1": "value",
  "option2": 123,
  "nested": {
    "suboption": true
  }
}
```

## Options

### `option1`

- **Type**: `string`
- **Default**: `"default-value"`
- **Required**: No

[Description of what this option does]

**Example**:
```json
"option1": "custom-value"
```

**Valid values**:
- `"value1"`: [What this means]
- `"value2"`: [What this means]

### `option2`

- **Type**: `number`
- **Default**: `100`
- **Required**: No

[Description of what this option does]

**Example**:
```json
"option2": 500
```

**Range**: 1 - 10000

### `nested.suboption`

- **Type**: `boolean`
- **Default**: `true`
- **Required**: No

[Description of what this nested option does]

## Environment Variables

Configuration can also be set via environment variables:

| Environment Variable | Config Option | Example |
|---------------------|---------------|---------|
| `PROJECT_OPTION1` | `option1` | `export PROJECT_OPTION1=value` |
| `PROJECT_OPTION2` | `option2` | `export PROJECT_OPTION2=500` |

## Examples

### Minimal Configuration

```json
{
  "option1": "value"
}
```

### Production Configuration

```json
{
  "option1": "production-value",
  "option2": 1000,
  "nested": {
    "suboption": false
  }
}
```

[Explain this configuration choice]
```

---

## Template Notes

- List all configuration options exhaustively
- Include type, default, and required for each option
- Show valid values or ranges
- Provide environment variable alternatives
- Include example configurations for common scenarios
