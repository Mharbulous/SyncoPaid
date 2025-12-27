# Progress: Moondream 2 Frozen Copy Setup

**Date:** 2025-12-26
**Status:** Complete
**Branch:** `claude/moonbeam-integration-docs-pEsnD`

---

## What Was Accomplished

Created a frozen copy of Moondream 2 on HuggingFace to prevent upstream changes from breaking SyncoPaid.

**Frozen copy:** https://huggingface.co/Mharbulous/moondream2-syncopaid
**Source:** `vikhyatk/moondream2` tag `2025-06-21`
**Size:** ~7.6GB total repository (~3.85GB model weights)

---

## Key Files Updated

| File | Purpose |
|------|---------|
| `ai_docs/MoonDream/moondream2-integration-checklist.md` | High-level integration phases |
| `.claude/data/plans/036_moondream2-integration.md` | TDD implementation plan |
| `.gitignore` | Added `moondream2-frozen/` exclusion |

---

## Technical Decisions

### Why fork to HuggingFace instead of other options?

| Option | Verdict |
|--------|---------|
| Pin revision in code | Depends on vikhyatk maintaining old revisions |
| Self-host on S3/CDN | Hosting costs, bandwidth fees |
| **Fork to own HuggingFace** | Free, deduplication means fast upload, full control |
| Bundle in installer | +4GB installer size |

### HuggingFace deduplication

Upload was fast (13.5MB actual transfer for 7.6GB) because HuggingFace deduplicates - identical files are linked, not re-uploaded.

### Free tier is sufficient

HuggingFace free accounts support unlimited public model repos. No payment required for hosting the frozen copy.

---

## Commands Reference

```bash
# Install HuggingFace CLI
pip install huggingface_hub[cli]

# Login (CLI may not be in PATH on Windows, use this instead)
python -c "from huggingface_hub import login; login()"

# List available tags/revisions
python -c "from huggingface_hub import list_repo_refs; refs = list_repo_refs('vikhyatk/moondream2'); print('Tags:', [t.name for t in refs.tags])"

# Download specific revision
python -c "from huggingface_hub import snapshot_download; snapshot_download('vikhyatk/moondream2', revision='2025-06-21', local_dir='.')"

# Create repo
python -c "from huggingface_hub import create_repo; create_repo('moondream2-syncopaid', repo_type='model')"

# Upload folder
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='.', repo_id='Mharbulous/moondream2-syncopaid', commit_message='Frozen copy')"
```

---

## Red Herrings to Avoid

| Looks relevant but isn't | Why |
|--------------------------|-----|
| `huggingface-cli` command | Not in PATH on Windows; use `python -c "from huggingface_hub import ..."` instead |
| `huggingface_hub[cli]` extras | Version 1.2.3 ignores this; CLI features included by default |
| Ollama/GGUF versions of Moondream | Documented quality issues, ~1 year behind official |
| `revision` parameter in code | No longer needed when using frozen repo |

---

## Architecture Decision: Subprocess Model

Moondream runs as a **background worker process**, not embedded in main app:

```
SyncoPaid.exe (lightweight, ~50MB)
    └── spawns moondream_worker.py when analysis needed
            └── loads ~3.85GB model weights into RAM
            └── processes analysis requests via JSON IPC
            └── can be killed to reclaim memory
```

Benefits: Main app stays responsive, model only loads when needed, can free 4GB+ RAM by killing worker.

---

## Moondream 2 Project Status (as of 2025-12-26)

- Actively maintained: commits through November 2025
- Version 2.5 release in preparation
- Latest frozen tag: `2025-06-21`
- Apache 2.0 license (commercial use OK)

---

## Key External Resources

- [Moondream GitHub commits](https://github.com/vikhyat/moondream/commits/main) - check for updates
- [HuggingFace Pricing](https://huggingface.co/pricing) - free tier details
- [Mharbulous frozen copy](https://huggingface.co/Mharbulous/moondream2-syncopaid) - what SyncoPaid uses

---

## Next Steps (Not Started)

Prerequisites from `.claude/data/plans/036_moondream2-integration.md`:
1. Story 14.1: VisionEngine base class interface
2. Story 14.2: Hardware detection (CPU/GPU)
3. Then: Implement MoondreamEngine class

The frozen copy is ready; integration code is not yet implemented.
