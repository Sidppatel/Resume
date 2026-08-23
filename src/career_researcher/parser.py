"""
Response parsing and file I/O for Career Knowledge Researcher.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Union


class KnowledgeResponseParser:
    """
    Handles static profile loading, raw LLM JSON extraction, and response sanitization
    for Career Domain Knowledge data.
    """

    @staticmethod
    def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Loads and returns parsed JSON from a file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def clean_json_response(raw_text: str) -> Dict[str, Any]:
        """
        Strips markdown code fences, isolates outer JSON structure, and parses into Python dict.
        """
        text = raw_text.strip()

        # Remove markdown code fences if present (```json ... ``` or ``` ...)
        if "```" in text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                text = match.group(1).strip()

        # Locate outer JSON braces
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]

        return json.loads(text)
