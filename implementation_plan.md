# GenAR PADER Safety Reporting System

## Goal
Create a runnable Python prototype that loads the provided CSV dataset, validates the data, performs deterministic analysis, builds evidence packets, allows a human reviewer to approve or flag the analysis, and then invokes the OpenAI LLM to generate a PADER‑style report. The project will be organized under a clear package structure.

## User Review Required
- None identified; the project name, libraries, dataset handling, and LLM API have been specified.

## Open Questions
- None.

## Proposed Changes
### New Files
- **[NEW] `src/main.py`** – Entry point script that orchestrates the workflow.
- **[NEW] `src/data_validation.py`** – Functions to load the CSV and perform schema/consistency checks.
- **[NEW] `src/analysis.py`** – Deterministic data analysis utilities (already present).
- **[NEW] `src/evidence.py`** – Builder that creates section‑specific evidence packets from analysis results.
- **[NEW] `src/llm_interface.py`** – Wrapper around OpenAI API to generate report sections from evidence.
- **[NEW] `src/human_review.py`** – Simple terminal‑based human‑in‑the‑loop approval/flag step.
- **[NEW] `src/report_generator.py`** – Functions to assemble the final markdown PADER report using Jinja2 templates.
- **[NEW] `src/templates/report_template.md`** – Jinja2 template for the PADER report structure.
- **[NEW] `prompts/narrative_summary.txt`** – Prompt template for the Narrative Summary and Analysis section.
- **[NEW] `prompts/case_summary.txt`** – Prompt template for the Summary Analysis of Cases section.
- **[NEW] `prompts/reaction_analysis.txt`** – Prompt template for the Reaction / Adverse Event Analysis section.
- **[NEW] `prompts/alerts.txt`** – Prompt template for the Serious Cases / 15‑Day Alerts section.
- **[NEW] `prompts/trends.txt`** – Prompt template for the Trends and Important Observations section.
- **[NEW] `architecture.png`** – Placeholder architecture diagram (generated separately).
- **[NEW] `README.md`** – Project overview and usage instructions.

### Modified Files
- **[MODIFY] `requirements.txt`** – Ensure required dependencies are listed (pandas, openai, jinja2, python-dotenv, numpy, openpyxl).

## Verification Plan
The human‑review step satisfies the challenge’s requirement for human control, so no separate automated verification of report sections is needed. After running `python src/main.py --data /path/to/dataset.csv`, the workflow will:
1. Produce `output/pader_report.md`.
2. Pause for the reviewer to APPROVE or FLAG the generated content.
3. If APPROVED, complete; if FLAGGED, allow the reviewer to edit or abort.

---
*This plan is presented for your approval before any code is written.*
