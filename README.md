# climate_neutrality_review_LLM

Small Python framework to enrich publication Excel sheets with LLM-based extraction from abstract text.

## What it does
- Reads an Excel file where each row is one publication.
- Uses a configurable `abstract` column (or any user-selected column).
- Lets you define which output columns should be filled by the LLM.
- Builds a prompt row-by-row and asks for JSON output with exactly those fields.
- Writes the enriched rows to a new Excel file.

## Usage
```bash
python excel_llm_framework.py input.xlsx output_json_dir
```

Optional flags:
- `--abstract-column "Abstract"` (default: `Abstract`)
- `--instruction "..."` to customize extraction behavior

By default, the CLI sends each prompt to the installed Copilot CLI and writes one JSON file per row into the output directory.

## Requirements
To run Excel I/O:
```bash
pip install pandas openpyxl
```

To run the LLM step, install the GitHub Copilot CLI and sign in once:
```bash
gh copilot
```

## Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```
