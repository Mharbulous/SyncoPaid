# 046: Import Clients & Matters - Folder Parser Module

## Task
Create `client_matter_importer.py` module to extract client/matter data from folder structures.

## Context
Law firms organize files in hierarchical folders: `Clients/ClientName/MatterName/`. This module parses that structure deterministically (no AI) to extract client-matter relationships.

## Scope
- New module: `src/syncopaid/client_matter_importer.py`
- Extract folder hierarchy (2 levels: Client > Matter)
- Parse IDs from folder names like `Smith, John (C001)` or `C001 - Smith`
- Return structured data for database insertion

## Key Files

| File | Purpose |
|------|---------|
| `ai_docs/Matter-Import/2025-12-20-Listbot-high-level-import-guide.md` | Reference implementation (Python section at end) |
| `src/syncopaid/database_schema.py` | Target schema for imported data |

## Reference Algorithm

From the Listbot guide, the folder parser:
1. Traverses directory tree up to MAX_DEPTH=2 levels
2. Skips hidden folders and common excludes (`.git`, `__pycache__`, etc.)
3. Level 1 = clients, Level 2 = matters
4. Extracts IDs from name patterns

## Data Classes

```python
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class ImportedClient:
    client_name: str
    client_no: Optional[str] = None
    folder_path: str = ""
    confidence: str = "medium"

@dataclass
class ImportedMatter:
    client_name: str
    matter_name: str
    client_no: Optional[str] = None
    matter_no: Optional[str] = None
    folder_path: str = ""
    confidence: str = "medium"

@dataclass
class ImportResult:
    clients: List[ImportedClient]
    matters: List[ImportedMatter]
    stats: dict
```

## Key Functions

```python
EXCLUDED_FOLDERS = {
    '__pycache__', '.git', '.svn', '$RECYCLE.BIN',
    'System Volume Information', '.vscode', 'node_modules'
}
MAX_DEPTH = 2

def extract_id_from_name(name: str) -> Optional[str]:
    """
    Extract ID from folder name.
    Patterns:
      "Smith, John (C001)" → "C001"
      "C001 - Smith" → "C001"
      "2024-001 Real Estate" → "2024-001"
    """

def clean_name(name: str) -> str:
    """Remove ID patterns to get display name."""

def import_from_folder(folder_path: str) -> ImportResult:
    """Main entry point. Traverse folder, return clients/matters."""
```

## ID Extraction Patterns

The guide provides these regex patterns:
```python
# Parenthetical at end: "Smith, John (C001)"
r'\(([A-Z0-9-]+)\)\s*$'

# ID prefix: "C001 - Smith, John"
r'^([A-Z0-9-]+)\s*[-–]\s*'

# Numeric code: "2024-001"
r'^(\d{4}[-/]\d+)'
```

## Confidence Scoring

- `high`: Has both client_name and matter_name from folder structure
- `medium`: Has name but no ID extracted
- `low`: Missing key data

## Implementation Notes

- Use `pathlib.Path` for cross-platform paths
- Handle `PermissionError` gracefully (skip inaccessible folders)
- Sort results by path for consistent ordering
- Log progress for large imports

## Verification

```bash
venv\Scripts\activate

# Create test folders
mkdir -p /tmp/test_import/ClientA/Matter1
mkdir -p /tmp/test_import/ClientB/Matter2

# Run module directly
python -c "from syncopaid.client_matter_importer import import_from_folder; print(import_from_folder('/tmp/test_import'))"
```

## Dependencies
- Task 045 (database schema) should be complete first

## Next Task
After this: `047_import-clients-matters-dialog-ui.md`
