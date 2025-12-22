"""
Client and Matter folder structure importer.

Parses hierarchical folder structures:
  Clients/ClientName/MatterName/

Preserves exact folder names as display_name (no normalization).
"""
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class ImportedClient:
    """Client extracted from folder structure."""
    display_name: str      # Exact folder name
    folder_path: str       # Full path for reference


@dataclass
class ImportedMatter:
    """Matter extracted from folder structure."""
    client_display_name: str   # Parent folder name
    display_name: str          # This folder name
    folder_path: str           # Full path for reference


@dataclass
class ImportResult:
    """Result of folder import operation."""
    clients: List[ImportedClient]
    matters: List[ImportedMatter]
    root_path: str
    stats: dict  # {"clients": N, "matters": M}


EXCLUDED_FOLDERS = {
    '__pycache__', '.git', '.svn', '$RECYCLE.BIN',
    'System Volume Information', '.vscode', 'node_modules',
    'Desktop.ini', 'Thumbs.db'
}
MAX_DEPTH = 2  # Client > Matter


def import_from_folder(folder_path: str) -> ImportResult:
    """
    Import clients and matters from folder hierarchy.

    Folder structure:
        root/
            ClientA/
                Matter1/
                Matter2/
            ClientB/
                MatterX/

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
