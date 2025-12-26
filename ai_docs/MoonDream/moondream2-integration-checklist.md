# Moondream 2 Integration Checklist for SyncoPaid

## Overview

This checklist covers integrating Moondream 2 as the local AI engine for screenshot analysis in SyncoPaid. The model runs entirely on-device, ensuring attorney-client privilege compliance.

**Key specs:**
- Model size: 3.85GB
- Inference speed: 7-25 seconds (CPU) / sub-second (GPU)
- Minimum RAM: 8GB
- License: Apache 2.0 (commercial use permitted)

---

## Phase 1: Validate Feasibility

- [ ] **1.1** Set up Python development environment (3.10 or 3.11 recommended)

- [ ] **1.2** Install core dependencies:
  ```bash
  pip install transformers torch pillow einops accelerate
  ```

- [ ] **1.3** Verify GPU detection:
  ```bash
  python -c "import torch; print(torch.cuda.is_available())"
  ```

- [ ] **1.4** Download model from frozen copy and run test inference:
  ```python
  from transformers import AutoModelForCausalLM
  from PIL import Image

  # Using Mharbulous frozen copy (originally vikhyatk/moondream2 tag 2025-06-21)
  model = AutoModelForCausalLM.from_pretrained(
      "Mharbulous/moondream2-syncopaid",
      trust_remote_code=True
  )
  ```

- [ ] **1.5** Benchmark inference time on target minimum hardware spec to confirm acceptable performance

---

## Phase 2: Prototype the AI Pipeline

- [ ] **2.1** Develop and test prompts for specific use cases:
  - Activity classification
  - Application detection
  - Document identification
  - Task/matter categorization

- [ ] **2.2** Define exact input/output contract:
  - Input: Screenshot image (format, resolution, compression)
  - Output: Structured data (client, matter, activity type, billing narrative)

- [ ] **2.3** Test with representative legal workflow screenshots:
  - Clio
  - Outlook / email clients
  - Word / document editors
  - Legal research tools (Westlaw, CanLII, etc.)
  - Court filing systems

---

## Phase 3: Build Production Integration

- [ ] **3.1** Implement robust initialization with GPU detection and CPU fallback:
  ```python
  device = "cuda" if torch.cuda.is_available() else "cpu"
  dtype = torch.float16 if device == "cuda" else torch.float32  # float32 required for CPU

  # Using Mharbulous frozen copy (originally vikhyatk/moondream2 tag 2025-06-21)
  model = AutoModelForCausalLM.from_pretrained(
      "Mharbulous/moondream2-syncopaid",
      trust_remote_code=True,
      torch_dtype=dtype,
      device_map={"": device} if device == "cuda" else None
  )
  ```

- [ ] **3.2** Add image encoding cache to avoid re-encoding for multiple queries per screenshot:
  ```python
  encoded = model.encode_image(screenshot)
  app_name = model.query(encoded, "What application is visible?")["answer"]
  doc_type = model.query(encoded, "What type of document is shown?")["answer"]
  ```

- [ ] **3.3** Build screenshot capture pipeline in the app

- [ ] **3.4** Create background processing queue for non-blocking analysis

- [ ] **3.5** Implement error handling and graceful degradation:
  - Model load failures
  - Inference timeouts
  - Low-confidence results
  - Out-of-memory conditions

- [ ] **3.6** Add user controls:
  - Enable/disable AI features
  - Adjust analysis frequency
  - Review/correct AI categorizations

---

## Phase 4: Package for Distribution

- [ ] **4.1** Choose deployment method:
  - **Recommended:** Moondream Station (`pip install moondream-station`)
  - Alternative: Direct Transformers integration (more control, more complexity)

- [ ] **4.2** Configure model cache path to app's data directory (not default HuggingFace cache at `%USERPROFILE%\.cache\huggingface`)

- [ ] **4.3** Implement first-run model download OR bundle weights with installer (~4GB)

- [ ] **4.4** Pin dependencies in requirements.txt:
  ```
  transformers==4.41.0  # or tested compatible version
  torch>=2.0.0
  # Model revision pinned in code: 2025-06-21
  ```

- [ ] **4.5** Add Apache 2.0 license attribution to about/credits:
  ```
  Screenshot analysis powered by Moondream 2
  Copyright © vikhyat/M87 Labs - Apache 2.0 License
  https://github.com/vikhyat/moondream
  ```

---

## Phase 5: Validate and Document

- [ ] **5.1** Test on minimum spec hardware (8GB RAM, no GPU)

- [ ] **5.2** Verify no network calls occur during inference (privacy compliance for attorney-client privilege)

- [ ] **5.3** Document system requirements for users:
  - Windows 11
  - 8GB RAM minimum (16GB recommended)
  - 5GB free disk space
  - Optional: NVIDIA GPU with 2.4GB+ VRAM for faster analysis

- [ ] **5.4** Create troubleshooting guide including:
  - Cache-clearing instructions for tensor mismatch errors
  - GPU not detected issues
  - Slow performance remediation

---

## Known Pitfalls to Avoid

| Issue | Cause | Solution |
|-------|-------|----------|
| GPU shows 0% usage | Missing device_map configuration | Add `device_map={"": "cuda"}` |
| `LayerNormKernelImpl not implemented for 'Half'` | Using float16 on CPU | Use float32 for CPU |
| Model breaks after update | Transformers version incompatibility | Pin both model revision and transformers version |
| Tensor size mismatch | Stale cached model files | Clear HuggingFace cache directory |
| Poor quality outputs | Using Ollama or GGUF versions | Use official HuggingFace model only |

---

## Deployment Options Comparison

| Option | Complexity | Bundle Size | Recommendation |
|--------|------------|-------------|----------------|
| Moondream Station | Low | ~3GB | ✅ Recommended |
| HuggingFace Transformers | Medium | 5-10GB | For advanced customization |
| Ollama | Low | ~2GB | ❌ Outdated (~1 year behind) |
| GGUF/llama.cpp | High | ~2GB | ❌ Documented quality issues |

---

## Resources

- [SyncoPaid Frozen Copy](https://huggingface.co/Mharbulous/moondream2-syncopaid) ← Use this for SyncoPaid
- [Moondream Documentation](https://docs.moondream.ai/)
- [Moondream 2 Original (vikhyatk)](https://huggingface.co/vikhyatk/moondream2)
- [GitHub Repository](https://github.com/vikhyat/moondream)
- [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)
