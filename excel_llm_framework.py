# pyright: reportMissingImports=false
from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


LLMClient = Callable[[str, dict[str, Any]], dict[str, Any]]


def load_default_instruction() -> str:
    prompt_path = Path(__file__).with_name("prompt.md")
    try:
        return prompt_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to read prompt file: {prompt_path}") from exc


@dataclass
class FrameworkConfig:
    abstract_column: str = "Abstract"
    doi_column: str = "DOI"
    instruction: str = load_default_instruction()


class ExcelLLMFramework:
    def __init__(self, llm_client: LLMClient, config: FrameworkConfig | None = None) -> None:
        self.llm_client = llm_client
        self.config = config or FrameworkConfig()

    def build_prompt(self, abstract_text: str) -> str:
        lines = [self.config.instruction.strip()]
        lines.extend(["", "Abstract:", abstract_text.strip()])
        return "\n".join(lines)

    def process_rows(self, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        processed_rows: list[dict[str, Any]] = []
        for row in rows:
            abstract_text = str(row.get(self.config.abstract_column, "") or "")
            prompt = self.build_prompt(abstract_text)
            extracted = self.llm_client(prompt, row) or {}
            processed_rows.append(extracted)
        return processed_rows

    def run_excel(
        self, input_excel_path: str, output_directory: str, sheet_name: str | int = 0
    ) -> list[Path]:
        try:
            pd = importlib.import_module("pandas")
        except ImportError as exc:
            raise RuntimeError(
                "pandas is required to read Excel files. Install with: pip install pandas openpyxl"
            ) from exc

        dataframe = pd.read_excel(input_excel_path, sheet_name=sheet_name)
        if self.config.abstract_column not in dataframe.columns:
            raise ValueError(f"Missing required abstract column: '{self.config.abstract_column}'")
        if self.config.doi_column not in dataframe.columns:
            raise ValueError(f"Missing required DOI column: '{self.config.doi_column}'")

        rows = dataframe.to_dict(orient="records")
        doi_values: list[str] = []
        for row_index, row in enumerate(rows, start=1):
            doi_value = row.get(self.config.doi_column)
            doi_text = str(doi_value).strip() if doi_value is not None else ""
            if not doi_text:
                raise ValueError(f"Missing DOI value for row {row_index}")
            doi_values.append(doi_text)

        processed_rows = self.process_rows(rows)
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        written_files: list[Path] = []
        for row_index, (doi_text, extracted_row) in enumerate(
            zip(doi_values, processed_rows), start=1
        ):
            extracted_row["doi"] = doi_text
            safe_doi = re.sub(r"[^A-Za-z0-9._-]+", "_", doi_text)
            if safe_doi in {"", ".", ".."}:
                raise ValueError(f"Invalid DOI value for filename in row {row_index}")

            file_path = output_path / f"{safe_doi}.json"
            file_path.write_text(
                json.dumps(extracted_row, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            written_files.append(file_path)

        return written_files


def _extract_json_payload(response_text: str) -> str:
    stripped_text = response_text.strip()
    fenced_match = re.search(
        r"^```(?:json)?\s*(.*?)\s*```$", stripped_text, flags=re.DOTALL | re.IGNORECASE
    )
    if fenced_match:
        stripped_text = fenced_match.group(1).strip()

    try:
        json.loads(stripped_text)
        return stripped_text
    except json.JSONDecodeError:
        pass

    json_start = stripped_text.find("{")
    json_end = stripped_text.rfind("}")
    if json_start != -1 and json_end != -1 and json_end > json_start:
        candidate = stripped_text[json_start : json_end + 1]
        json.loads(candidate)
        return candidate

    raise ValueError("Copilot response did not contain valid JSON")


def copilot_llm_client(prompt: str, _: dict[str, Any]) -> dict[str, Any]:
    command = ["copilot", "-p", prompt]
    completed_process = subprocess.run(
        command, capture_output=True, text=True, check=False
    )

    if completed_process.returncode != 0:
        stderr = completed_process.stderr.strip()
        stdout = completed_process.stdout.strip()
        details = stderr or stdout or f"exit code {completed_process.returncode}"
        raise RuntimeError(f"Copilot CLI failed: {details}")

    response_text = completed_process.stdout.strip()
    if not response_text:
        raise RuntimeError("Copilot CLI returned no output")

    return json.loads(_extract_json_payload(response_text))


def fallback_json_llm_client(prompt: str, _: dict[str, Any]) -> dict[str, Any]:
    print("\n=== Prompt sent to LLM ===\n")
    print(prompt)
    print("\nPaste JSON response and press Enter:")
    raw = input().strip()
    return json.loads(raw) if raw else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract abstract information into user-selected Excel columns")
    parser.add_argument("input_excel", help="Path to source Excel file")
    parser.add_argument(
        "output_directory", help="Directory where one JSON file per row will be written"
    )
    parser.add_argument(
        "--abstract-column",
        default=FrameworkConfig().abstract_column,
        help="Column containing abstract text",
    )
    parser.add_argument("--instruction", default=FrameworkConfig().instruction, help="Base extraction instruction")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    framework = ExcelLLMFramework(
        llm_client=copilot_llm_client,
        config=FrameworkConfig(
            abstract_column=args.abstract_column, instruction=args.instruction
        ),
    )
    framework.run_excel(args.input_excel, args.output_directory)


if __name__ == "__main__":
    main()
