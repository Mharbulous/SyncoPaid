# 022B: Import Clients & Matters - Folder Parser Module
Story ID: 8.1.2

## Task
Create `client_matter_importer.py` module to extract client/matter data from folder structures.

## Context
Law firms organize files in hierarchical folders: `Clients/ClientName/MatterName/`. This module parses that structure and preserves the exact folder names the user already uses—no normalization or ID extraction needed.

**Design principle**: Use folder names exactly as-is for `display_name`.

## Scope
- New module: `src/syncopaid/client_matter_importer.py`
- Extract folder hierarchy (2 levels: Client > Matter)
- Return structured data with exact folder names

## Key Files

| File | Purpose |
|------|---------|
| `ai_docs/Matter-Import/2025-12-20-Listbot-high-level-import-guide.md` | Reference implementation (simplified—skip ID extraction) |
| `src/syncopaid/database_schema.py` | Target schema for imported data |

## Data Classes

```python
from dataclasses import dataclass
from typing import List
from pathlib import Path

@dataclass
class ImportedClient:
    display_name: str      # Exact folder name
    folder_path: str       # Full path for reference

@dataclass
class ImportedMatter:
    client_display_name: str   # Parent folder name
    display_name: str          # This folder name
    folder_path: str           # Full path for reference

@dataclass
class ImportResult:
    clients: List[ImportedClient]
    matters: List[ImportedMatter]
    root_path: str
    stats: dict  # {"clients": N, "matters": M}
```

## Key Functions

```python
EXCLUDED_FOLDERS = {
    '__pycache__', '.git', '.svn', '$RECYCLE.BIN',
    'System Volume Information', '.vscode', 'node_modules',
    'Desktop.ini', 'Thumbs.db'
}
MAX_DEPTH = 2  # Client > Matter

def import_from_folder(folder_path: str) -> ImportResult:
    """
    Main entry point.

    Args:
        folder_path: Root folder containing client subfolders

    Returns:
        ImportResult with clients (level 1) and matters (level 2)
    """
    root = Path(folder_path)
    clients = []
    matters = []

    for client_dir in sorted(root.iterdir()):
        if not client_dir.is_dir():
            continue
        if client_dir.name.startswith('.') or client_dir.name in EXCLUDED_FOLDERS:
            continue

        # Level 1 = Client
        client = ImportedClient(
            display_name=client_dir.name,
            folder_path=str(client_dir)
        )
        clients.append(client)

        # Level 2 = Matters under this client
        try:
            for matter_dir in sorted(client_dir.iterdir()):
                if not matter_dir.is_dir():
                    continue
                if matter_dir.name.startswith('.') or matter_dir.name in EXCLUDED_FOLDERS:
                    continue

                matter = ImportedMatter(
                    client_display_name=client_dir.name,
                    display_name=matter_dir.name,
                    folder_path=str(matter_dir)
                )
                matters.append(matter)
        except PermissionError:
            continue  # Skip inaccessible folders

    return ImportResult(
        clients=clients,
        matters=matters,
        root_path=str(root),
        stats={"clients": len(clients), "matters": len(matters)}
    )
```

## Simplification from Listbot

The Listbot guide includes ID extraction (parsing "C001" from "Smith, John (C001)").

**Skip this**—SyncoPaid uses exact folder names. If user named folder "Smith, John (C001)", that's the `display_name`. No parsing needed.

## Handling Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty folder | Return empty lists |
| No subfolders (flat) | Return clients only, no matters |
| Permission denied | Skip that folder, log warning |
| Hidden folders (`.name`) | Skip |
| System folders (`$RECYCLE.BIN`) | Skip |

## Module Testing

```python
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m syncopaid.client_matter_importer <folder_path>")
        sys.exit(1)

    result = import_from_folder(sys.argv[1])

    print(f"Root: {result.root_path}")
    print(f"Found {result.stats['clients']} clients, {result.stats['matters']} matters\n")

    print("Clients:")
    for c in result.clients:
        print(f"  - {c.display_name}")

    print("\nMatters:")
    for m in result.matters:
        print(f"  - {m.client_display_name} / {m.display_name}")
```

## Verification

```bash
venv\Scripts\activate

# Create test structure
mkdir -p /tmp/test_import/ClientA/Matter1
mkdir -p /tmp/test_import/ClientA/Matter2
mkdir -p /tmp/test_import/ClientB/MatterX

# Run
python -m syncopaid.client_matter_importer /tmp/test_import

# Expected output:
# Root: /tmp/test_import
# Found 2 clients, 3 matters
# Clients:
#   - ClientA
#   - ClientB
# Matters:
#   - ClientA / Matter1
#   - ClientA / Matter2
#   - ClientB / MatterX
```

## Dependencies
- Task 022A (database schema) should be complete first

## Next Task
After this: `022C_import-clients-matters-dialog-ui.md`
