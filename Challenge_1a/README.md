# Challenge 1A: PDF Outline Extraction 

## Objective

Develop a system to extract a structured outline—including Title, H1, H2, and H3 headings—from unstructured PDF documents. The extracted information should be formatted and saved in JSON for further analysis or downstream tasks.

---

## Project Structure

```
Challenge_1a/
├── sample_dataset/
│   ├── pdfs/                  # Input PDF files
│   └── outputs/               # Output JSON files generated
├── process_pdfs.py           # Main script for PDF outline extraction
├── Dockerfile                # Docker build file
└── README.md
```

---

## 🔧 How to Run

1. **Install Dependencies**

Ensure that the following Python packages are installed:

```bash
pip install PyPDF2 PyMuPDF
```

2. **Execute the Script**

Run the main processing script using:

```bash
python process_pdfs.py
```

By default, this processes all `.pdf` files located in `sample_dataset/pdfs/`  
and generates corresponding `.json` outputs in `sample_dataset/outputs/`.

---

## Output Format

Each output JSON file follows the structure below:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Main Section",
      "page": 2
    },
    {
      "level": "H2",
      "text": "Subsection",
      "page": 3
    }
  ]
}
```

---

## Heading Detection Strategy

Headings are detected and classified using a combination of layout-based and semantic cues:

- Adaptive font size thresholding based on document analysis
- Classification based on:
  - Font size hierarchy
  - Font weight (bold), uppercase patterns
  - Numbering schemes (e.g., 1., 1.1, 1.1.1)
- Post-processing includes:
  - Noise and duplicate removal
  - Filtering non-content artifacts

---

## Docker(Optional)

To build and run the project using Docker:

```bash
docker build -t pdf-outline-extractor .
docker run -v ${PWD}/sample_dataset:/app/sample_dataset pdf-outline-extractor
```

---

## Features

- Extracts multi-level hierarchical outlines from varied PDF layouts
- Heuristics-driven, format-agnostic heading classification
- Outputs clean, structured, machine-readable JSON files ready for submission or analysis
