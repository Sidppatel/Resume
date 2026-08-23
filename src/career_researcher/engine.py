"""
AI Career Knowledge Researcher Engine orchestrator.
"""
import json
import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

from .config import ResearcherConfig
from .prompts import ResearchPromptBuilder
from .parser import KnowledgeResponseParser
from ..db import get_db, ResumeDatabase


class CareerKnowledgeResearcher:
    """
    Orchestrates the AI research pipeline:
    1. Loads static candidate profile (companies, locations, job titles, dates, education).
    2. Constructs deep-research prompts for NVIDIA DeepSeek V4 Flash.
    3. Analyzes each company's genuine industry, operations, enterprise tech environment, and domain KPIs.
    4. Analyzes each job title's detailed scope, daily duties, transferable technical skills, and domain boundary rules.
    5. Saves structured career knowledge JSON for downstream ATS tailoring.
    6. Archives researched knowledge profiles into the local SQLite database.
    """

    def __init__(self, config: Optional[ResearcherConfig] = None, db: Optional[ResumeDatabase] = None):
        self.config = config or ResearcherConfig()
        self.client = self.config.create_client()
        self.prompt_builder = ResearchPromptBuilder()
        self.parser = KnowledgeResponseParser()
        self.db = db or get_db()
        self.last_knowledge_id: Optional[int] = None

    def research(
        self,
        static_path: Union[str, Path] = "data/resume_static.json",
        output_path: Optional[Union[str, Path]] = "data/career_knowledge.json",
        show_reasoning: bool = False,
        dry_run: bool = False,
        save_to_db: bool = True
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Executes end-to-end AI career research against the static profile.

        Returns:
            Tuple of (knowledge_data_dict, reasoning_text_or_None)
        """
        # Ensure UTF-8 output on Windows consoles
        stdout = getattr(sys, "stdout", None)
        reconfigure = getattr(stdout, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        static_data = self.parser.load_json_file(static_path)
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(static_data=static_data)

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
        print("[*] Connecting to NVIDIA endpoint for Career Research...", flush=True)

        start_time = time.time()
        reasoning_parts = []
        content_parts = []
        token_count = [0]
        phase = ["Researching Companies..."]
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
                "Deep Thinking & Researching"
                if (not self.config.fast and self.config.reasoning_effort != "none")
                else "Generating Knowledge JSON"
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
                    if phase[0] == "Deep Thinking & Researching":
                        phase[0] = "Generating Knowledge JSON"
                        if show_reasoning:
                            print("\n\n--- Generating Career Knowledge JSON ---", flush=True)
                    content_parts.append(delta.content)
                    token_count[0] += 1

        finally:
            stop_spinner.set()
            spinner_thread.join(timeout=0.5)

        elapsed = time.time() - start_time
        if not show_reasoning:
            sys.stdout.write(
                f"\r[+] Research completed in {elapsed:.1f}s ({token_count[0]} tokens)                          \n"
            )
            sys.stdout.flush()
        else:
            print(f"\n[+] Research completed in {elapsed:.1f}s ({token_count[0]} tokens)", flush=True)

        full_content = "".join(content_parts)
        full_reasoning = "".join(reasoning_parts) if reasoning_parts else None

        knowledge_data = self.parser.clean_json_response(full_content)

        # Set generated timestamp if not present
        if "generated_at" not in knowledge_data or not knowledge_data["generated_at"]:
            knowledge_data["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if output_path and not dry_run:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(knowledge_data, f, indent=2)

        # Archive career knowledge profile into local SQLite database
        self.last_knowledge_id = None
        if save_to_db and not dry_run:
            try:
                profile_name = Path(output_path).stem if output_path else Path(static_path).stem.replace("resume_static", "career_knowledge")
                cand_name = static_data.get("header", {}).get("name", "Unknown")
                self.last_knowledge_id = self.db.save_career_knowledge(
                    profile_name=profile_name,
                    knowledge_data=knowledge_data,
                    candidate_name=cand_name,
                    source_static_path=str(static_path),
                    reasoning_trace=full_reasoning
                )
            except Exception as e:
                print(f"[!] Warning: Could not save knowledge profile to local DB: {e}", file=sys.stderr)

        return knowledge_data, full_reasoning
