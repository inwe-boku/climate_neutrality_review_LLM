from __future__ import annotations

import argparse
import json
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

    def run_excel(self, input_excel_path: str, output_excel_path: str, sheet_name: str | int = 0) -> None:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError(
                "pandas is required to read/write Excel files. Install with: pip install pandas openpyxl"
            ) from exc

        dataframe = pd.read_excel(input_excel_path, sheet_name=sheet_name)
        if self.config.abstract_column not in dataframe.columns:
            raise ValueError(f"Missing required abstract column: '{self.config.abstract_column}'")

        rows = dataframe.to_dict(orient="records")
        processed_rows = self.process_rows(rows)
        print(processed_rows)
        pd.DataFrame(processed_rows).to_excel(output_excel_path, index=False)


def json_llm_client(prompt: str, _: dict[str, Any]) -> dict[str, Any]:
    print("\n=== Prompt sent to LLM ===\n")
    print(prompt)
    print("\nPaste JSON response and press Enter:")
    raw = input().strip()
    return json.loads(raw) if raw else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract abstract information into user-selected Excel columns")
    parser.add_argument("input_excel", help="Path to source Excel file")
    parser.add_argument("output_excel", help="Path for enriched Excel file")
    parser.add_argument("--abstract-column", default="abstract", help="Column containing abstract text")
    parser.add_argument("--instruction", default=FrameworkConfig().instruction, help="Base extraction instruction")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    framework = ExcelLLMFramework(llm_client=json_llm_client)
    framework.run_excel(args.input_excel, args.output_excel)


if __name__ == "__main__":
    main()
