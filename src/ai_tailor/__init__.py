"""
AI Resume Tailor Package.
"""
from .config import TailorConfig, DEFAULT_MODEL, NVIDIA_BASE_URL
from .prompts import PromptBuilder
from .parser import TailorResponseParser
from .engine import ResumeTailor
from ..career_researcher import CareerKnowledgeResearcher

__all__ = [
    "ResumeTailor",
    "TailorConfig",
    "PromptBuilder",
    "TailorResponseParser",
    "CareerKnowledgeResearcher",
    "DEFAULT_MODEL",
    "NVIDIA_BASE_URL",
]
