"""
Data schema loader and defensive normalizer for resume JSON data.
Handles diverse data schemas, aliases, and missing fields defensively.
"""
import json
from pathlib import Path
from typing import Dict, Any, Union


class ResumeDataLoader:
    """
    Loads, validates, and defensively normalizes resume JSON data schemas.
    """

    @classmethod
    def normalize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes resume data structure to support various schema aliases and formats.
        """
        normalized = {}

        # 1. Header normalization
        header = data.get("header", {})
        if not isinstance(header, dict):
            header = {"name": str(header)}

        # Check top-level name / title if header is flat
        if "name" not in header and "name" in data:
            header["name"] = data["name"]
        if "job_title" not in header and "title" in header:
            header["job_title"] = header["title"]
        elif "job_title" not in header and "target_title" in header:
            header["job_title"] = header["target_title"]
        elif "job_title" not in header and "job_title" in data:
            header["job_title"] = data["job_title"]

        normalized["header"] = header

        # 2. Professional Summary
        summary = (
            data.get("summary") or
            data.get("professional_summary") or
            data.get("profile") or
            data.get("about") or
            ""
        )
        normalized["summary"] = summary.strip() if isinstance(summary, str) else ""

        # 3. Technical Skills normalization
        skills = (
            data.get("technical_skills") or
            data.get("skills") or
            data.get("core_competencies") or
            []
        )
        normalized_skills = []
        if isinstance(skills, list):
            for item in skills:
                if isinstance(item, dict):
                    cat = item.get("category") or item.get("name") or item.get("group") or ""
                    val = item.get("skills") or item.get("items") or item.get("value") or ""
                    if isinstance(val, list):
                        val = ", ".join(str(v) for v in val)
                    if cat or val:
                        normalized_skills.append({
                            "category": str(cat).strip(),
                            "skills": str(val).strip()
                        })
                elif isinstance(item, str) and item.strip():
                    if ":" in item:
                        cat, val = item.split(":", 1)
                        normalized_skills.append({
                            "category": cat.strip(),
                            "skills": val.strip()
                        })
                    else:
                        normalized_skills.append({
                            "category": "",
                            "skills": item.strip()
                        })
        elif isinstance(skills, dict):
            for k, v in skills.items():
                val_str = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
                normalized_skills.append({
                    "category": str(k).strip(),
                    "skills": val_str.strip()
                })
        normalized["technical_skills"] = normalized_skills

        # 4. Work Experience normalization
        exp = (
            data.get("professional_experience") or
            data.get("work_experience") or
            data.get("experience") or
            []
        )
        normalized_exp = []
        if isinstance(exp, list):
            for item in exp:
                if isinstance(item, dict):
                    company = (
                        item.get("company") or
                        item.get("organization") or
                        item.get("employer") or
                        ""
                    )
                    location = item.get("location") or item.get("city") or ""
                    role = (
                        item.get("role") or
                        item.get("title") or
                        item.get("position") or
                        item.get("job_title") or
                        ""
                    )
                    dates = (
                        item.get("dates") or
                        item.get("date") or
                        item.get("period") or
                        item.get("duration") or
                        ""
                    )
                    overview = item.get("overview") or item.get("summary") or ""
                    bullets_raw = (
                        item.get("bullets") or
                        item.get("highlights") or
                        item.get("responsibilities") or
                        item.get("points") or
                        []
                    )

                    bullets = []
                    if isinstance(bullets_raw, list):
                        for b in bullets_raw:
                            if isinstance(b, dict):
                                tag = b.get("tag") or b.get("prefix") or ""
                                txt = b.get("text") or b.get("content") or ""
                                if tag and not txt.startswith(f"{tag}:"):
                                    bullets.append(f"**{tag}:** {txt}")
                                else:
                                    bullets.append(txt)
                            elif isinstance(b, str) and b.strip():
                                bullets.append(b.strip())
                    elif isinstance(bullets_raw, str) and bullets_raw.strip():
                        bullets.append(bullets_raw.strip())

                    normalized_exp.append({
                        "company": str(company).strip(),
                        "location": str(location).strip(),
                        "role": str(role).strip(),
                        "dates": str(dates).strip(),
                        "overview": str(overview).strip(),
                        "bullets": bullets
                    })
        normalized["professional_experience"] = normalized_exp

        # 5. Key Projects normalization
        projects = (
            data.get("key_projects") or
            data.get("projects") or
            data.get("technical_projects") or
            []
        )
        normalized_projects = []
        if isinstance(projects, list):
            for item in projects:
                if isinstance(item, dict):
                    title = (
                        item.get("title") or
                        item.get("name") or
                        item.get("project_name") or
                        ""
                    )
                    tools = (
                        item.get("tools") or
                        item.get("technologies") or
                        item.get("tech_stack") or
                        ""
                    )
                    if isinstance(tools, list):
                        tools = ", ".join(str(t) for t in tools)
                    dates = (
                        item.get("dates") or
                        item.get("date") or
                        item.get("duration") or
                        ""
                    )
                    bullets_raw = (
                        item.get("bullets") or
                        item.get("highlights") or
                        item.get("points") or
                        []
                    )

                    bullets = []
                    if isinstance(bullets_raw, list):
                        for b in bullets_raw:
                            if isinstance(b, dict):
                                tag = b.get("tag") or b.get("prefix") or ""
                                txt = b.get("text") or b.get("content") or ""
                                if tag and not txt.startswith(f"{tag}:"):
                                    bullets.append(f"**{tag}:** {txt}")
                                else:
                                    bullets.append(txt)
                            elif isinstance(b, str) and b.strip():
                                bullets.append(b.strip())
                    elif isinstance(bullets_raw, str) and bullets_raw.strip():
                        bullets.append(bullets_raw.strip())

                    normalized_projects.append({
                        "title": str(title).strip(),
                        "tools": str(tools).strip(),
                        "dates": str(dates).strip(),
                        "bullets": bullets
                    })
        normalized["key_projects"] = normalized_projects

        # 6. Education & Certifications normalization
        edu = (
            data.get("education_and_certifications") or
            data.get("education") or
            data.get("certifications") or
            []
        )
        normalized_edu = []
        if isinstance(edu, list):
            for item in edu:
                if isinstance(item, dict):
                    inst = (
                        item.get("institution") or
                        item.get("school") or
                        item.get("issuer") or
                        item.get("organization") or
                        ""
                    )
                    title = (
                        item.get("title") or
                        item.get("degree") or
                        item.get("certificate") or
                        item.get("program") or
                        ""
                    )
                    dates = (
                        item.get("dates") or
                        item.get("date") or
                        item.get("year") or
                        item.get("graduation_date") or
                        ""
                    )
                    cred_id = item.get("credential_id") or item.get("id") or ""
                    bullets_raw = (
                        item.get("bullets") or
                        item.get("details") or
                        item.get("description") or
                        []
                    )

                    bullets = []
                    if isinstance(bullets_raw, list):
                        for b in bullets_raw:
                            if isinstance(b, str) and b.strip():
                                bullets.append(b.strip())
                    elif isinstance(bullets_raw, str) and bullets_raw.strip():
                        bullets.append(bullets_raw.strip())

                    normalized_edu.append({
                        "institution": str(inst).strip(),
                        "title": str(title).strip(),
                        "dates": str(dates).strip(),
                        "credential_id": str(cred_id).strip(),
                        "bullets": bullets
                    })
        normalized["education_and_certifications"] = normalized_edu

        return normalized

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load, parse, and normalize resume JSON data from file.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume data file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.normalize(data)


# Backward-compatible helper functions
def normalize_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return ResumeDataLoader.normalize(data)


def load_resume_data(file_path: Union[str, Path]) -> Dict[str, Any]:
    return ResumeDataLoader.load(file_path)
