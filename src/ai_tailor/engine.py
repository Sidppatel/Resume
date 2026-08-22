"""
AI Resume Tailor Engine orchestrator.
"""
import json
import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

from .config import TailorConfig
from .prompts import PromptBuilder
from .parser import TailorResponseParser


class ResumeTailor:
    """
    Orchestrates the AI resume tailoring pipeline:
    1. Loads Job Description, static candidate profile, and current resume.
    2. Builds optimized ATS prompts.
    3. Calls NVIDIA NIM DeepSeek API with live token streaming and reasoning display.
    4. Cleans JSON response, merges with static profile, and saves updated resume data.
    """

    def __init__(self, config: Optional[TailorConfig] = None):
        self.config = config or TailorConfig()
        self.client = self.config.create_client()
        self.prompt_builder = PromptBuilder()
        self.parser = TailorResponseParser()

    @staticmethod
    def _resolve_jd_path(jd_path: Union[str, Path]) -> Path:
        """Helper to resolve jd file, supporting both .txt and .text extensions."""
        p = Path(jd_path)
        if p.exists():
            return p
        # If jd.txt requested but jd.text exists, or vice-versa
        alt = p.with_suffix(".text") if p.suffix == ".txt" else p.with_suffix(".txt")
        if alt.exists():
            return alt
        return p

    def tailor(
        self,
        jd_path: Union[str, Path] = "data/jd.txt",
        static_path: Union[str, Path] = "data/resume_static.json",
        current_resume_path: Union[str, Path] = "data/resume_data.json",
        output_path: Optional[Union[str, Path]] = "data/resume_data.json",
        show_reasoning: bool = False,
        dry_run: bool = False
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Executes end-to-end resume tailoring against a Job Description.

        Returns:
            Tuple of (merged_resume_dict, reasoning_text_or_None)
        """
        # Ensure UTF-8 output on Windows consoles
        stdout = getattr(sys, "stdout", None)
        reconfigure = getattr(stdout, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        resolved_jd = self._resolve_jd_path(jd_path)
        jd_text = self.parser.load_text_file(resolved_jd)
        static_data = self.parser.load_json_file(static_path)
        current_resume = self.parser.load_json_file(current_resume_path)

        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            static_data=static_data,
            current_resume=current_resume,
            jd_text=jd_text
        )

        # Configure extra_body based on thinking configuration
        extra_body = {}
        if self.config.fast or self.config.reasoning_effort == "none":
            extra_body = {"chat_template_kwargs": {"thinking": False}}
        else:
            extra_body = {
                "chat_template_kwargs": {
                    "thinking": True,
                    "reasoning_effort": self.config.reasoning_effort
                }
            }

        thinking_label = (
            "OFF (Fast Mode)"
            if (self.config.fast or self.config.reasoning_effort == "none")
            else f"ON (effort: {self.config.reasoning_effort})"
        )
        print(f"[*] Thinking Mode:    {thinking_label}", flush=True)
        print("[*] Connecting to NVIDIA endpoint...", flush=True)

        start_time = time.time()
        reasoning_parts = []
        content_parts = []
        token_count = [0]
        phase = ["Connecting..."]
        stop_spinner = threading.Event()

        def spinner_loop():
            spinner_chars = ["|", "/", "-", "\\"]
            idx = 0
            while not stop_spinner.is_set():
                if not show_reasoning:
                    elapsed = time.time() - start_time
                    sp = spinner_chars[idx % len(spinner_chars)]
                    cnt = token_count[0]
                    token_str = f" ({cnt} tokens)" if cnt > 0 else ""
                    sys.stdout.write(f"\r[{sp}] [{elapsed:.1f}s] {phase[0]}{token_str}    ")
                    sys.stdout.flush()
                    idx += 1
                time.sleep(0.1)

        spinner_thread = threading.Thread(target=spinner_loop, daemon=True)
        spinner_thread.start()

        try:
            response_stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_tokens=self.config.max_tokens,
                extra_body=extra_body,
                stream=True
            )

            phase[0] = (
                "Thinking"
                if (not self.config.fast and self.config.reasoning_effort != "none")
                else "Generating JSON"
            )

            for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # Extract reasoning chunk if available
                reasoning_chunk = (
                    getattr(delta, "reasoning", None) or
                    getattr(delta, "reasoning_content", None) or
                    (delta.model_dump().get("reasoning_content") if hasattr(delta, "model_dump") else None)
                )
                if reasoning_chunk:
                    reasoning_parts.append(reasoning_chunk)
                    token_count[0] += 1
                    if show_reasoning:
                        sys.stdout.write(reasoning_chunk)
                        sys.stdout.flush()

                # Extract content chunk
                if delta.content:
                    if phase[0] == "Thinking":
                        phase[0] = "Generating JSON"
                        if show_reasoning:
                            print("\n\n--- Generating Final Resume JSON ---", flush=True)
                    content_parts.append(delta.content)
                    token_count[0] += 1

        finally:
            stop_spinner.set()
            spinner_thread.join(timeout=0.5)

        elapsed = time.time() - start_time
        if not show_reasoning:
            sys.stdout.write(
                f"\r[+] Stream completed in {elapsed:.1f}s ({token_count[0]} tokens)                          \n"
            )
            sys.stdout.flush()
        else:
            print(f"\n[+] Stream completed in {elapsed:.1f}s ({token_count[0]} tokens)", flush=True)

        full_content = "".join(content_parts)
        full_reasoning = "".join(reasoning_parts) if reasoning_parts else None

        dynamic_data = self.parser.clean_json_response(full_content)
        merged_data = self.parser.merge_resume_data(static_data, dynamic_data)

        if output_path and not dry_run:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(merged_data, f, indent=2)

        return merged_data, full_reasoning
