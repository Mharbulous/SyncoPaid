"""Abstract base class for vision LLM engines.

Defines the interface that all vision engines must implement,
enabling easy swapping of AI models (Moondream, LLaVA, etc.)
without changing the analysis pipeline.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Type


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

    def config_schema(self) -> dict:
        """Return configuration schema for this engine.

        Override in subclasses to define engine-specific settings.
        Schema format: {"setting_name": {"type": "str|int|float|bool", "default": value, "options": [...]}}

        Returns:
            Dict defining configuration options, empty by default
        """
        return {}


# Engine registry - maps engine names to their classes
_registry: Dict[str, Type[VisionEngine]] = {}


def register_engine(name: str, engine_class: Type[VisionEngine]) -> None:
    """Register a vision engine class.

    Args:
        name: Unique identifier for the engine (e.g., 'moondream2')
        engine_class: The VisionEngine subclass to register
    """
    _registry[name] = engine_class


def get_registered_engines() -> Dict[str, Type[VisionEngine]]:
    """Get all registered engine classes.

    Returns:
        Dict mapping engine names to their classes
    """
    return _registry.copy()


def get_engine(name: str) -> Optional[VisionEngine]:
    """Get an instantiated engine by name.

    Args:
        name: The registered engine name

    Returns:
        Instantiated engine or None if not found
    """
    engine_class = _registry.get(name)
    if engine_class is None:
        return None
    return engine_class()


def get_available_engines() -> Dict[str, Type[VisionEngine]]:
    """Get engines that are currently available for use.

    Returns:
        Dict mapping engine names to classes, filtered to only available engines
    """
    available = {}
    for name, engine_class in _registry.items():
        try:
            engine = engine_class()
            if engine.is_available():
                available[name] = engine_class
        except Exception:
            # Skip engines that fail to instantiate
            pass
    return available
