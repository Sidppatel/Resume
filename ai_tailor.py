#!/usr/bin/env python3
"""
CLI entry point to automatically tailor resume data to a target Job Description using NVIDIA DeepSeek V4 Flash.
"""
import argparse
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.ai_tailor import ResumeTailor, TailorConfig, DEFAULT_MODEL


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered Resume Tailor using NVIDIA DeepSeek V4 Flash."
    )
    parser.add_argument(
        "--jd",
        "-j",
        type=str,
        default="data/jd.txt",
        help="Path to job description text file (default: data/jd.txt)",
    )
    parser.add_argument(
        "--static",
        "-s",
        type=str,
        default="data/resume_static.json",
        help="Path to static resume profile JSON (default: data/resume_static.json)",
    )
    parser.add_argument(
        "--data",
        "-d",
        type=str,
        default="data/resume_data.json",
        help="Path to current resume JSON (default: data/resume_data.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/resume_data.json",
        help="Path for tailored resume output JSON (default: data/resume_data.json)",
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
        help="Fast mode: disable deep reasoning to generate tailored resume in ~5-10 seconds.",
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
        help="Stream the model's internal thinking and reasoning process live in terminal.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run AI tailoring and display output without writing to file.",
    )

    args = parser.parse_args()

    print("========================================", flush=True)
    print("       AI Resume Data Tailor            ", flush=True)
    print("========================================", flush=True)
    print(f"[*] Model:            {args.model}", flush=True)
    print(f"[*] Job Description:  {args.jd}", flush=True)
    print(f"[*] Static Profile:   {args.static}", flush=True)
    print(f"[*] Current Resume:   {args.data}", flush=True)
    print(f"[*] Output Target:    {args.output if not args.dry_run else '[DRY RUN - No file written]'}", flush=True)
    print("----------------------------------------", flush=True)

    try:
        config = TailorConfig(
            model=args.model,
            fast=args.fast,
            reasoning_effort=args.reasoning
        )
        tailor_engine = ResumeTailor(config=config)

        merged_data, reasoning = tailor_engine.tailor(
            jd_path=args.jd,
            static_path=args.static,
            current_resume_path=args.data,
            output_path=args.output,
            show_reasoning=args.show_reasoning,
            dry_run=args.dry_run
        )

        if args.show_reasoning and reasoning:
            print("\n========================================", flush=True)
            print("         AI Reasoning & Strategy        ", flush=True)
            print("========================================", flush=True)
            print(reasoning, flush=True)
            print("========================================\n", flush=True)

        print("\n[+] Resume tailoring completed successfully!", flush=True)
        print(f"[*] New Target Title: {merged_data.get('header', {}).get('job_title')}", flush=True)
        print(f"[*] Skill Categories: {len(merged_data.get('technical_skills', []))}", flush=True)
        print(f"[*] Experience Roles: {len(merged_data.get('professional_experience', []))}", flush=True)
        print(f"[*] Key Projects:     {len(merged_data.get('key_projects', []))}", flush=True)

        if not args.dry_run:
            print(f"[+] Updated resume JSON saved to: {args.output}", flush=True)
            print("\nNext step: Run `python build_resume.py` to generate your tailored Word resume!", flush=True)
        else:
            print("\n[Preview of Tailored Data]:", flush=True)
            print(json.dumps(merged_data, indent=2), flush=True)

        print("========================================", flush=True)

    except Exception as e:
        print(f"\n[!] Error during resume tailoring: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
