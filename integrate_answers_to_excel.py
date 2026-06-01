import pandas as pd
import argparse
import os
import json


def get_inputfile(input_path):
    """import the input-file with dois as excel
    Parameters: 
        input_path (str): path to the input-file
    Returns:
        pd.DataFrame: Pandas Dataframe holding the data from input_path.
    """
    # Read the Excel file and ensure DOI is available
    df = pd.read_excel(input_path, dtype=str)
    if 'DOI' not in df.columns:
        raise ValueError("Input file must contain a 'DOI' column")
    # normalize DOI to lowercase 'doi' column for consistent merging
    df['doi'] = df['DOI'].astype(str).str.strip()
    return df

def get_llm_answers(input_folder):
    """
    import all json-files and merge them together in one pandas DataFrame. Uses 
    the doi as index and holds doi as one column named doi. The other columns are 
    named q1_climate_neutrality, q1_comment, q2_region, q2_comment, q3_sector, q3_comment, q4_method, q4_comment.
    
    JSON-INPUTS are of the following format: 
    ```json
        {
    "doi": "10.1002/adsu.202501637",
    "q1_climate_neutrality": "yes",
    "q1_comment": "",
    "q2_comment": "",
    "q2_region": "yes",
    "q3_comment": "",
    "q3_sector": "yes",
    "q4_comment": "",
    "q4_method": "yes"
    }
    ```

    Parameters:
        input_folder (str): path to the folder
    Returns:
        pd.DataFrame: Pandas Dataframe with all merged ansewrs from input_folder..
    """
    # Collect JSON files in the folder
    files = [f for f in os.listdir(input_folder) if f.lower().endswith('.json')]
    records = []
    for fname in files:
        path = os.path.join(input_folder, fname)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            # skip files that cannot be read
            print(f"Warning: failed to read {path}: {e}")
            continue

        # normalize keys to lower-case
        rec = {k.lower(): v for k, v in data.items()}

        # expected keys (lower-case)
        expected = [
            'doi',
            'q1_climate_neutrality', 'q1_comment',
            'q2_region', 'q2_comment',
            'q3_sector', 'q3_comment',
            'q4_method', 'q4_comment'
        ]

        row = {}
        for key in expected:
            val = rec.get(key, '')
            if isinstance(val, str):
                val = val.strip()
            row[key] = val

        # For the binary/flag questions, convert empty string -> NA
        for col in ['q1_climate_neutrality', 'q2_region', 'q3_sector', 'q4_method']:
            if row.get(col, '') == '':
                row[col] = pd.NA

        # ensure doi exists and is a str
        if row.get('doi', '') is None:
            row['doi'] = ''
        row['doi'] = str(row['doi']).strip()

        records.append(row)

    if not records:
        # return empty dataframe with expected columns
        return pd.DataFrame(columns=expected)

    df = pd.DataFrame.from_records(records)
    return df

def merge_input_and_llm_answers(input_df, llm_df):
    """merge the two dataframes
    Parameters:
        input_df (pd.DataFrame): Pandas Dataframe holding the data from input_path.
        llm_df (pd.DataFrame): Pandas Dataframe holding the data from the LLM answers.
    Returns:
        pd.DataFrame: Pandas Dataframe holding the merged data.
    """
    # Ensure both dataframes have a lower-case 'doi' column to join on
    if 'doi' not in input_df.columns:
        if 'DOI' in input_df.columns:
            input_df['doi'] = input_df['DOI'].astype(str).str.strip()
        else:
            raise ValueError("input_df must contain a 'DOI' column")

    if 'doi' not in llm_df.columns:
        raise ValueError("llm_df must contain a 'doi' column")

    # Merge left to keep all input rows
    merged = input_df.merge(llm_df, on='doi', how='left', suffixes=('', '_llm'))

    return merged

def main():
    # command line interface: parameters: inputfile, inputfolder
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("input_folder", help="Path to the input folder")
    parser.description = "Add Paths to the file holding all abstract input information and the folder holding all the LLM answers."
    args = parser.parse_args()

    input_df = get_inputfile(args.input_file)
    llm_df = get_llm_answers(args.input_folder)
    merged_df = merge_input_and_llm_answers(input_df, llm_df)
    # write merged_df to outputfile (overwrite if exists)
    out_path = args.input_file.rsplit('.', 1)[0] + "_LLM-answers.xlsx"
    merged_df.to_excel(out_path, index=False)


if __name__ == '__main__':
    main()