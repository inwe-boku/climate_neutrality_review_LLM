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
python excel_llm_framework.py input.xlsx output.xlsx --columns "method,region,sector"
```

Optional flags:
- `--abstract-column "abstract"` (default: `abstract`)
- `--instruction "..."` to customize extraction behavior

By default, the CLI prints each prompt and expects a JSON response from stdin (so you can connect your own LLM API/client with minimal changes).

## Requirements
To run Excel I/O:
```bash
pip install pandas openpyxl
```

## Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```
