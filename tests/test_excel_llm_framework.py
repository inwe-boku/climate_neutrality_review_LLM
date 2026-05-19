import unittest

from excel_llm_framework import ExcelLLMFramework, FrameworkConfig


class FrameworkTests(unittest.TestCase):
    def test_build_prompt_includes_target_fields_line_by_line(self):
        framework = ExcelLLMFramework(
            llm_client=lambda prompt, row: {},
            config=FrameworkConfig(target_columns=["method", "region"]),
        )

        prompt = framework.build_prompt("short abstract")

        self.assertIn("Fields to extract:\n- method\n- region", prompt)
        self.assertIn("Abstract:\nshort abstract", prompt)

    def test_process_rows_fills_user_defined_columns(self):
        calls = []

        def fake_llm(prompt, row):
            calls.append((prompt, row["id"]))
            return {"method": "review", "region": "EU"}

        framework = ExcelLLMFramework(
            llm_client=fake_llm,
            config=FrameworkConfig(target_columns=["method", "region"]),
        )

        rows = [
            {"id": 1, "abstract": "A"},
            {"id": 2, "abstract": "B", "method": ""},
        ]
        result = framework.process_rows(rows)

        self.assertEqual(2, len(calls))
        self.assertEqual("review", result[0]["method"])
        self.assertEqual("EU", result[1]["region"])


if __name__ == "__main__":
    unittest.main()
