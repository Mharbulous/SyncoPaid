"""Abstract base class for vision LLM engines.

Defines the interface that all vision engines must implement,
enabling easy swapping of AI models (Moondream, LLaVA, etc.)
without changing the analysis pipeline.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AnalysisResult:
    """Structured output from vision engine analysis.

    Attributes:
        description: Human-readable description of what the screenshot shows
        activity_type: Categorized activity (e.g., 'document_editing', 'web_browsing')
        confidence: Confidence score 0.0-1.0
        raw_output: Raw model output for debugging/logging
    """
    description: str
    activity_type: str
    confidence: float
    raw_output: str


class VisionEngine(ABC):
    """Abstract base class for vision LLM engines.

    All vision engines must implement the analyze() method
    to provide screenshot analysis capabilities.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the engine's display name (e.g., 'Moondream 2')."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the model identifier (e.g., 'vikhyatk/moondream2')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is available (dependencies installed, model downloaded)."""
        pass

    @abstractmethod
    def analyze(self, image_path: Path, prompt: Optional[str] = None) -> AnalysisResult:
        """Analyze a screenshot and return structured results.

        Args:
            image_path: Path to the screenshot image file
            prompt: Optional custom prompt (uses default if None)

        Returns:
            AnalysisResult with description, activity_type, confidence, raw_output
        """
        pass
