# Challenge 1b: Multi-Collection PDF Analysis

## Overview
This solution processes **multiple PDF collections** to extract relevant sections based on specific **personas** and **job-to-be-done** contexts.  
The output is a well-structured, merged JSON that captures top-ranked content from each PDF.

---

## Project Structure

```
Challenge_1b/
├── Collection 1/                 # Travel Planning
│   ├── PDFs/                    # South of France guides
│   ├── challenge1b_input.json   # Input: persona + job
│   └── challenge1b_output.json  # Output: extracted sections
├── Collection 2/                 # Adobe Acrobat Learning
│   ├── PDFs/
│   ├── challenge1b_input.json
│   └── challenge1b_output.json
├── Collection 3/                 # Recipe Collection
│   ├── PDFs/
│   ├── challenge1b_input.json
│   └── challenge1b_output.json
├── process_pdfs.py              # Reused from Challenge 1A
├── mergeOutput.py               # This script generates the merged output
└── README.md
```

---

## How to Run

1. Make sure you have Python 3.10+
2. Install required packages:

```bash
pip install PyPDF2 PyMuPDF
```

3. To process the PDFs and generate output JSON:

```bash
python mergeOutput.py
```

Make sure you're in the correct collection folder (e.g., `Collection 1/`) when you run the script.

---

## Input Format (challenge1b_input.json)

```json
{
  "challenge_info": {
    "challenge_id": "round_1b_002",
    "test_case_name": "travel_case"
  },
  "documents": [
    {"filename": "South of France - Cuisine.pdf", "title": "Cuisine Guide"},
    {"filename": "South of France - History.pdf", "title": "History Overview"}
  ],
  "persona": { "role": "Travel Planner" },
  "job_to_be_done": { "task": "Plan a 4-day trip for 10 friends" }
}
```

---

## Output Format (challenge1b_output.json)

```json
{
  "metadata": {
    "input_documents": [
      "South of France - Cuisine.pdf",
      "South of France - History.pdf"
    ],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a 4-day trip for 10 friends"
  },
  "extracted_sections": [
    {
      "document": "South of France - Cuisine.pdf",
      "section_title": "Top Traditional Dishes",
      "importance_rank": 1,
      "page_number": 2
    }
  ],
  "subsection_analysis": [
    {
      "document": "South of France - Cuisine.pdf",
      "refined_text": "Explore classic French cuisines like Ratatouille, Bouillabaisse, etc.",
      "page_number": 2
    }
  ]
}
```

---

## Features

- Persona-focused section selection
- Ranked extraction of relevant content
- Merges content across documents into structured JSON
- Handles multiple challenge collections with ease

---

