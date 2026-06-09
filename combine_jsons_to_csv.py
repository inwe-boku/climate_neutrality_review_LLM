import json
import csv
import glob
import os

# Folder containing your JSON files
INPUT_FOLDER = "abstracts_llm_output"
OUTPUT_CSV = "abstracts_llm_output/abstracts_output.csv"


def load_json_files(folder):
    data = []
    all_keys = set()

    for filepath in glob.glob(os.path.join(folder, "*.json")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
            data.append(content)
            all_keys.update(content.keys())

    return data, sorted(all_keys)


def write_csv(data, keys, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()

        for row in data:
            writer.writerow(row)


if __name__ == "__main__":
    data, keys = load_json_files(INPUT_FOLDER)
    write_csv(data, keys, OUTPUT_CSV)

    print(f"Done! Wrote {len(data)} rows to {OUTPUT_CSV}")
