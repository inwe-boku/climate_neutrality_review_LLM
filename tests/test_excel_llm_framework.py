import unittest
import tempfile
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from excel_llm_framework import ExcelLLMFramework, FrameworkConfig, copilot_llm_client


class FrameworkTests(unittest.TestCase):

    def test_build_prompt_includes_instruction_and_abstract(self):
        framework = ExcelLLMFramework(
            llm_client=lambda prompt, row: {},
        )

        prompt = framework.build_prompt("short abstract")

        self.assertIn("You are a scientific abstract screening assistant", prompt)
        self.assertIn("Abstract:\nshort abstract", prompt)

    def test_copilot_client_parses_fenced_json(self):
        completed_process = SimpleNamespace(
            returncode=0,
            stdout='```json\n{"method": "review", "region": "EU"}\n```',
            stderr="",
        )

        with patch(
            "excel_llm_framework.subprocess.run", return_value=completed_process
        ):
            result = copilot_llm_client("prompt text", {})

        self.assertEqual({"method": "review", "region": "EU"}, result)

    def test_process_rows_returns_llm_output(self):
        calls = []

        def fake_llm(prompt, row):
            calls.append((prompt, row["id"]))
            return {"method": "review", "region": "EU"}

        framework = ExcelLLMFramework(
            llm_client=fake_llm,
        )

        rows = [
            {"id": 1, "abstract": "A"},
            {"id": 2, "abstract": "B", "method": ""},
        ]
        result = framework.process_rows(rows)

        self.assertEqual(2, len(calls))
        self.assertEqual("review", result[0]["method"])
        self.assertEqual("EU", result[1]["region"])

    def test_run_excel_writes_one_json_file_per_row(self):
        fake_module = ModuleType("pandas")
        fake_module.read_excel = lambda *args, **kwargs: SimpleNamespace(
            columns=["Abstract", "DOI"],
            to_dict=lambda orient="records": [
                {"id": 1, "Abstract": "A", "DOI": "10.1000/ABC"},
                {"id": 2, "Abstract": "B", "DOI": "10.2000/DEF"},
            ],
        )

        class FakeDataFrame:
            def __init__(self, rows):
                self.rows = rows

        fake_module.DataFrame = FakeDataFrame

        framework = ExcelLLMFramework(
            llm_client=lambda prompt, row: {
                "id": row["id"],
                "abstract": row["Abstract"],
                "source": "copilot",
            },
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_excel = Path(temp_dir) / "input.xlsx"
            input_excel.write_text("placeholder", encoding="utf-8")
            output_directory = Path(temp_dir) / "output"

            with patch.dict("sys.modules", {"pandas": fake_module}):
                written_files = framework.run_excel(
                    str(input_excel), str(output_directory)
                )

            self.assertEqual(2, len(written_files))
            self.assertTrue((output_directory / "10.1000_ABC.json").exists())
            self.assertTrue((output_directory / "10.2000_DEF.json").exists())
            self.assertEqual(
                '{\n  "abstract": "A",\n  "doi": "10.1000/ABC",\n  "id": 1,\n  "source": "copilot"\n}',
                (output_directory / "10.1000_ABC.json").read_text(encoding="utf-8"),
            )

    def test_run_excel_raises_on_missing_doi(self):
        fake_module = ModuleType("pandas")
        fake_module.read_excel = lambda *args, **kwargs: SimpleNamespace(
            columns=["Abstract", "DOI"],
            to_dict=lambda orient="records": [
                {"id": 1, "Abstract": "A", "DOI": ""},
            ],
        )

        class FakeDataFrame:
            def __init__(self, rows):
                self.rows = rows

        fake_module.DataFrame = FakeDataFrame

        framework = ExcelLLMFramework(
            llm_client=lambda prompt, row: {
                "id": row["id"],
                "abstract": row["Abstract"],
                "source": "copilot",
            },
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            input_excel = Path(temp_dir) / "input.xlsx"
            input_excel.write_text("placeholder", encoding="utf-8")
            output_directory = Path(temp_dir) / "output"

            with patch.dict("sys.modules", {"pandas": fake_module}):
                with self.assertRaises(ValueError):
                    framework.run_excel(str(input_excel), str(output_directory))


if __name__ == "__main__":
    unittest.main()
