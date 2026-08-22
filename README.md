# Executive AI Resume Suite

A modular, dual-engine Python system designed to tailor candidate resumes to any Job Description (JD) using **NVIDIA NIM DeepSeek V4 Flash** and generate executive-grade, ATS-compliant Word documents (`.docx`) using **python-docx**.

Built to adhere strictly to **Harvard / Wharton Career Guidelines**, **FAANG / Tech Lead** standards, and **The Resume Playbook by Wonsulting** ATS formatting rules.

---

## Architecture & Project Structure

The repository cleanly separates two independent projects while sharing a single **`data/`** directory as the single source of truth:

```text
Resume-New/
├── data/                                   # Single shared data repository
│   ├── jd.txt                              # Target Job Description (input for AI Tailor)
│   ├── jd.sample.txt                       # Sample Job Description template
│   ├── resume_data.json                    # Active/tailored resume data (output of Tailor, input to Builder)
│   ├── resume_data.sample.json             # Sample tailored resume data structure
│   ├── resume_static.json                  # Immutable candidate profile (contacts, companies, degrees)
│   └── resume_static.sample.json           # Sample static candidate profile
├── src/
│   ├── ai_tailor/                          # Project 1: AI Resume Tailoring Package
│   │   ├── __init__.py                     # Package exports
│   │   ├── config.py                       # TailorConfig dataclass & client factory
│   │   ├── prompts.py                      # PromptBuilder class (system & user prompts)
│   │   ├── parser.py                       # TailorResponseParser class (JSON cleaner & data merger)
│   │   └── engine.py                       # ResumeTailor class (streaming LLM pipeline)
│   └── resume_builder/                     # Project 2: Word Resume Document Generator Package
│       ├── __init__.py                     # Package exports
│       ├── styles.py                       # ResumeStyles class (margins, fonts, borders, tabs)
│       ├── schema.py                       # ResumeDataLoader class & defensive normalizer
│       └── builder.py                      # ResumeBuilder class (python-docx document engine)
├── ai_tailor.py                            # CLI entry point for AI Tailor
├── build_resume.py                         # CLI entry point for Word Document Resume Generator
├── output/                                 # Generated .docx resume documents
│   └── .gitkeep
├── requirements.txt                        # Shared dependency specification
├── .env.example                            # Template for API credentials
├── .gitignore                              # Git exclusion rules
└── README.md                               # Project documentation
```

---

## The Two Projects Explained

### 1. `ai_tailor` (Resume Optimization Engine)

* **Goal**: Analyzes a target Job Description (`data/jd.txt`) and dynamically optimizes your resume's **job title**, **summary**, **technical skills**, **experience bullet points**, and **projects** with exact keyword alignment, power verbs, and quantified metrics.
* **Core Engine**: Powered by NVIDIA NIM API (`deepseek-ai/deepseek-v4-flash-0731`) with live token and reasoning streaming.
* **Truth Preservation**: Blends dynamic AI content with verified static candidate profile data (`data/resume_static.json`), ensuring dates, employers, degrees, and contact details remain 100% accurate.

### 2. `resume_builder` (Executive Word Document Builder)

* **Goal**: Reads `data/resume_data.json` and produces an executive-grade `.docx` resume following gold-standard ATS specifications.
* **Visual Anchor**: Candidate name in `16.5pt` bold, followed by a contact line and a prominently framed **Target Job Title** with top & bottom borders.
* **Two-Column Alignment**: Word native tab stops at `7.5"` margin width for dates and locations.
* **True Hanging Indents**: Clean round bullet points (`•\t`) with `0.22"` hanging indents.
* **Dynamic Filenames**: Automatically generates `<First>_<Last>_<Job_Title>.docx` in `output/`.

---

## Quick Start

### 1. Install Dependencies

Both projects share the same dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (For AI Tailor)

Copy `.env.example` to `.env` and add your NVIDIA NIM API key:

```bash
cp .env.example .env
```

Inside `.env`:

```env
NVIDIA_API_KEY=nvapi-your-key-here
```

---

## Usage & Workflows

### Complete End-to-End Flow

```bash
# Step 1: Place your target job description into data/jd.txt

# Step 2: Tailor your resume data with AI (takes ~5-15 seconds)
python ai_tailor.py

# Step 3: Build the executive Word document resume (.docx)
python build_resume.py
```

Your generated resume will be waiting in `output/` (e.g. `output/Siddh_Patel_Lead_Data_Analyst.docx`).

---

## CLI Reference

### `ai_tailor.py` (Project 1)

```bash
python ai_tailor.py [OPTIONS]
```

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--jd` | `-j` | `data/jd.txt` | Path to target job description text file |
| `--static` | `-s` | `data/resume_static.json` | Path to candidate's verified static profile |
| `--data` | `-d` | `data/resume_data.json` | Path to current resume JSON |
| `--output` | `-o` | `data/resume_data.json` | Destination path for tailored JSON |
| `--fast` | `-f` | `False` | Fast mode: disables deep reasoning (~5-10s execution) |
| `--reasoning` | | `medium` | Reasoning effort level (`none`, `low`, `medium`, `high`) |
| `--show-reasoning` | `-r` | `False` | Stream DeepSeek's internal thinking process live in terminal |
| `--dry-run` | | `False` | Run AI tailoring without overwriting files |

#### AI Tailor Examples

```bash
# Standard tailoring with live progress spinner
python ai_tailor.py

# Ultra-fast mode (~5 seconds)
python ai_tailor.py --fast

# Deep reasoning mode with live thought streaming
python ai_tailor.py --reasoning high --show-reasoning

# Test without saving changes
python ai_tailor.py --dry-run
```

---

### `build_resume.py` (Project 2)

```bash
python build_resume.py [OPTIONS]
```

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--data` | `-d` | `data/resume_data.json` | Path to resume JSON data file |
| `--output` | `-o` | Auto-generated | Custom output file destination |
| `--font` | `-f` | `Times New Roman` | Global font family override |

#### Resume Builder Examples

```bash
# Build using standard settings
python build_resume.py

# Build using sample data
python build_resume.py --data data/resume_data.sample.json

# Custom output destination and font override
python build_resume.py --output "output/Custom_Resume.docx" --font "Garamond"
```

---

## Programmatic Python API

Both packages can be imported and used directly in your Python applications:

```python
# Import from Project 1 (AI Tailor)
from src.ai_tailor import ResumeTailor, TailorConfig

config = TailorConfig(fast=True)
tailor = ResumeTailor(config=config)
merged_data, reasoning = tailor.tailor(
    jd_path="data/jd.txt",
    output_path="data/resume_data.json"
)

# Import from Project 2 (Resume Builder)
from src.resume_builder import ResumeBuilder, ResumeDataLoader

data = ResumeDataLoader.load("data/resume_data.json")
builder = ResumeBuilder(font_family="Times New Roman")
builder.build(data)
builder.save("output/My_Tailored_Resume.docx")
```

---

## Data Schema Reference

See `data/resume_data.sample.json` and `data/resume_static.sample.json` for full examples.

```json
{
  "header": {
    "name": "FIRST LAST",
    "job_title": "Target Role from JD",
    "contact": {
      "location": "City, State",
      "phone": "(123) 456-7890",
      "email": "name@email.com",
      "linkedin": "linkedin.com/in/profile",
      "github": "github.com/profile"
    }
  },
  "summary": "Impact-driven summary with **bold** keywords...",
  "technical_skills": [
    {
      "category": "Languages",
      "skills": "Python, SQL, R"
    }
  ],
  "professional_experience": [
    {
      "company": "COMPANY NAME",
      "location": "City, State",
      "role": "Job Title",
      "dates": "Jan 2023 – Present",
      "bullets": [
        "Action verb + achievement with **quantified metric**..."
      ]
    }
  ],
  "key_projects": [
    {
      "title": "Project Name",
      "tools": "Tool1, Tool2",
      "dates": "2023 – 2024",
      "bullets": [
        "Project accomplishment bullet point..."
      ]
    }
  ],
  "education_and_certifications": [
    {
      "institution": "University Name",
      "title": "Degree Name",
      "dates": "2018 – 2022",
      "bullets": []
    }
  ]
}
```
