"""
Prompt generation and template management for AI Resume Tailoring.
"""
import json
from typing import Dict, Any, Optional


class PromptBuilder:
    """
    Constructs specialized system instructions and context-rich user prompts
    for LLM resume optimization and ATS keyword alignment with strict Job Title & Employer Domain Fidelity.
    """

    @staticmethod
    def build_system_prompt() -> str:
        """Builds the system instruction prompt for ATS optimization."""
        return (
            "You are an elite ATS resume optimization expert, senior technical recruiter, and executive career coach.\n"
            "Your task is to tailor a candidate's resume to match a specific Job Description (JD) with maximum keyword alignment, "
            "impact, and ATS scoring while strictly adhering to JOB TITLE FIDELITY and EMPLOYER DOMAIN INTEGRITY.\n\n"
            "### STRICT GUIDELINES & INTEGRITY RULES:\n\n"
            "1. **TARGET JOB TITLE**:\n"
            "   - Set `job_title` to the exact or best-matching target title from the JD.\n\n"
            "2. **PROFESSIONAL SUMMARY**:\n"
            "   - Write a compelling 3-4 sentence summary highlighting the candidate's core expertise, relevant technical strengths from the JD, and standout metrics.\n"
            "   - Use markdown **bold** formatting for core skills, key tools, and high-impact metrics (e.g., `**Senior Data Engineer**`, `**reducing processing latency by 60%**`).\n"
            "   - When the JD is in a specialized industry (e.g., Banking, Credit Risk, Healthcare), frame the summary around the candidate's enterprise data capabilities and readiness to drive data platforms in that domain.\n\n"
            "3. **TECHNICAL SKILLS**:\n"
            "   - Group skills into 5-6 clear, high-relevance categories matching the JD (e.g., 'Programming & Scripting', 'Data Engineering & Big Data', 'BI & Analytics', 'Cloud & DevOps', 'Data Quality & Governance', 'Agile & Methodologies').\n"
            "   - Prioritize all technologies, tools, and platforms mentioned in the JD that match the candidate's core capabilities.\n\n"
            "4. **WORK EXPERIENCE - STRICT JOB TITLE & DOMAIN FIDELITY (CRITICAL)**:\n"
            "   - **JOB TITLE FIDELITY**: Bullet points for each work experience entry MUST authentically match the candidate's ACTUAL job title, seniority level, and role scope:\n"
            "     * *Business Intelligence Developer*: Focus on BI data models, Power BI/Tableau reports, DAX, enterprise dashboards, data pipelines feeding reporting layers, SQL query optimization, automated reporting workflows, and stakeholder self-service.\n"
            "     * *Application Developer*: Focus on custom software applications, REST APIs, Python & SQL backend data pipelines, event streaming (Kafka/Spark), script automation, data profiling, and CI/CD.\n"
            "     * *Application Support Analyst*: Focus on tier-2/3 technical support, SharePoint / Power Platform workflows, user acceptance testing (UAT), regression testing, data validation, system troubleshooting, and incident resolution.\n"
            "   - **ZERO FALSE DOMAIN INJECTION (EMPLOYER INTEGRITY)**:\n"
            "     * **NEVER** fabricate or inject the target JD's specialized business domain (e.g., banking/counterparty credit risk, trading desks, clinical healthcare, retail e-commerce, insurance claims) into past employers where they do NOT belong (e.g., shipbuilding/defense manufacturing, EPC, hospitality, retail).\n"
            "     * Ground past work bullets 100% in the employer's genuine industry and operational context (e.g., naval shipbuilding, production efficiency, vessel manufacturing data, supply chain, engineering quality, ERP integrations, EPC projects).\n"
            "   - **TRANSFERABLE TECHNICAL ALIGNMENT (HOW TO MATCH THE JD)**:\n"
            "     * Emphasize the candidate's **transferable technical capabilities, engineering tools, and methodologies** demanded by the JD (e.g., Python, SQL, Apache Spark, Power BI, Apache Iceberg, Dremio, REST APIs, CI/CD with Azure DevOps, Agile/Scrum, data profiling, query optimization, test automation) applied authentically within the candidate's real employer operations.\n"
            "   - **FORMATTING**: Every bullet point MUST begin with a powerful past-tense action verb and include markdown **bold** formatting for high-impact verbs, tools, and quantified metrics.\n\n"
            "5. **TECHNICAL PROJECTS (DOMAIN BRIDGING & ADVANCED TECH STACK)**:\n"
            "   - **NEVER** copy, rebrand, convert, or reuse items from Education & Certifications (e.g., University degrees, Google Certificates, IBM Certificates, Palantir Fellowships, Coursera courses) as projects.\n"
            "   - In `key_projects`, synthesize 2 to 3 distinct, high-impact **TECHNICAL PROJECTS** directly tailored to the target **Job Title** and target **JD's domain and core technologies** (e.g., Counterparty Risk Analytics Pipeline, Scalable Automated ETL Framework, Enterprise BI Platform, Spark/Kafka streaming, Iceberg, Dremio, Docker, Kubernetes, CI/CD, etc.).\n"
            "   - Each project MUST include:\n"
            "     - `title`: Enterprise-grade project name directly aligned with the target role and domain.\n"
            "     - `tools`: Comma-separated list of core technologies and platforms used.\n"
            "     - `dates`: Year or range (e.g., '2023 \u2013 2024' or '2024').\n"
            "     - `bullets`: EXACTLY 2 structured, high-impact bullets following this format:\n"
            "       - Bullet 1: `**Execution & Impact:** <Technical architecture, pipeline/model/framework design, tools used, data scale/volume, and bold keywords>`\n"
            "       - Bullet 2: `**Business Outcome:** <Quantified business results, efficiency gains, defect/waste reduction, uptime improvements, with bold metrics>`\n\n"
            "6. **AI TRANSPARENCY & REASONING**:\n"
            "   - DeepSeek's thinking process must explicitly evaluate:\n"
            "     1. JD technical competencies vs. target industry domain.\n"
            "     2. Candidate's authentic employer industries (e.g., Shipbuilding/Manufacturing at Austal-USA) and exact job titles.\n"
            "     3. Role-by-role strategy ensuring bullets strictly match the job title and employer domain while emphasizing JD technical skills.\n"
            "     4. How Key Projects and Summary bridge any domain-specific requirements.\n\n"
            "7. **OUTPUT FORMAT**:\n"
            "   - Respond ONLY with a valid JSON object matching the requested schema. Do NOT include extraneous conversational text."
        )

    @staticmethod
    def build_user_prompt(
        static_data: Dict[str, Any],
        current_resume: Dict[str, Any],
        jd_text: str,
        knowledge_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Builds the user prompt payload combining target JD, static profile context,
        optional career domain knowledge, and current resume data with the required JSON schema response specification.
        """
        # Determine company structure for prompt example if present
        exp_structure = static_data.get("professional_experience_structure", [])
        if not exp_structure:
            exp_structure = [
                {
                    "company": item.get("company", ""),
                    "role": item.get("role", ""),
                    "industry": item.get("industry", ""),
                    "core_focus": item.get("core_focus", "")
                }
                for item in current_resume.get("professional_experience", [])
            ]

        example_exp = []
        for item in exp_structure:
            role_name = item.get("role", "Role Name")
            ind_name = item.get("industry", "company industry")
            example_exp.append({
                "company": item.get("company", "Company Name"),
                "role": role_name,
                "bullets": [
                    f"Action verb + tailored accomplishment for {role_name} in {ind_name} with **bold** tools and metrics..."
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

        knowledge_block = ""
        if knowledge_data and "companies" in knowledge_data:
            knowledge_block = f"""### CANDIDATE'S VERIFIED CAREER & EMPLOYER DOMAIN KNOWLEDGE (GROUND TRUTH):
```json
{json.dumps(knowledge_data, indent=2)}
```

"""

        return f"""### TARGET JOB DESCRIPTION:
```text
{jd_text}
```

### CANDIDATE'S VERIFIED PROFILE & WORK HISTORY CONTEXT:
```json
{json.dumps(static_data, indent=2)}
```

{knowledge_block}### CRITICAL RULES FOR THIS RESUME GENERATION:
1. **JOB TITLE & DOMAIN FIDELITY (STRICT GROUNDING)**:
   - For each role in `professional_experience`, write bullets that strictly match the candidate's ACTUAL job title, authentic employer industry operations, domain KPIs, and role scope.
   - If Career Domain Knowledge is provided above, use it as your authoritative source of truth for each employer's operations, technology environment, and domain boundary rules.
   - **DO NOT** inject target company/industry domain terms (such as counterparty credit risk, trading, capital markets, clinical healthcare) into past employers where they are not relevant.
   - Align with the JD by highlighting **transferable technical capabilities** (e.g. Python, SQL, Spark, Power BI, data pipelines, ETL, query optimization, CI/CD, Agile, data quality) applied to the candidate's real operational and manufacturing/engineering data systems.
2. **TECHNICAL PROJECTS (DOMAIN BRIDGING)**:
   - In `key_projects`, generate 2 to 3 enterprise-grade, realistic technical projects directly tailored to the target Job Description domain and required technical stack (e.g., Counterparty Risk Analytics Pipeline, Scalable Automated ETL Framework, Enterprise BI Platform).
3. **DO NOT** reuse or copy any certifications, degrees, or fellowships (like Google Data Analytics, IBM Data Science, Palantir Fellowship, etc.) into `key_projects`. Certifications belong strictly in education.
4. Every project under `key_projects` MUST use the two structured bullets: `**Execution & Impact:** ...` and `**Business Outcome:** ...`.

### REQUIRED JSON OUTPUT STRUCTURE:
Return ONLY a valid JSON object matching this EXACT schema:
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
      "title": "Enterprise Real-Time BI & Product Performance Platform",
      "tools": "Power BI, Python (Plotly, Pandas), SQL Server, Apache Spark, IoT JSON Streams",
      "dates": "2023 \u2013 2024",
      "bullets": [
        "**Execution & Impact:** Formulated automated data pipelines via **Spark** to ingest and wrangle **500K+ daily records** from disparate databases. Developed statistical tracking systems and **Python** scripts for real-time anomaly detection across **15+ complex product performance KPIs**.",
        "**Business Outcome:** Substantially influenced executive decision-making, **reducing material waste by 30%** through historical trend mapping, **increasing assembly line uptime by 22%** via predictive modeling, and **cutting cross-departmental meeting overhead by 35%** via centralized data storytelling."
      ]
    }},
    {{
      "title": "Scalable Compliance ETL Pipeline & Causal Analysis Framework",
      "tools": "Python (PySpark, Pandas), Docker, Kubernetes, SQL Server, Azure DevOps",
      "dates": "2022 \u2013 2023",
      "bullets": [
        "**Execution & Impact:** Built a robust, parallel processing data onboarding pipeline handling **2M+ daily rows** from **20+ unstructured and streaming sources**. Applied structured analytics methodologies (**CRISP-DM**) and automated data lineage tracking to align with strict **ISO 9001** quality compliance standards.",
        "**Business Outcome:** Accelerated data onboarding for new cross-functional projects by **60%**, expanded Quality Assurance compliance audit pass rates by **18%**, and enabled **95% faster root-cause analysis** by correlating disparate data streams."
      ]
    }}
  ]
}}
"""
