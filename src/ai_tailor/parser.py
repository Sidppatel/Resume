"""
Response parsing, JSON extraction, and data merging for AI Resume Tailoring.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Union


class TailorResponseParser:
    """
    Handles file I/O, raw LLM JSON extraction/cleaning, and merging of
    dynamic tailored content with the candidate's static profile.
    """

    @staticmethod
    def load_text_file(file_path: Union[str, Path]) -> str:
        """Reads and returns text content from a file (supports UTF-8)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

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
        Strips markdown code fences, isolates JSON structure, and parses into Python dict.
        """
        text = raw_text.strip()

        # Remove markdown code fences if present (```json ... ``` or ``` ...)
        if "```" in text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                text = match.group(1).strip()

        # Attempt to locate outer JSON braces if there's leading/trailing noise
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]

        return json.loads(text)

    @classmethod
    def merge_resume_data(
        cls,
        static_data: Dict[str, Any],
        dynamic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merges static candidate profile (name, contact, dates, verified education)
        with AI-tailored dynamic fields (job title, summary, skills, experience bullets, projects).
        """
        merged: Dict[str, Any] = {}

        # 1. Header: Contact and static name, AI-tailored target Job Title
        header = dict(static_data.get("header", {}))
        if "job_title" in dynamic_data and dynamic_data["job_title"]:
            header["job_title"] = dynamic_data["job_title"]
        merged["header"] = header

        # 2. Summary from dynamic response
        merged["summary"] = dynamic_data.get("summary", "")

        # 3. Technical Skills from dynamic response
        merged["technical_skills"] = dynamic_data.get("technical_skills", [])

        # 4. Professional Experience: Static company/role/dates + AI-tailored bullets
        static_exp = static_data.get("professional_experience_structure", [])
        dynamic_exp = dynamic_data.get("professional_experience", [])

        merged_exp = []
        for i, exp_item in enumerate(static_exp):
            comp = exp_item.get("company", "")
            role = exp_item.get("role", "")
            loc = exp_item.get("location", "")
            dates = exp_item.get("dates", "")

            # Match bullets from dynamic response by index or company name
            bullets = []
            if i < len(dynamic_exp):
                bullets = dynamic_exp[i].get("bullets", [])
            else:
                for d in dynamic_exp:
                    if d.get("company", "").strip().lower() == comp.strip().lower():
                        bullets = d.get("bullets", [])
                        break

            exp_dict = {
                "company": comp,
                "location": loc,
                "role": role,
                "dates": dates,
                "bullets": bullets
            }
            if "industry" in exp_item:
                exp_dict["industry"] = exp_item["industry"]
            if "overview" in exp_item:
                exp_dict["overview"] = exp_item["overview"]
            merged_exp.append(exp_dict)

        # If static profile had no explicit experience structure, fallback to dynamic
        if not merged_exp and dynamic_exp:
            merged_exp = dynamic_exp

        merged["professional_experience"] = merged_exp

        # 5. Key Projects from dynamic response (defensively sanitize against certification leaks)
        dynamic_projects = dynamic_data.get("key_projects", [])
        static_edu = static_data.get("education_and_certifications", [])

        # Collect titles and institutions from static education to prevent duplication
        edu_keywords = {"fellowship", "coursera", "certificate", "certification", "degree", "diploma", "bachelor", "master"}
        for item in static_edu:
            t = item.get("title", "").lower()
            inst = item.get("institution", "").lower()
            if t:
                edu_keywords.add(t)
            if inst:
                edu_keywords.add(inst)

        sanitized_projects = []
        for proj in dynamic_projects:
            proj_title = proj.get("title", "").strip()
            proj_title_lower = proj_title.lower()

            # Skip if project title directly matches an education title or known certification phrase
            is_edu_dup = any(
                edu_kw in proj_title_lower for edu_kw in [
                    "fellowship", "coursera", "certificate", "certification",
                    "data analytics professional", "data science professional"
                ]
            ) or any(
                proj_title_lower == item.get("title", "").strip().lower() for item in static_edu
            )

            if not is_edu_dup and proj_title:
                sanitized_projects.append(proj)

        # Fallback to dynamic_projects if sanitization emptied the list unexpectedly
        merged["key_projects"] = sanitized_projects if sanitized_projects else dynamic_projects

        # 6. Education and Certifications from static verified profile
        merged["education_and_certifications"] = static_edu

        return merged
