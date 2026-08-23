# Executive AI Resume Suite

A modular, multi-engine Python system designed to research candidate employers, tailor resumes to any Job Description (JD) using **NVIDIA NIM DeepSeek V4 Flash**, and generate executive-grade, ATS-compliant Word documents (`.docx`) using **python-docx**.

Built to adhere strictly to **Harvard / Wharton Career Guidelines**, **FAANG / Tech Lead** standards, and **The Resume Playbook by Wonsulting** ATS formatting rules.

---

## Architecture & Project Structure

The repository cleanly separates independent modules while sharing a single **`data/`** directory as the single source of truth:

```text
Resume-New/
├── data/                                   # Single shared data repository
│   ├── jd.txt                              # Target Job Description (input for AI Tailor)
│   ├── jd.sample.txt                       # Sample Job Description template
│   ├── resume_data.json                    # Active/tailored resume data (output of Tailor, input to Builder)
│   ├── resume_data.sample.json             # Sample tailored resume data structure
│   ├── resume_static.json                  # Immutable candidate profile (contacts, companies, degrees)
│   ├── resume_static.sample.json           # Sample static candidate profile
│   ├── career_knowledge.json               # AI-researched employer domain knowledge & role boundaries
│   └── resume_vault.db                     # Local SQLite database (queries, reasoning, and tailored data)
├── src/
│   ├── ai_tailor/                          # Project 1: AI Resume Tailoring Package
│   │   ├── __init__.py                     # Package exports
│   │   ├── config.py                       # TailorConfig dataclass & client factory
│   │   ├── prompts.py                      # PromptBuilder class (system & user prompts with knowledge grounding)
│   │   ├── parser.py                       # TailorResponseParser class (JSON cleaner & data merger)
│   │   └── engine.py                       # ResumeTailor class (streaming LLM pipeline with knowledge auto-load)
│   ├── career_researcher/                  # Project 2: AI Career Domain & Employer Researcher Package
│   │   ├── __init__.py                     # Package exports (CareerKnowledgeResearcher, ResearcherConfig)
│   │   ├── config.py                       # ResearcherConfig dataclass & client factory
│   │   ├── prompts.py                      # ResearchPromptBuilder class (system & user prompts for deep research)
│   │   ├── parser.py                       # KnowledgeResponseParser class (JSON cleaner & file loader)
│   │   └── engine.py                       # CareerKnowledgeResearcher class (streaming research engine & DB archival)
│   ├── resume_builder/                     # Project 3: Word Resume Document Generator Package
│   │   ├── __init__.py                     # Package exports
│   │   ├── styles.py                       # ResumeStyles class (margins, fonts, borders, tabs)
│   │   ├── schema.py                       # ResumeDataLoader class & defensive normalizer
│   │   └── builder.py                      # ResumeBuilder class (python-docx document engine)
│   └── db/                                 # Project 4: Local SQLite Database & Repository Package
│       ├── __init__.py                     # Package exports (ResumeDatabase, get_db)
│       └── database.py                     # SQLite connection, schema, session logging & queries
├── research_profile.py                     # CLI entry point for AI Career & Company Domain Research
├── ai_tailor.py                            # CLI entry point for AI Tailor
├── build_resume.py                         # CLI entry point for Word Document Resume Generator
├── history.py                              # CLI entry point for Resume Vault history & query manager
├── output/                                 # Generated .docx resume documents
│   └── .gitkeep
├── requirements.txt                        # Shared dependency specification
├── .env.example                            # Template for API credentials
├── .gitignore                              # Git exclusion rules
└── README.md                               # Project documentation
```

---

## The Core Engines Explained

### 1. `research_profile.py` (AI Career & Domain Researcher)

* **Goal**: Analyzes your verified static profile (`data/resume_static.json`) and performs exhaustive AI research into each employer's genuine industry, core operations, enterprise technical environment, standard domain KPIs, and role boundary rules.
* **Ground Truth Output**: Saves structured domain knowledge to `data/career_knowledge.json` (or profile-specific files like `career_knowledge-Vidhi.json`).
* **Zero Hallucinations Guarantee**: Defines what belongs in each role vs. what must NEVER be hallucinated (e.g., prevents injecting banking/credit risk into shipbuilding companies).

### 2. `ai_tailor` (Resume Optimization Engine)

* **Goal**: Analyzes a target Job Description (`data/jd.txt`) and dynamically optimizes your resume's **job title**, **summary**, **technical skills**, **experience bullet points**, and **projects** with exact keyword alignment, power verbs, and quantified metrics.
* **Knowledge Grounding**: Automatically detects and loads `data/career_knowledge.json` to ground past work bullets in verified employer realities.
* **Job Title & Domain Fidelity**:
  * **Title Accuracy**: Experience bullet points strictly match the candidate's actual job title (e.g. BI Developer focuses on BI dashboards, DAX, data models; Application Developer focuses on APIs and software pipelines; Support Analyst focuses on tier-2/3 support and UAT).
  * **Domain Integrity**: Protects against false domain transplanting (e.g. prevents injecting banking/credit risk duties into a shipbuilding manufacturing employer like Austal-USA).
  * **Transferable Technical Matching**: Highlights transferable technical tools (Python, SQL, Spark, Power BI, ETL, CI/CD, Agile) applied within the candidate's authentic employer operations.
  * **Domain Bridging via Projects**: Complex target domain platforms (e.g. Counterparty Credit Risk pipelines) are showcased in dedicated **Technical Projects** (`key_projects`) and the **Professional Summary**.
* **Truth Preservation**: Blends dynamic AI content with verified static candidate profile data (`data/resume_static.json`), ensuring dates, employers, degrees, and contact details remain 100% accurate.

### 3. `resume_builder` (Executive Word Document Builder)

* **Goal**: Reads `data/resume_data.json` and produces an executive-grade `.docx` resume following gold-standard ATS specifications.
* **Visual Anchor**: Candidate name in `16.5pt` bold, followed by a contact line and a prominently framed **Target Job Title** with top & bottom borders.
* **Two-Column Alignment**: Word native tab stops at `7.5"` margin width for dates and locations.
* **True Hanging Indents**: Clean round bullet points (`•\t`) with `0.22"` hanging indents.
* **Dynamic Filenames**: Automatically generates `<First>_<Last>_<Job_Title>.docx` in `output/`.

### 4. `history` & `src/db` (Local SQLite Resume Vault)

* **Goal**: Automatically archives every target Job Description query, AI reasoning/thinking trace, prompts, and complete tailored resume JSON into a local zero-config SQLite database (`data/resume_vault.db`).
* **Instant Search & Restore**: Search past applications by job title, skills, or JD keywords, and restore any previous resume snapshot back into `data/resume_data.json` at any time.
* **Usage & Token Analytics**: Inspect total sessions, average latency, tokens generated, and top tailored job titles.

---

## Quick Start

### 1. Install Dependencies

Both projects share the same dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (For AI Tailor & Researcher)

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
# Step 1 (One-Time / As Needed): Research candidate employers and generate career domain knowledge
python research_profile.py

# Step 2: Place your target job description into data/jd.txt

# Step 3: Tailor your resume data with AI (auto-loads career knowledge and archives to local DB)
python ai_tailor.py

# Step 4: Build the executive Word document resume (.docx)
python build_resume.py

# Step 5 (Optional): Inspect past applications and search queries in Resume Vault
python history.py list
```

Your generated resume will be waiting in `output/` (e.g. `output/Siddh_Patel_Senior_Data_Engineer.docx`).

---

## CLI Reference

### `research_profile.py` (Domain & Role Researcher)

```bash
python research_profile.py [OPTIONS]
```

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--static` | `-s` | `data/resume_static.json` | Path to static candidate profile |
| `--output` | `-o` | Auto-detected | Destination path for career knowledge JSON |
| `--model` | `-m` | `deepseek-ai/deepseek-v4-flash-0731` | NVIDIA model identifier |
| `--fast` | `-f` | `False` | Fast mode: disables deep reasoning (~5-10s execution) |
| `--reasoning` | | `medium` | Reasoning effort level (`none`, `low`, `medium`, `high`) |
| `--show-reasoning` | `-r` | `False` | Stream DeepSeek's internal research reasoning live |
| `--dry-run` | | `False` | Preview researched knowledge without writing to disk |

---

### `ai_tailor.py` (Resume Optimization Engine)

```bash
python ai_tailor.py [OPTIONS]
```

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--jd` | `-j` | `data/jd.txt` | Path to target job description text file |
| `--static` | `-s` | `data/resume_static.json` | Path to candidate's verified static profile |
| `--knowledge` | `-k` | Auto-detected | Path to career knowledge JSON (`data/career_knowledge[-profile].json`) |
| `--data` | `-d` | `data/resume_data.json` | Path to current resume JSON |
| `--output` | `-o` | `data/resume_data.json` | Destination path for tailored JSON |
| `--fast` | `-f` | `False` | Fast mode: disables deep reasoning (~5-10s execution) |
| `--reasoning` | | `medium` | Reasoning effort level (`none`, `low`, `medium`, `high`) |
| `--show-reasoning` | `-r` | `False` | Stream DeepSeek's internal thinking process live in terminal |
| `--dry-run` | | `False` | Run AI tailoring without overwriting files |
| `--no-db` | | `False` | Skip saving session to local SQLite database |
| `--history` | | `False` | View recent tailoring history table and exit |

---

### `history.py` (Resume Vault & Query Manager)

```bash
python history.py [COMMAND] [OPTIONS]
```

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `list` | `[--limit N] [--offset N]` | List recent tailoring queries and sessions (default) |
| `show` | `<ID> [-j/--full-jd] [-r/--show-reasoning]` | Display full details, JD text, AI reasoning, and tailored data |
| `search` | `<KEYWORD> [--limit N]` | Full-text search across past JDs, titles, and resume content |
| `export` | `<ID> [-o output.json]` | Export/restore a past tailored resume to JSON |
| `stats` | | View total sessions, token counts, and top job titles |
| `delete` | `<ID> [-y/--yes]` | Delete a session record from the local database |

---

### `build_resume.py` (Word Document Generator)

```bash
python build_resume.py [OPTIONS]
```

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--data` | `-d` | `data/resume_data.json` | Path to resume JSON data file |
| `--output` | `-o` | Auto-generated | Custom output file destination |
| `--font` | `-f` | `Times New Roman` | Global font family override |

---

## Data Schema Reference

See `data/resume_data.sample.json`, `data/resume_static.sample.json`, and `data/career_knowledge.json` for full examples.
