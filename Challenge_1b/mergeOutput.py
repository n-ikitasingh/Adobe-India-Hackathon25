import os
import json
from process_pdfs import process_single_pdf  # 👈 reuse your logic here

# Path Config
input_path = "e:/adobe hackathon/Challenge_1b/Collection 3/challenge1b_input.json"
pdf_folder = "e:/adobe hackathon/Challenge_1b/Collection 3/PDFs"
output_path = "e:/adobe hackathon/Challenge_1b/Collection 3/challenge1b_output.json"

# Load persona and job
with open(input_path, "r", encoding="utf-8") as f:
    input_data = json.load(f)

final_output = {
    "persona": input_data.get("persona", ""),
    "job": input_data.get("job", ""),
    "documents": []
}

# Loop through each PDF and use your imported function
for pdf_file in os.listdir(pdf_folder):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"Processing: {pdf_path}")
        single_result = process_single_pdf(pdf_path)
        final_output["documents"].append(single_result)

# Save final combined output
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"\nDone! Output written to {output_path}")
