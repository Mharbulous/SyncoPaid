# Screenshot Analysis - Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Verify that all screenshot analysis subsystems work together as a complete feature, enabling automatic screenshot capture, AI analysis, batch processing, and failure handling.

**Approach:** Create integration tests that exercise the complete screenshot analysis workflow across all child story implementations (8.6.1-8.6.5). Validate that automatic analysis, night processing, batch processing, privacy controls, and failure handling work cohesively.

**Tech Stack:** Python pytest, src/syncopaid/screenshot_analyzer.py, src/syncopaid/screenshot_worker_actions.py, existing vision_engine.py

---

## Story Context

**Title:** Screenshot Analysis
**Description:** Automatic analysis of captured screenshots for activity categorization

**Parent Story Completion Criteria:**
- [ ] All child stories (8.6.1-8.6.5) are verified/implemented
- [ ] Integration tests pass for complete workflow
- [ ] Screenshot → Analysis → Categorization pipeline works end-to-end

**Child Stories:**
| ID | Title | Status | Notes |
|----|-------|--------|-------|
| 8.6.1 | Automatic Screenshot Analysis | verifying | Core analyzer |
| 8.6.2 | Night Processing Mode | implemented | Scheduling |
| 8.6.3 | Batch Processing On-Demand | active | UI for batch |
| 8.6.4 | Privacy-Preserving Analysis | active | Privacy features |
| 8.6.5 | Handling Analysis Failures | active | Error handling |

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Child stories 8.6.1 and 8.6.2 are at least 'implemented' stage

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/integration/test_screenshot_analysis_workflow.py` | Create | Integration tests for complete workflow |
| `src/syncopaid/screenshot_analyzer.py` | Verify | Ensure AnalysisResult.model_version is present |

## TDD Tasks

### Task 1: Create Integration Test Scaffold (~3 min)

**Files:**
- Create: `tests/integration/test_screenshot_analysis_workflow.py`

**Context:** Integration tests verify that screenshot capture, analysis, and storage work together. This scaffold sets up the test module and imports.

**Step 1 - RED:** Write failing test

```python
# tests/integration/test_screenshot_analysis_workflow.py
"""Integration tests for screenshot analysis workflow.

Tests that all screenshot analysis components (8.6.1-8.6.5) work together:
- Automatic screenshot capture
- AI-powered analysis
- Night/batch processing
- Privacy controls
- Failure handling
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from syncopaid.screenshot_analyzer import ScreenshotAnalyzer, AnalysisResult


class TestScreenshotAnalysisWorkflow:
    """Integration tests for the complete screenshot analysis pipeline."""

    def test_analysis_result_serialization_roundtrip(self):
        """AnalysisResult can be serialized and deserialized."""
        original = AnalysisResult(
            application="Microsoft Word",
            document_name="Brief_2024.docx",
            case_numbers=["2024 BCSC 1234"],
            email_subject=None,
            webpage_title=None,
            visible_text=["Client Matter: Smith v. Jones"],
            confidence=0.85
        )

        json_str = original.to_json()
        restored = AnalysisResult.from_json(json_str)

        assert restored.application == original.application
        assert restored.document_name == original.document_name
        assert restored.case_numbers == original.case_numbers
        assert restored.confidence == original.confidence
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py::TestScreenshotAnalysisWorkflow::test_analysis_result_serialization_roundtrip -v
```
Expected output: `PASSED` (this test validates existing functionality)

**Step 3 - GREEN:** Test should pass with existing code

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/integration/test_screenshot_analysis_workflow.py && git commit -m "test: add integration test scaffold for screenshot analysis"
```

---

### Task 2: Test Analyzer Initialization (~3 min)

**Files:**
- Modify: `tests/integration/test_screenshot_analysis_workflow.py`

**Context:** The ScreenshotAnalyzer requires an LLM client with vision capabilities. This test verifies proper initialization and prompt building.

**Step 1 - RED:** Add test to existing file

```python
# tests/integration/test_screenshot_analysis_workflow.py (append to class)

    def test_analyzer_initialization_with_mock_client(self):
        """ScreenshotAnalyzer initializes with LLM client."""
        mock_client = Mock()
        mock_client.analyze_image = Mock(return_value='{"application": "test", "confidence": 0.5}')

        analyzer = ScreenshotAnalyzer(mock_client)

        assert analyzer.llm_client is mock_client
        assert 'lawyer' in analyzer._analysis_prompt.lower()
        assert 'JSON' in analyzer._analysis_prompt
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py::TestScreenshotAnalysisWorkflow::test_analyzer_initialization_with_mock_client -v
```
Expected output: `PASSED` (validates existing functionality)

**Step 3 - GREEN:** Test should pass with existing code

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py -v
```
Expected output: `2 passed`

**Step 5 - COMMIT:**
```bash
git add tests/integration/test_screenshot_analysis_workflow.py && git commit -m "test: add analyzer initialization test"
```

---

### Task 3: Test Analysis Pipeline with Mock Vision Engine (~5 min)

**Files:**
- Modify: `tests/integration/test_screenshot_analysis_workflow.py`

**Context:** Tests the complete analysis pipeline from screenshot path to AnalysisResult. Uses a mock vision engine to avoid actual API calls.

**Step 1 - RED:** Add end-to-end pipeline test

```python
# tests/integration/test_screenshot_analysis_workflow.py (append to class)

    def test_analysis_pipeline_returns_structured_result(self):
        """Complete analysis pipeline returns properly structured AnalysisResult."""
        mock_response = '''{
            "application": "Outlook",
            "document_name": null,
            "case_numbers": ["2024 BCSC 5678"],
            "email_subject": "Re: Smith Matter - Document Review",
            "webpage_title": null,
            "visible_text": ["From: client@example.com"],
            "confidence": 0.92
        }'''

        mock_client = Mock()
        mock_client.analyze_image = Mock(return_value=mock_response)

        analyzer = ScreenshotAnalyzer(mock_client)

        # Create a temporary test image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name

        try:
            result = analyzer.analyze(temp_path)

            assert isinstance(result, AnalysisResult)
            assert result.application == "Outlook"
            assert result.email_subject == "Re: Smith Matter - Document Review"
            assert "2024 BCSC 5678" in result.case_numbers
            assert result.confidence == 0.92
        finally:
            os.unlink(temp_path)
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py::TestScreenshotAnalysisWorkflow::test_analysis_pipeline_returns_structured_result -v
```
Expected output: `PASSED` or `FAILED` depending on analyze method implementation

**Step 3 - GREEN:** If test fails, verify the analyze method exists in ScreenshotAnalyzer. The method should:
1. Read the image file
2. Call llm_client.analyze_image with the image
3. Parse the JSON response
4. Return an AnalysisResult

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py -v
```
Expected output: `3 passed`

**Step 5 - COMMIT:**
```bash
git add tests/integration/test_screenshot_analysis_workflow.py && git commit -m "test: add analysis pipeline integration test"
```

---

### Task 4: Test Failure Handling (8.6.5 Integration) (~3 min)

**Files:**
- Modify: `tests/integration/test_screenshot_analysis_workflow.py`

**Context:** Verifies that analysis failures are handled gracefully (relates to story 8.6.5). The analyzer should not crash on malformed responses.

**Step 1 - RED:** Add failure handling test

```python
# tests/integration/test_screenshot_analysis_workflow.py (append to class)

    def test_analyzer_handles_malformed_json_gracefully(self):
        """Analyzer handles malformed LLM responses without crashing."""
        mock_client = Mock()
        mock_client.analyze_image = Mock(return_value='not valid json at all')

        analyzer = ScreenshotAnalyzer(mock_client)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name

        try:
            result = analyzer.analyze(temp_path)

            # Should return a default/empty result rather than crashing
            assert isinstance(result, AnalysisResult)
            assert result.confidence == 0.0 or result.confidence is None
        finally:
            os.unlink(temp_path)

    def test_analyzer_handles_llm_exception_gracefully(self):
        """Analyzer handles LLM client exceptions without crashing."""
        mock_client = Mock()
        mock_client.analyze_image = Mock(side_effect=Exception("API error"))

        analyzer = ScreenshotAnalyzer(mock_client)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name

        try:
            result = analyzer.analyze(temp_path)

            # Should return a default/empty result rather than crashing
            assert isinstance(result, AnalysisResult)
        finally:
            os.unlink(temp_path)
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py -k "malformed or exception" -v
```
Expected output: Tests may pass or fail depending on current error handling

**Step 3 - GREEN:** If tests fail, ensure ScreenshotAnalyzer.analyze wraps LLM calls in try/except and returns a default AnalysisResult on error.

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_screenshot_analysis_workflow.py -v
```
Expected output: `5 passed`

**Step 5 - COMMIT:**
```bash
git add tests/integration/test_screenshot_analysis_workflow.py && git commit -m "test: add failure handling integration tests for story 8.6.5"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/integration/test_screenshot_analysis_workflow.py -v  # All integration tests pass
python -m pytest -v                                                          # All tests pass
python -m syncopaid.screenshot_analyzer                                      # Module imports without error (if has __main__)
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This is a **coordination plan** for parent story 8.6
- Child stories (8.6.1-8.6.5) have their own detailed plans
- Parent story can transition to 'verifying' when:
  - All child stories are 'implemented' or 'verifying'
  - Integration tests in this plan pass
- The integration tests validate that subsystems work together without testing each subsystem in isolation (that's covered by child story tests)
