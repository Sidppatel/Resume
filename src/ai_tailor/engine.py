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
from ..db import get_db, ResumeDatabase


class ResumeTailor:
    """
    Orchestrates the AI resume tailoring pipeline:
    1. Loads Job Description, static candidate profile, career domain knowledge, and current resume.
    2. Builds optimized ATS prompts with strict Job Title & Employer Domain Fidelity.
    3. Calls NVIDIA NIM DeepSeek API with live token streaming and reasoning display.
    4. Cleans JSON response, merges with static profile, and saves updated resume data.
    5. Archives the session (query, reasoning, prompts, tailored data) into local SQLite database.
    """

    def __init__(self, config: Optional[TailorConfig] = None, db: Optional[ResumeDatabase] = None):
        self.config = config or TailorConfig()
        self.client = self.config.create_client()
        self.prompt_builder = PromptBuilder()
        self.parser = TailorResponseParser()
        self.db = db or get_db()
        self.last_session_id: Optional[int] = None

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

    @staticmethod
    def _resolve_knowledge_path(
        knowledge_path: Optional[Union[str, Path]],
        static_path: Union[str, Path]
    ) -> Optional[Path]:
        """Helper to resolve knowledge file, supporting auto-detection based on static profile."""
        if knowledge_path:
            p = Path(knowledge_path)
            if p.exists():
                return p
            return None

        # Auto-detection based on static profile name
        p_static = Path(static_path)
        stem = p_static.stem
        # Check profile-specific first (e.g. data/career_knowledge-Vidhi.json)
        if stem.startswith("resume_static-"):
            suffix = stem[len("resume_static-"):]
            cand = p_static.parent / f"career_knowledge-{suffix}.json"
            if cand.exists():
                return cand
        # Check default data/career_knowledge.json
        cand_default = p_static.parent / "career_knowledge.json"
        if cand_default.exists():
            return cand_default
        return None

    def tailor(
        self,
        jd_path: Union[str, Path] = "data/jd.txt",
        static_path: Union[str, Path] = "data/resume_static.json",
        current_resume_path: Union[str, Path] = "data/resume_data.json",
        knowledge_path: Optional[Union[str, Path]] = None,
        output_path: Optional[Union[str, Path]] = "data/resume_data.json",
        show_reasoning: bool = False,
        dry_run: bool = False,
        save_to_db: bool = True
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

        # Load career knowledge if available
        knowledge_data = None
        resolved_knowledge = self._resolve_knowledge_path(knowledge_path, static_path)
        if resolved_knowledge and resolved_knowledge.exists():
            try:
                knowledge_data = self.parser.load_json_file(resolved_knowledge)
                print(f"[*] Career Knowledge: Loaded ({resolved_knowledge})", flush=True)
            except Exception as e:
                print(f"[!] Warning: Failed loading career knowledge from {resolved_knowledge}: {e}", file=sys.stderr)
        else:
            print("[*] Career Knowledge: Not found (using static profile context)", flush=True)

        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            static_data=static_data,
            current_resume=current_resume,
            jd_text=jd_text,
            knowledge_data=knowledge_data
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

        # Archive session to local SQLite database
        self.last_session_id = None
        if save_to_db and not dry_run:
            try:
                self.last_session_id = self.db.save_tailoring_run(
                    jd_text=jd_text,
                    tailored_data=merged_data,
                    static_data=static_data,
                    knowledge_data=knowledge_data,
                    prompt_system=system_prompt,
                    prompt_user=user_prompt,
                    thinking_process=full_reasoning,
                    token_count=token_count[0],
                    execution_time_seconds=elapsed,
                    model=self.config.model,
                    reasoning_effort=self.config.reasoning_effort
                )
            except Exception as e:
                print(f"[!] Warning: Could not save session to local DB: {e}", file=sys.stderr)

        return merged_data, full_reasoning
