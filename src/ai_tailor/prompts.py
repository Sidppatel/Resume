"""
Prompt generation and template management for AI Resume Tailoring.
"""
import json
from typing import Dict, Any


class PromptBuilder:
    """
    Constructs specialized system instructions and context-rich user prompts
    for LLM resume optimization and ATS keyword alignment.
    """

    @staticmethod
    def build_system_prompt() -> str:
        """Builds the system instruction prompt for ATS optimization."""
        return (
            "You are an elite ATS resume optimization expert, senior technical recruiter, and executive career coach.\n"
            "Your task is to tailor a candidate's resume to match a specific Job Description (JD) with maximum keyword alignment, "
            "impact, and ATS scoring.\n\n"
            "### STRICT GUIDELINES:\n"
            "1. **Job Title**: Set `job_title` to the exact or best-matching target title from the JD.\n"
            "2. **Summary**: Write a compelling 3-4 sentence professional summary highlighting the candidate's core expertise, "
            "relevant domain knowledge from the JD, and standout metrics. Use **bold** syntax (e.g. `**Senior Data Analyst**`, `**reducing latency by 99%**`) for key skills and metrics.\n"
            "3. **Technical Skills**: Group relevant skills into clear categories (e.g. 'Languages', 'Data Engineering & Big Data', 'BI & Analytics', 'Cloud & DevOps'). Prioritize technologies, tools, and methodologies mentioned in the JD.\n"
            "4. **Professional Experience Bullets**: Tailor bullet points for each company to emphasize responsibilities, domain concepts (e.g., source-to-target mapping STTM, data pipelines, SQL optimization, data profiling, governance), and achievements relevant to the JD. "
            "Every bullet point MUST include markdown **bold** formatting for high-impact verbs, tools, and quantified metrics.\n"
            "5. **Key Projects**: Tailor project titles, tools, and bullets to emphasize projects and tech stacks most aligned with the JD.\n"
            "6. **Preserve Truth & Structure**: Maintain the candidate's core background, companies, and roles while phrasing and highlighting details to best fit the job description.\n"
            "7. **Output Format**: Respond ONLY with a valid JSON object matching the requested schema. Do NOT include extraneous conversational text."
        )

    @staticmethod
    def build_user_prompt(
        static_data: Dict[str, Any],
        current_resume: Dict[str, Any],
        jd_text: str
    ) -> str:
        """
        Builds the user prompt payload combining target JD, static profile context,
        and current resume data with the required JSON schema response specification.
        """
        # Determine company structure for prompt example if present
        exp_structure = static_data.get("professional_experience_structure", [])
        if not exp_structure:
            exp_structure = [
                {"company": item.get("company", ""), "role": item.get("role", "")}
                for item in current_resume.get("professional_experience", [])
            ]

        example_exp = []
        for item in exp_structure:
            example_exp.append({
                "company": item.get("company", "Company Name"),
                "role": item.get("role", "Role Name"),
                "bullets": [
                    "Action verb + tailored accomplishment with **bold** keywords and metrics..."
                ]
            })

        if not example_exp:
            example_exp = [
                {
                    "company": "Company Name",
                    "role": "Role Name",
                    "bullets": ["Action verb + tailored accomplishment with **bold** keywords and metrics..."]
                }
            ]

        return f"""### TARGET JOB DESCRIPTION:
```text
{jd_text}
```

### CANDIDATE'S CURRENT RESUME CONTEXT:
```json
{json.dumps(current_resume, indent=2)}
```

### INSTRUCTIONS:
Tailor the resume for the Job Description above. Return ONLY a JSON object with this EXACT structure:
{{
  "job_title": "Target Job Title matching JD",
  "summary": "Tailored summary with **bold** keywords and achievements...",
  "technical_skills": [
    {{
      "category": "Category Name",
      "skills": "Comma-separated skills list"
    }}
  ],
  "professional_experience": {json.dumps(example_exp, indent=4)},
  "key_projects": [
    {{
      "title": "Project Name",
      "tools": "Tool1, Tool2, Tool3",
      "dates": "2023 \u2013 2024",
      "bullets": [
        "Project bullet point with **bold** keywords..."
      ]
    }}
  ]
}}
"""
