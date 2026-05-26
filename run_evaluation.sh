INPUT_FILE="$1"
OUTPUT_DIRECTORY="$2"

if [[ -z "$INPUT_FILE" || -z "$OUTPUT_DIRECTORY" ]]; then
	echo "Usage: $0 <input_file> <output_directory>"
	exit 1
fi

echo "Starting Copilot Login via GitHub. This needs your input! After login, press esc and type "exit" in interactive copilot terminal to continue."
sleep 5
copilot login

echo "Starting evaluation. This may take some time. If evaluation fails, program tries again once."
if pixi run python excel_llm_framework.py "$INPUT_FILE" "$OUTPUT_DIRECTORY"; then
	copilot -i /logout
	exit 0
fi

echo "First evaluation attempt failed; retrying once..."

if pixi run python excel_llm_framework.py "$INPUT_FILE" "$OUTPUT_DIRECTORY"; then
	copilot -i /logout
	exit 0
fi

echo "Evaluation failed again on retry."
echo "Logging out of Copilot. This needs your input! Type 'exit' in interactive copilot terminal."
sleep 5
copilot logout

exit 1
