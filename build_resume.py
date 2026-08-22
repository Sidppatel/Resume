#!/usr/bin/env python3
"""
CLI entry point to generate a customized Word resume (.docx) from a JSON data source.
"""
import argparse
import re
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.resume_builder import ResumeBuilder, ResumeStyles, ResumeDataLoader


def get_default_output_path(data: dict, output_dir: str = "output") -> str:
    """
    Constructs default output filename in the format: first_last_job_title.docx
    """
    header = data.get("header", {})
    name = header.get("name", "Resume").strip()

    # Retrieve job title from header or first experience role
    job_title = header.get("job_title") or header.get("title")
    if not job_title:
        exp = data.get("professional_experience", [])
        if exp and isinstance(exp, list) and len(exp) > 0:
            job_title = exp[0].get("role", "Resume")
        else:
            job_title = "Resume"

    # Clean and format: "SIDDH PATEL" -> "Siddh_Patel", "Lead Data Analyst" -> "Lead_Data_Analyst"
    name_parts = [w.capitalize() for w in re.findall(r'[A-Za-z0-9]+', name)]
    job_parts = [w.capitalize() for w in re.findall(r'[A-Za-z0-9]+', job_title)]

    name_str = "_".join(name_parts) if name_parts else "Resume"
    job_str = "_".join(job_parts) if job_parts else "Resume"

    filename = f"{name_str}_{job_str}.docx"
    return str(Path(output_dir) / filename)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a professional Word resume (.docx) from JSON data."
    )
    parser.add_argument(
        "--data",
        "-d",
        type=str,
        default="data/resume_data.json",
        help="Path to resume JSON data file (default: data/resume_data.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path for generated .docx file (default: output/<first>_<last>_<job_title>.docx)",
    )
    parser.add_argument(
        "--font",
        "-f",
        type=str,
        default=ResumeStyles.FONT_FAMILY,
        help=f"Font family to use throughout document (default: {ResumeStyles.FONT_FAMILY})",
    )

    args = parser.parse_args()

    print("========================================")
    print("      Resume Word Document Generator     ")
    print("========================================")
    print(f"Loading data from: {args.data}")
    data = ResumeDataLoader.load(args.data)

    output_path = args.output if args.output else get_default_output_path(data)

    print(f"Applying font family: {args.font}")
    builder = ResumeBuilder(font_family=args.font)

    print("Building sections...")
    builder.build(data)

    print(f"Saving output to: {output_path}")
    builder.save(output_path)
    print("========================================")
    print("Generation complete!")


if __name__ == "__main__":
    main()
