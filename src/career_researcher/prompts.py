"""
Prompt construction for deep AI career, company, and role domain research.
"""
import json
from typing import Dict, Any


class ResearchPromptBuilder:
    """
    Constructs specialized system and user prompts to guide NVIDIA DeepSeek V4 Flash
    in conducting deep, authentic research into employer industries, operational tech environments,
    domain KPIs, and strict role boundary rules.
    """

    @staticmethod
    def build_system_prompt() -> str:
        """Builds system prompt for deep industry, technology, and role research."""
        return (
            "You are a principal enterprise technology researcher, industry analyst, and executive career architect.\n"
            "Your task is to conduct deep, comprehensive research into a candidate's past employers, industries, and specific job titles.\n\n"
            "### OBJECTIVES:\n"
            "1. **Company & Industry Authenticity**: For each employer, identify its exact core business model, products/services, physical or digital operations, and typical enterprise technical environment.\n"
            "2. **Domain KPIs & Metrics**: Identify genuine operational metrics, performance indicators, and business benchmarks authentic to that industry (e.g., naval shipbuilding = vessel production throughput, labor hours, material procurement lead time, quality audit pass rates; EPC = engineering schedule variance, commissioning milestones, UAT pass rates).\n"
            "3. **Role & Title Deep Dive**: For each specific job title at that company:\n"
            "   - Detail the realistic day-to-day scope, architecture focus, and core responsibilities.\n"
            "   - List high-value **transferable technical capabilities** (e.g. Python, SQL, Power BI, Spark, ETL, CI/CD, Agile, Data Quality) applied in that employer's domain.\n"
            "   - Define **Domain Boundary Rules**: Explicitly list what belongs in this role versus what must **NEVER** be hallucinated (e.g. NEVER inject banking/credit risk or Wall Street capital markets into a shipbuilding or construction company).\n"
            "4. **Output Format**: Respond ONLY with a valid JSON object matching the requested schema. Do NOT include extraneous conversational text."
        )

    @staticmethod
    def build_user_prompt(static_data: Dict[str, Any]) -> str:
        """Builds user prompt for company & role research."""
        candidate_name = static_data.get("header", {}).get("name", "Candidate")
        exp_structure = static_data.get("professional_experience_structure", [])
        edu_list = static_data.get("education_and_certifications", [])

        return f"""### CANDIDATE PROFILE CONTEXT:
Candidate Name: {candidate_name}

Verified Work History Structure:
{json.dumps(exp_structure, indent=2)}

Education & Certifications Background:
{json.dumps(edu_list, indent=2)}

### INSTRUCTIONS:
Conduct an exhaustive, expert industry and technological deep-dive into each company and role listed in the candidate's work history.
Return ONLY a valid JSON object matching this EXACT schema:
{{
  "candidate_name": "{candidate_name}",
  "generated_at": "ISO-8601 Timestamp",
  "companies": [
    {{
      "company": "Company Name Exactly as in Static Profile",
      "industry": "Specific Primary Industry (e.g. Naval Shipbuilding & Defense Manufacturing)",
      "core_operations": "2-3 sentences explaining what this business actually designs, manufactures, or delivers, its clients, and physical/operational scale.",
      "enterprise_tech_environment": "Detailed breakdown of typical software, ERP, PLM, SCADA/IoT, databases, and reporting systems used in this company's operations.",
      "domain_kpis_and_metrics": "Key business and operational metrics authentic to this industry (e.g., vessel milestone completion, labor efficiency variance, rework percentage, supply chain lead time, engineering change notices).",
      "roles": [
        {{
          "role": "Job Title Exactly as in Static Profile",
          "scope_and_responsibilities": "Comprehensive explanation of what this role does day-to-day within this specific employer and industry.",
          "transferable_technical_skills": [
            "Skill 1 (e.g. SQL / T-SQL)",
            "Skill 2 (e.g. Power BI / DAX)",
            "Skill 3 (e.g. Python)",
            "Skill 4 (e.g. ETL & Data Pipelines)"
          ],
          "domain_boundary_rules": {{
            "what_to_include": "Specific operational workflows, manufacturing/engineering metrics, and authentic data processes appropriate for this role at this company.",
            "what_never_to_include": "Strict list of irrelevant domains that MUST NEVER be hallucinated or attributed to this employer (e.g. NEVER include financial trading, banking credit risk, clinical healthcare, or retail e-commerce)."
          }}
        }}
      ]
    }}
  ]
}}
"""
