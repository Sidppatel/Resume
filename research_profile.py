#!/usr/bin/env python3
"""
CLI entry point to automatically research and build career domain knowledge from a static candidate profile.
Uses NVIDIA DeepSeek V4 Flash with deep reasoning to generate comprehensive industry, tech stack, and role analysis.
"""
import argparse
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.career_researcher import CareerKnowledgeResearcher, ResearcherConfig, DEFAULT_MODEL


def get_default_output_path(static_path: str) -> str:
    """
    Computes default output path for knowledge JSON.
    e.g., data/resume_static.json -> data/career_knowledge.json
          data/resume_static-Vidhi.json -> data/career_knowledge-Vidhi.json
    """
    p = Path(static_path)
    stem = p.stem
    if stem.startswith("resume_static-"):
        profile_suffix = stem[len("resume_static-"):]
        return str(p.parent / f"career_knowledge-{profile_suffix}.json")
    elif stem == "resume_static":
        return str(p.parent / "career_knowledge.json")
    else:
        return str(p.parent / f"career_knowledge_{stem}.json")


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered Career & Company Domain Researcher using NVIDIA DeepSeek V4 Flash."
    )
    parser.add_argument(
        "--static",
        "-s",
        type=str,
        default="data/resume_static.json",
        help="Path to static resume profile JSON (default: data/resume_static.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path for career knowledge output JSON (default: auto-detected as data/career_knowledge[-profile].json)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model identifier (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--fast",
        "-f",
        action="store_true",
        help="Fast mode: disable deep reasoning for quick research (~5-10s).",
    )
    parser.add_argument(
        "--reasoning",
        type=str,
        choices=["none", "low", "medium", "high"],
        default="medium",
        help="Reasoning effort level (default: medium). Use 'none' or --fast for fastest execution.",
    )
    parser.add_argument(
        "--show-reasoning",
        "-r",
        action="store_true",
        help="Stream the model's internal thinking and research process live in terminal.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run AI research and display knowledge output without writing to file.",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Do not archive this career knowledge profile into the local SQLite database.",
    )

    args = parser.parse_args()

    output_path = args.output if args.output else get_default_output_path(args.static)

    print("========================================", flush=True)
    print("      AI Career Knowledge Researcher    ", flush=True)
    print("========================================", flush=True)
    print(f"[*] Model:          {args.model}", flush=True)
    print(f"[*] Static Profile: {args.static}", flush=True)
    print(f"[*] Output Target:  {output_path if not args.dry_run else '[DRY RUN - No file written]'}", flush=True)
    print(f"[*] Local Vault DB: {'Enabled (data/resume_vault.db)' if not args.no_db and not args.dry_run else 'Disabled'}", flush=True)
    print("----------------------------------------", flush=True)

    try:
        config = ResearcherConfig(
            model=args.model,
            fast=args.fast,
            reasoning_effort=args.reasoning
        )
        researcher = CareerKnowledgeResearcher(config=config)

        knowledge_data, reasoning = researcher.research(
            static_path=args.static,
            output_path=output_path,
            show_reasoning=args.show_reasoning,
            dry_run=args.dry_run,
            save_to_db=not args.no_db
        )

        if args.show_reasoning and reasoning:
            print("\n========================================", flush=True)
            print("       AI Research Thinking Trace       ", flush=True)
            print("========================================", flush=True)
            print(reasoning, flush=True)
            print("========================================\n", flush=True)

        print("\n[+] Career domain research completed successfully!", flush=True)
        print(f"[*] Candidate:      {knowledge_data.get('candidate_name', 'N/A')}", flush=True)
        companies = knowledge_data.get("companies", [])
        print(f"[*] Companies:      {len(companies)} researched", flush=True)
        for c in companies:
            comp_name = c.get("company", "Unknown")
            industry = c.get("industry", "Unknown Industry")
            roles_cnt = len(c.get("roles", []))
            print(f"    • {comp_name} ({industry}) — {roles_cnt} role(s)", flush=True)

        if researcher.last_knowledge_id:
            print(f"[+] Saved to Local DB: Knowledge Profile #{researcher.last_knowledge_id} in data/resume_vault.db", flush=True)

        if not args.dry_run:
            print(f"[+] Career knowledge JSON saved to: {output_path}", flush=True)
            print("\nNext step: Run `python ai_tailor.py` to tailor resumes using this grounded knowledge!", flush=True)
        else:
            print("\n[Preview of Researched Knowledge]:", flush=True)
            print(json.dumps(knowledge_data, indent=2), flush=True)

        print("========================================", flush=True)

    except Exception as e:
        print(f"\n[!] Error during career research: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
