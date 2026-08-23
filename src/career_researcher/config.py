"""
Configuration and Client Factory for Career Knowledge Researcher.
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "deepseek-ai/deepseek-v4-flash-0731"


@dataclass
class ResearcherConfig:
    """Configuration options for Career Knowledge Researcher engine."""
    model: str = DEFAULT_MODEL
    base_url: str = NVIDIA_BASE_URL
    api_key: Optional[str] = None
    reasoning_effort: str = "medium"
    fast: bool = False
    temperature: float = 0.6
    top_p: float = 0.95
    max_tokens: int = 16384

    def get_api_key(self) -> str:
        """Retrieves and validates API key from config or environment."""
        key = self.api_key or os.getenv("NVIDIA_API_KEY")
        if not key or key.strip() == "your_nvidia_api_key_here":
            raise ValueError(
                "NVIDIA_API_KEY is not set.\n"
                "Please create a .env file with NVIDIA_API_KEY=your_key or set the environment variable."
            )
        return key.strip()

    def create_client(self) -> OpenAI:
        """Instantiates and returns an OpenAI client configured for NVIDIA NIM endpoints."""
        return OpenAI(base_url=self.base_url, api_key=self.get_api_key())
