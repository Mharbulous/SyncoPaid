# Client/Matter Import System - High-Level Guide

> **Purpose**: This document provides a comprehensive overview of the Listbot client/matter import system architecture, focusing on deterministic (non-AI) parsing and matching logic. Intended as a reference for building similar import tools in other environments (e.g., Python desktop applications).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Sources](#data-sources)
3. [Phase 1: Folder Structure Extraction](#phase-1-folder-structure-extraction)
4. [Phase 2: List File Parsing](#phase-2-list-file-parsing)
5. [Phase 3: Cross-Reference Matching](#phase-3-cross-reference-matching)
6. [Data Structures](#data-structures)
7. [Algorithms Reference](#algorithms-reference)
8. [Python Implementation Guide](#python-implementation-guide)

---

## Architecture Overview

The import system uses a **three-phase pipeline** to extract and reconcile client/matter data from two independent sources:

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   PHASE 1: Folders  │     │   PHASE 2: Lists    │     │  PHASE 3: Cross-Ref │
│   (Directory Tree)  │ ──► │   (Excel/CSV)       │ ──► │   (Match & Merge)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
   Deterministic                Deterministic                Deterministic
   tree traversal               spreadsheet parse            matching algorithm
```

### Key Design Principles

1. **Two-Source Validation**: Matters confirmed by both folder structure AND list data have higher confidence
2. **Incremental Processing**: Large datasets are processed in batches to manage memory
3. **Confidence Scoring**: Each extracted matter receives a confidence rating based on data completeness
4. **Merge Strategy**: When combining data from both sources, prefer list data for IDs and folder data for paths

---

## Data Sources

### Source 1: Folder Structure

Law firms typically organize files in hierarchical folder structures:

```
Clients/
├── Smith, John (C001)/
│   ├── Real Estate Purchase (M001)/
│   │   └── [documents...]
│   └── Divorce Proceedings (M002)/
│       └── [documents...]
├── Johnson Corp (C002)/
│   └── Contract Dispute (M003)/
│       └── [documents...]
```

**Hierarchy Patterns Detected**:
- `Client > Matter`
- `Year > Client > Matter`
- `Client > Year > Matter`
- Custom variations

### Source 2: List Files (Excel/CSV)

Spreadsheets containing client/matter data with columns like:

| Client Name | Client # | Matter Description | File # |
|-------------|----------|-------------------|--------|
| Smith, John | C001 | Real Estate Purchase | M001 |
| Smith, John | C001 | Divorce Proceedings | M002 |
| Johnson Corp | C002 | Contract Dispute | M003 |

---

## Phase 1: Folder Structure Extraction

### Overview

Extracts folder hierarchy and infers client/matter relationships from directory names.

### Algorithm: Folder Tree Building

```javascript
// Constants
const EXCLUDED_FOLDERS = new Set([
  'node_modules', '__pycache__', '.git', '.svn', '.hg',
  '.DS_Store', 'Thumbs.db', '$RECYCLE.BIN',
  'System Volume Information', '.vscode', '.idea',
  'target', 'build', 'dist', '.cache'
])

const MAX_DEPTH = 2  // Only analyze top 2 levels (Client > Matter)

/**
 * Extract folder structure from file paths in a single pass.
 * Performance: O(n * d) where n = file count, d = average path depth
 */
function extractFolderStructure(files) {
  const folderMap = new Map()
  const processedFileDirs = new Set()
  let lastFileDir = ''

  // Statistics
  let maxLevel = 0
  let potentialClients = 0
  let potentialMatters = 0

  for (const file of files) {
    const fullPath = file.relativePath

    // Extract directory path (everything before last slash)
    const lastSlashIndex = fullPath.lastIndexOf('/')
    const fileDir = fullPath.slice(0, lastSlashIndex)

    // Skip if same directory as last file (optimization)
    if (fileDir === lastFileDir) continue

    // Skip if already processed
    if (processedFileDirs.has(fileDir)) {
      lastFileDir = fileDir
      continue
    }

    processedFileDirs.add(fileDir)
    lastFileDir = fileDir

    const parts = fullPath.split('/')

    // Build folder paths (exclude filename)
    for (let i = 1; i < parts.length - 1 && i < MAX_DEPTH; i++) {
      const folderName = parts[i]

      // Skip hidden and excluded folders
      if (folderName.startsWith('.') || EXCLUDED_FOLDERS.has(folderName)) {
        break
      }

      const folderPath = parts.slice(0, i + 1).join('/')

      if (!folderMap.has(folderPath)) {
        const level = i
        const parentPath = parts.slice(1, i).join('/')
        const relativePath = parts.slice(1, i + 1).join('/')

        folderMap.set(folderPath, {
          path: relativePath,
          name: folderName,
          level: level,
          parentPath: parentPath
        })

        // Gather statistics
        maxLevel = Math.max(maxLevel, level)
        if (level === 1) potentialClients++
        if (level === 2 || level === 3) potentialMatters++
      }
    }
  }

  return {
    flatList: Array.from(folderMap.values()).sort((a, b) =>
      a.path.localeCompare(b.path)
    ),
    stats: {
      totalFolders: folderMap.size,
      levelsDetected: maxLevel,
      potentialClients,
      potentialMatters
    }
  }
}
```

### Algorithm: Build Tree from Flat List

```javascript
/**
 * Build tree from flat array in O(n) using Map for parent lookup.
 */
function buildTreeFromFlat(flatList, rootName) {
  const root = {
    name: rootName,
    level: 0,
    children: [],
    path: ''
  }

  const nodeMap = new Map()
  nodeMap.set('', root)

  for (const item of flatList) {
    const node = {
      name: item.name,
      level: item.level,
      children: [],
      path: item.path
    }

    nodeMap.set(item.path, node)

    const parent = nodeMap.get(item.parentPath)
    if (parent) {
      parent.children.push(node)
    }
  }

  return root
}
```

### Folder Data Structure

```typescript
interface FolderItem {
  path: string        // "Smith, John/Real Estate Purchase"
  name: string        // "Real Estate Purchase"
  level: number       // 1 = client level, 2 = matter level
  parentPath: string  // "Smith, John"
}

interface FolderStats {
  totalFolders: number
  levelsDetected: number
  potentialClients: number
  potentialMatters: number
}
```

---

## Phase 2: List File Parsing

### Overview

Parses Excel/CSV files to extract client/matter data from tabular format.

### Algorithm: Excel/CSV Parsing

```javascript
/**
 * Load and parse spreadsheet file.
 * Returns headers and rows as objects.
 */
function parseSpreadsheet(fileBuffer) {
  // Use a library like xlsx (JavaScript) or openpyxl (Python)
  const workbook = XLSX.read(fileBuffer, { type: 'array' })

  // Get first sheet
  const firstSheetName = workbook.SheetNames[0]
  const worksheet = workbook.Sheets[firstSheetName]

  // Convert to JSON with headers
  const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

  if (jsonData.length < 2) {
    return null  // Need at least header + 1 data row
  }

  // First row is headers
  const headers = jsonData[0].map(h => String(h || '').trim())

  // Convert rows to objects
  const rows = jsonData.slice(1).map(row => {
    const obj = {}
    headers.forEach((header, idx) => {
      obj[header] = row[idx] !== undefined ? String(row[idx]) : ''
    })
    return obj
  })

  // Filter out completely empty rows
  const validRows = rows.filter(row =>
    Object.values(row).some(v => v && v.trim())
  )

  return {
    headers,
    rows: validRows
  }
}
```

### Column Detection Heuristics

When AI is not available, use pattern matching to detect columns:

```javascript
/**
 * Detect which columns contain client/matter data.
 * Uses common naming patterns.
 */
function detectColumns(headers) {
  const patterns = {
    clientName: [
      /^client\s*name$/i,
      /^client$/i,
      /^customer$/i,
      /^party$/i
    ],
    matterName: [
      /^matter\s*name$/i,
      /^matter$/i,
      /^case$/i,
      /^file\s*name$/i,
      /^description$/i
    ],
    clientNo: [
      /^client\s*(no|number|#|id)$/i,
      /^customer\s*(no|number|#|id)$/i
    ],
    matterNo: [
      /^matter\s*(no|number|#|id)$/i,
      /^case\s*(no|number|#|id)$/i,
      /^file\s*(no|number|#|id)$/i,
      /^docket$/i
    ]
  }

  const detected = {
    clientName: null,
    matterName: null,
    clientNo: null,
    matterNo: null
  }

  for (const header of headers) {
    for (const [field, fieldPatterns] of Object.entries(patterns)) {
      if (detected[field]) continue  // Already found

      for (const pattern of fieldPatterns) {
        if (pattern.test(header)) {
          detected[field] = header
          break
        }
      }
    }
  }

  return detected
}

/**
 * Extract matters from parsed spreadsheet data.
 */
function extractMattersFromList(parsedData, detectedColumns) {
  const { rows } = parsedData
  const matters = []
  const seen = new Set()  // For deduplication

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]

    const clientName = detectedColumns.clientName
      ? row[detectedColumns.clientName]?.trim()
      : ''
    const matterName = detectedColumns.matterName
      ? row[detectedColumns.matterName]?.trim()
      : ''
    const clientNo = detectedColumns.clientNo
      ? row[detectedColumns.clientNo]?.trim()
      : ''
    const matterNo = detectedColumns.matterNo
      ? row[detectedColumns.matterNo]?.trim()
      : ''

    // Skip if no identifying information
    if (!clientName && !matterName) continue

    // Deduplication key
    const key = `${clientName}|${matterName}|${clientNo}|${matterNo}`
    if (seen.has(key)) continue
    seen.add(key)

    matters.push({
      id: `list-${i + 1}`,
      clientName,
      matterName,
      clientNo,
      matterNo,
      rowSource: `row${i + 2}`,  // +2 for header row and 1-indexing
      matchSource: 'list-only',
      selected: false,
      confidence: (clientNo && matterNo) ? 'medium' : 'low'
    })
  }

  return matters
}
```

---

## Phase 3: Cross-Reference Matching

### Overview

This is the core deterministic algorithm that matches matters from folders with matters from lists.

### Matching Strategy

1. **Phase 3A - Exact Number Matching**: Match by normalized `clientNo + matterNo`
2. **Phase 3B - Fuzzy Name Matching**: For unmatched items, compare normalized names

### Complete Cross-Reference Algorithm

```javascript
/**
 * Cross-reference matters from folders and lists.
 * Matching is done primarily on clientNo + matterNo,
 * with fallback to name matching.
 */
function crossReference(folderMatters, listMatters) {
  const confirmed = []
  const preliminary = []
  const matchedFolderIds = new Set()
  const matchedListIds = new Set()

  // ========================================
  // PHASE 3A: Match by clientNo + matterNo (exact match)
  // ========================================
  for (const folderMatter of folderMatters) {
    if (!folderMatter.clientNo || !folderMatter.matterNo) continue

    const matchKey = createMatchKey(folderMatter.clientNo, folderMatter.matterNo)

    for (const listMatter of listMatters) {
      if (matchedListIds.has(listMatter.id)) continue
      if (!listMatter.clientNo || !listMatter.matterNo) continue

      const listMatchKey = createMatchKey(listMatter.clientNo, listMatter.matterNo)

      if (matchKey === listMatchKey) {
        // Exact match found - create confirmed matter
        confirmed.push(mergeMatters(folderMatter, listMatter, 'exact'))
        matchedFolderIds.add(folderMatter.id)
        matchedListIds.add(listMatter.id)
        break
      }
    }
  }

  // ========================================
  // PHASE 3B: Fuzzy match by name for remaining matters
  // ========================================
  for (const folderMatter of folderMatters) {
    if (matchedFolderIds.has(folderMatter.id)) continue

    const folderKey = createNameKey(folderMatter.clientName, folderMatter.matterName)

    for (const listMatter of listMatters) {
      if (matchedListIds.has(listMatter.id)) continue

      const listKey = createNameKey(listMatter.clientName, listMatter.matterName)

      if (fuzzyNameMatch(folderKey, listKey)) {
        confirmed.push(mergeMatters(folderMatter, listMatter, 'fuzzy'))
        matchedFolderIds.add(folderMatter.id)
        matchedListIds.add(listMatter.id)
        break
      }
    }
  }

  // ========================================
  // Add unmatched to preliminary
  // ========================================
  for (const folderMatter of folderMatters) {
    if (matchedFolderIds.has(folderMatter.id)) continue

    preliminary.push({
      ...folderMatter,
      matchSource: 'folder-only',
      selected: false,
      confidence: 'low'
    })
  }

  for (const listMatter of listMatters) {
    if (matchedListIds.has(listMatter.id)) continue

    preliminary.push({
      ...listMatter,
      matchSource: 'list-only',
      selected: false,
      confidence: 'low'
    })
  }

  // Generate unique IDs
  const allMatters = [
    ...confirmed.map((m, i) => ({ ...m, id: `confirmed-${i + 1}` })),
    ...preliminary.map((m, i) => ({ ...m, id: `preliminary-${i + 1}` }))
  ]

  return {
    matters: allMatters,
    confirmed,
    preliminary,
    stats: {
      totalFolderMatters: folderMatters.length,
      totalListMatters: listMatters.length,
      exactMatches: confirmed.filter(m => m.matchType === 'exact').length,
      fuzzyMatches: confirmed.filter(m => m.matchType === 'fuzzy').length,
      confirmedCount: confirmed.length,
      preliminaryCount: preliminary.length,
      folderOnlyCount: preliminary.filter(m => m.matchSource === 'folder-only').length,
      listOnlyCount: preliminary.filter(m => m.matchSource === 'list-only').length
    }
  }
}
```

### Helper Functions

```javascript
/**
 * Create a normalized key from clientNo + matterNo for exact matching.
 * Removes all non-alphanumeric characters and lowercases.
 *
 * Examples:
 *   "C-001" + "M-001" → "c001:m001"
 *   "2024/001" + "0001" → "2024001:0001"
 */
function createMatchKey(clientNo, matterNo) {
  const normalizedClientNo = String(clientNo || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
  const normalizedMatterNo = String(matterNo || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')

  return `${normalizedClientNo}:${normalizedMatterNo}`
}

/**
 * Create a normalized key from names for fuzzy matching.
 */
function createNameKey(clientName, matterName) {
  const normalizedClient = String(clientName || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
  const normalizedMatter = String(matterName || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')

  return `${normalizedClient}:${normalizedMatter}`
}

/**
 * Check if two name keys match with fuzzy tolerance.
 */
function fuzzyNameMatch(key1, key2) {
  // Exact match after normalization
  if (key1 === key2) return true

  // Both empty is not a match
  if (!key1 || !key2) return false

  // For longer strings, check containment and similarity
  if (key1.length > 10 && key2.length > 10) {
    const shorter = key1.length < key2.length ? key1 : key2
    const longer = key1.length < key2.length ? key2 : key1

    // Substring containment
    if (longer.includes(shorter)) return true

    // Similarity threshold (80%)
    const similarity = calculateSimilarity(key1, key2)
    if (similarity > 0.8) return true
  }

  return false
}

/**
 * Calculate similarity between two strings (0-1).
 * Uses Jaccard similarity on character sets.
 */
function calculateSimilarity(str1, str2) {
  if (str1 === str2) return 1
  if (!str1 || !str2) return 0

  const set1 = new Set(str1.split(''))
  const set2 = new Set(str2.split(''))

  const intersection = new Set([...set1].filter(x => set2.has(x)))
  const union = new Set([...set1, ...set2])

  return intersection.size / union.size
}

/**
 * Merge a folder matter and list matter into a confirmed matter.
 *
 * Merge Strategy:
 * - Prefer folder data for names (more accurate from file system)
 * - Prefer list data for numbers (official IDs from records)
 */
function mergeMatters(folderMatter, listMatter, matchType) {
  return {
    id: `matched-${folderMatter.id}-${listMatter.id}`,
    clientName: folderMatter.clientName || listMatter.clientName,
    matterName: folderMatter.matterName || listMatter.matterName,
    clientNo: listMatter.clientNo || folderMatter.clientNo,  // Prefer list
    matterNo: listMatter.matterNo || folderMatter.matterNo,  // Prefer list
    matchSource: 'both',
    matchType,
    folderMatch: folderMatter.folderPath || folderMatter.path,
    listMatch: listMatter.rowSource,
    selected: true,  // Auto-selected for confirmed matters
    confidence: matchType === 'exact' ? 'high' : 'medium'
  }
}
```

---

## Data Structures

### Matter Object

```typescript
interface Matter {
  id: string              // Unique identifier
  clientName: string      // "Smith, John"
  matterName: string      // "Real Estate Purchase"
  clientNo: string | null // "C001"
  matterNo: string | null // "M001"

  // Source tracking
  matchSource: 'folder-only' | 'list-only' | 'both'
  matchType?: 'exact' | 'fuzzy'  // Only for confirmed matches
  folderMatch?: string    // Original folder path
  listMatch?: string      // Original row source

  // Selection state
  selected: boolean
  confidence: 'high' | 'medium' | 'low'
}
```

### Result Categories

| Category | Source | Auto-Selected | Confidence |
|----------|--------|---------------|------------|
| Confirmed (exact) | Both | Yes | High |
| Confirmed (fuzzy) | Both | Yes | Medium |
| Preliminary (folder-only) | Folder | No | Low |
| Preliminary (list-only) | List | No | Low |

---

## Algorithms Reference

### Normalization Function

Used throughout for consistent string comparison:

```python
def normalize(value: str) -> str:
    """
    Remove all non-alphanumeric characters and lowercase.

    Examples:
        "C-001" → "c001"
        "Smith, John" → "smithjohn"
        "Matter #A" → "mattera"
        "2024/001-0001" → "202400010001"
    """
    import re
    return re.sub(r'[^a-z0-9]', '', value.lower())
```

### Confidence Scoring Rules

```python
def calculate_confidence(matter: dict) -> str:
    """
    Determine confidence level based on data completeness.
    """
    has_client_name = bool(matter.get('clientName'))
    has_matter_name = bool(matter.get('matterName'))
    has_client_no = bool(matter.get('clientNo'))
    has_matter_no = bool(matter.get('matterNo'))
    has_folder_path = bool(matter.get('folderPath'))

    # From folder extraction
    if has_client_name and has_matter_name and has_folder_path:
        return 'high'

    # From list extraction
    if has_client_no and has_matter_no:
        return 'medium'

    return 'low'
```

---

## Python Implementation Guide

### Complete Python Example

```python
"""
Client/Matter Import System - Python Implementation
Deterministic extraction and matching without AI dependency.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import openpyxl  # For Excel files
import csv       # For CSV files


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Matter:
    id: str
    client_name: str = ""
    matter_name: str = ""
    client_no: Optional[str] = None
    matter_no: Optional[str] = None
    match_source: str = "unknown"  # 'folder-only', 'list-only', 'both'
    match_type: Optional[str] = None  # 'exact', 'fuzzy'
    folder_path: Optional[str] = None
    row_source: Optional[str] = None
    selected: bool = False
    confidence: str = "low"  # 'high', 'medium', 'low'


@dataclass
class FolderStats:
    total_folders: int = 0
    levels_detected: int = 0
    potential_clients: int = 0
    potential_matters: int = 0


@dataclass
class CrossReferenceStats:
    total_folder_matters: int = 0
    total_list_matters: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    confirmed_count: int = 0
    preliminary_count: int = 0
    folder_only_count: int = 0
    list_only_count: int = 0


# =============================================================================
# CONSTANTS
# =============================================================================

EXCLUDED_FOLDERS = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg',
    '.DS_Store', 'Thumbs.db', '$RECYCLE.BIN',
    'System Volume Information', '.vscode', '.idea',
    'target', 'build', 'dist', '.cache', '__MACOSX'
}

MAX_DEPTH = 2  # Client > Matter


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def normalize(value: str) -> str:
    """Remove non-alphanumeric characters and lowercase."""
    if not value:
        return ""
    return re.sub(r'[^a-z0-9]', '', value.lower())


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate Jaccard similarity between two strings."""
    if str1 == str2:
        return 1.0
    if not str1 or not str2:
        return 0.0

    set1 = set(str1)
    set2 = set(str2)

    intersection = set1 & set2
    union = set1 | set2

    return len(intersection) / len(union) if union else 0.0


# =============================================================================
# PHASE 1: FOLDER EXTRACTION
# =============================================================================

def extract_folder_structure(root_path: str) -> Tuple[List[Dict], str, FolderStats]:
    """
    Extract folder hierarchy from filesystem.

    Args:
        root_path: Path to root directory

    Returns:
        Tuple of (flat_list, root_name, stats)
    """
    root = Path(root_path)
    root_name = root.name

    folders = []
    stats = FolderStats()

    def traverse(path: Path, level: int, parent_path: str):
        if level >= MAX_DEPTH:
            return

        try:
            entries = sorted(path.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if not entry.is_dir():
                continue

            name = entry.name

            # Skip hidden and excluded
            if name.startswith('.') or name in EXCLUDED_FOLDERS:
                continue

            relative_path = str(entry.relative_to(root))
            current_level = level + 1

            folders.append({
                'path': relative_path,
                'name': name,
                'level': current_level,
                'parent_path': parent_path
            })

            # Update stats
            stats.total_folders += 1
            stats.levels_detected = max(stats.levels_detected, current_level)

            if current_level == 1:
                stats.potential_clients += 1
            if current_level in (2, 3):
                stats.potential_matters += 1

            # Recurse
            traverse(entry, current_level, relative_path)

    traverse(root, 0, "")

    return folders, root_name, stats


def folders_to_matters(folders: List[Dict]) -> List[Matter]:
    """
    Convert folder structure to matter objects.
    Assumes Client > Matter hierarchy.
    """
    matters = []

    # Group by client (level 1)
    clients = {}
    for folder in folders:
        if folder['level'] == 1:
            clients[folder['path']] = folder['name']

    # Find matters (level 2) and associate with clients
    for folder in folders:
        if folder['level'] == 2:
            client_path = folder['parent_path']
            client_name = clients.get(client_path, "")

            # Try to extract IDs from names
            client_no = extract_id_from_name(client_name)
            matter_no = extract_id_from_name(folder['name'])

            matter = Matter(
                id=f"folder-{len(matters) + 1}",
                client_name=clean_name(client_name),
                matter_name=clean_name(folder['name']),
                client_no=client_no,
                matter_no=matter_no,
                match_source='folder-only',
                folder_path=folder['path'],
                confidence='high' if client_name and folder['name'] else 'low'
            )
            matters.append(matter)

    return matters


def extract_id_from_name(name: str) -> Optional[str]:
    """
    Extract ID from folder/matter name.

    Examples:
        "Smith, John (C001)" → "C001"
        "C001 - Smith, John" → "C001"
        "2024-001 Real Estate" → "2024-001"
    """
    if not name:
        return None

    # Pattern: parenthetical ID at end
    match = re.search(r'\(([A-Z0-9-]+)\)\s*$', name)
    if match:
        return match.group(1)

    # Pattern: ID at start followed by dash/space
    match = re.match(r'^([A-Z0-9-]+)\s*[-–]\s*', name)
    if match:
        return match.group(1)

    # Pattern: just a number code
    match = re.match(r'^(\d{4}[-/]\d+)', name)
    if match:
        return match.group(1)

    return None


def clean_name(name: str) -> str:
    """Remove ID patterns from name to get clean display name."""
    if not name:
        return ""

    # Remove parenthetical ID at end
    name = re.sub(r'\s*\([A-Z0-9-]+\)\s*$', '', name)

    # Remove ID prefix
    name = re.sub(r'^[A-Z0-9-]+\s*[-–]\s*', '', name)

    return name.strip()


# =============================================================================
# PHASE 2: LIST PARSING
# =============================================================================

def parse_excel(file_path: str) -> Tuple[List[str], List[Dict]]:
    """Parse Excel file and return headers and rows."""
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))

    if len(rows) < 2:
        return [], []

    headers = [str(h or '').strip() for h in rows[0]]

    data_rows = []
    for row in rows[1:]:
        row_dict = {}
        for i, header in enumerate(headers):
            value = row[i] if i < len(row) else None
            row_dict[header] = str(value) if value is not None else ''

        # Skip empty rows
        if any(v.strip() for v in row_dict.values()):
            data_rows.append(row_dict)

    return headers, data_rows


def parse_csv(file_path: str) -> Tuple[List[str], List[Dict]]:
    """Parse CSV file and return headers and rows."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = [row for row in reader if any(v.strip() for v in row.values())]

    return headers, rows


def detect_columns(headers: List[str]) -> Dict[str, Optional[str]]:
    """Detect which columns contain client/matter data."""
    patterns = {
        'client_name': [
            r'^client\s*name$', r'^client$', r'^customer$', r'^party$'
        ],
        'matter_name': [
            r'^matter\s*name$', r'^matter$', r'^case$',
            r'^file\s*name$', r'^description$'
        ],
        'client_no': [
            r'^client\s*(no|number|#|id)$', r'^customer\s*(no|number|#|id)$'
        ],
        'matter_no': [
            r'^matter\s*(no|number|#|id)$', r'^case\s*(no|number|#|id)$',
            r'^file\s*(no|number|#|id)$', r'^docket$'
        ]
    }

    detected = {k: None for k in patterns}

    for header in headers:
        header_lower = header.lower().strip()
        for field, field_patterns in patterns.items():
            if detected[field]:
                continue
            for pattern in field_patterns:
                if re.match(pattern, header_lower, re.IGNORECASE):
                    detected[field] = header
                    break

    return detected


def extract_matters_from_list(
    rows: List[Dict],
    columns: Dict[str, Optional[str]],
    source_file: str
) -> List[Matter]:
    """Extract matters from parsed list data."""
    matters = []
    seen = set()

    for i, row in enumerate(rows):
        client_name = row.get(columns['client_name'] or '', '').strip()
        matter_name = row.get(columns['matter_name'] or '', '').strip()
        client_no = row.get(columns['client_no'] or '', '').strip() or None
        matter_no = row.get(columns['matter_no'] or '', '').strip() or None

        if not client_name and not matter_name:
            continue

        # Deduplication
        key = f"{client_name}|{matter_name}|{client_no}|{matter_no}"
        if key in seen:
            continue
        seen.add(key)

        confidence = 'medium' if (client_no and matter_no) else 'low'

        matter = Matter(
            id=f"list-{len(matters) + 1}",
            client_name=client_name,
            matter_name=matter_name,
            client_no=client_no,
            matter_no=matter_no,
            match_source='list-only',
            row_source=f"{source_file}:row{i + 2}",
            confidence=confidence
        )
        matters.append(matter)

    return matters


# =============================================================================
# PHASE 3: CROSS-REFERENCE MATCHING
# =============================================================================

def cross_reference(
    folder_matters: List[Matter],
    list_matters: List[Matter]
) -> Tuple[List[Matter], List[Matter], CrossReferenceStats]:
    """
    Cross-reference matters from folders and lists.

    Returns:
        Tuple of (confirmed, preliminary, stats)
    """
    confirmed = []
    preliminary = []
    matched_folder_ids: Set[str] = set()
    matched_list_ids: Set[str] = set()

    # Phase 3A: Exact match by clientNo + matterNo
    for fm in folder_matters:
        if not fm.client_no or not fm.matter_no:
            continue

        folder_key = f"{normalize(fm.client_no)}:{normalize(fm.matter_no)}"

        for lm in list_matters:
            if lm.id in matched_list_ids:
                continue
            if not lm.client_no or not lm.matter_no:
                continue

            list_key = f"{normalize(lm.client_no)}:{normalize(lm.matter_no)}"

            if folder_key == list_key:
                confirmed.append(merge_matters(fm, lm, 'exact'))
                matched_folder_ids.add(fm.id)
                matched_list_ids.add(lm.id)
                break

    # Phase 3B: Fuzzy match by name
    for fm in folder_matters:
        if fm.id in matched_folder_ids:
            continue

        folder_key = f"{normalize(fm.client_name)}:{normalize(fm.matter_name)}"

        for lm in list_matters:
            if lm.id in matched_list_ids:
                continue

            list_key = f"{normalize(lm.client_name)}:{normalize(lm.matter_name)}"

            if fuzzy_name_match(folder_key, list_key):
                confirmed.append(merge_matters(fm, lm, 'fuzzy'))
                matched_folder_ids.add(fm.id)
                matched_list_ids.add(lm.id)
                break

    # Add unmatched to preliminary
    for fm in folder_matters:
        if fm.id not in matched_folder_ids:
            fm.confidence = 'low'
            preliminary.append(fm)

    for lm in list_matters:
        if lm.id not in matched_list_ids:
            lm.confidence = 'low'
            preliminary.append(lm)

    # Assign new IDs
    for i, m in enumerate(confirmed):
        m.id = f"confirmed-{i + 1}"
    for i, m in enumerate(preliminary):
        m.id = f"preliminary-{i + 1}"

    # Calculate stats
    stats = CrossReferenceStats(
        total_folder_matters=len(folder_matters),
        total_list_matters=len(list_matters),
        exact_matches=sum(1 for m in confirmed if m.match_type == 'exact'),
        fuzzy_matches=sum(1 for m in confirmed if m.match_type == 'fuzzy'),
        confirmed_count=len(confirmed),
        preliminary_count=len(preliminary),
        folder_only_count=sum(1 for m in preliminary if m.match_source == 'folder-only'),
        list_only_count=sum(1 for m in preliminary if m.match_source == 'list-only')
    )

    return confirmed, preliminary, stats


def fuzzy_name_match(key1: str, key2: str) -> bool:
    """Check if two name keys match with fuzzy tolerance."""
    if key1 == key2:
        return True

    if not key1 or not key2:
        return False

    if len(key1) > 10 and len(key2) > 10:
        shorter = key1 if len(key1) < len(key2) else key2
        longer = key2 if len(key1) < len(key2) else key1

        if shorter in longer:
            return True

        if calculate_similarity(key1, key2) > 0.8:
            return True

    return False


def merge_matters(folder_matter: Matter, list_matter: Matter, match_type: str) -> Matter:
    """Merge folder and list matter into confirmed matter."""
    return Matter(
        id=f"matched-{folder_matter.id}-{list_matter.id}",
        client_name=folder_matter.client_name or list_matter.client_name,
        matter_name=folder_matter.matter_name or list_matter.matter_name,
        client_no=list_matter.client_no or folder_matter.client_no,  # Prefer list
        matter_no=list_matter.matter_no or folder_matter.matter_no,  # Prefer list
        match_source='both',
        match_type=match_type,
        folder_path=folder_matter.folder_path,
        row_source=list_matter.row_source,
        selected=True,
        confidence='high' if match_type == 'exact' else 'medium'
    )


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class ClientMatterImporter:
    """Main orchestrator for client/matter import."""

    def __init__(self):
        self.folder_matters: List[Matter] = []
        self.list_matters: List[Matter] = []
        self.confirmed: List[Matter] = []
        self.preliminary: List[Matter] = []
        self.stats: Optional[CrossReferenceStats] = None

    def import_from_folder(self, folder_path: str):
        """Import matters from folder structure."""
        folders, root_name, folder_stats = extract_folder_structure(folder_path)
        self.folder_matters = folders_to_matters(folders)

        print(f"Extracted {len(self.folder_matters)} matters from {folder_stats.total_folders} folders")
        return self.folder_matters

    def import_from_file(self, file_path: str):
        """Import matters from Excel/CSV file."""
        ext = Path(file_path).suffix.lower()

        if ext in ('.xlsx', '.xls'):
            headers, rows = parse_excel(file_path)
        elif ext == '.csv':
            headers, rows = parse_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        columns = detect_columns(headers)
        print(f"Detected columns: {columns}")

        self.list_matters = extract_matters_from_list(
            rows, columns, Path(file_path).name
        )

        print(f"Extracted {len(self.list_matters)} matters from {len(rows)} rows")
        return self.list_matters

    def cross_reference(self):
        """Run cross-reference matching."""
        if not self.folder_matters and not self.list_matters:
            raise ValueError("No matters to cross-reference")

        self.confirmed, self.preliminary, self.stats = cross_reference(
            self.folder_matters, self.list_matters
        )

        print(f"\nCross-reference results:")
        print(f"  Confirmed: {self.stats.confirmed_count}")
        print(f"    - Exact matches: {self.stats.exact_matches}")
        print(f"    - Fuzzy matches: {self.stats.fuzzy_matches}")
        print(f"  Preliminary: {self.stats.preliminary_count}")
        print(f"    - Folder-only: {self.stats.folder_only_count}")
        print(f"    - List-only: {self.stats.list_only_count}")

        return self.confirmed, self.preliminary


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    importer = ClientMatterImporter()

    # Phase 1: Import from folder
    importer.import_from_folder("/path/to/client/folders")

    # Phase 2: Import from list
    importer.import_from_file("/path/to/client-list.xlsx")

    # Phase 3: Cross-reference
    confirmed, preliminary = importer.cross_reference()

    # Output results
    print("\n=== CONFIRMED MATTERS ===")
    for m in confirmed:
        print(f"  {m.client_name} / {m.matter_name} ({m.match_type})")

    print("\n=== PRELIMINARY MATTERS ===")
    for m in preliminary:
        print(f"  {m.client_name} / {m.matter_name} ({m.match_source})")
```

---

## Summary

This guide covers the complete deterministic client/matter import pipeline:

1. **Phase 1**: Extract folder hierarchy, infer client/matter relationships from directory structure
2. **Phase 2**: Parse Excel/CSV files, detect columns via pattern matching
3. **Phase 3**: Match across sources using exact number matching and fuzzy name matching

All algorithms are deterministic and do not require AI. The Python implementation provided can serve as a starting point for desktop applications.
