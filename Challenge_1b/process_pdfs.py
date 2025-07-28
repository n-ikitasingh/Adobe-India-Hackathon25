import os
import json
import re
import logging
from pathlib import Path   
from typing import Dict, List, Tuple, Optional
import PyPDF2
import fitz  # PyMuPDF
from dataclasses import dataclass
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HeadingInfo:
    """Data class to store heading information"""
    level: str
    text: str
    page: int
    font_size: float = 0.0
    font_name: str = ""
    is_bold: bool = False
    
class EnhancedPDFOutlineExtractor:
    def __init__(self):
        self.toc_detected = False

    def is_noise(self, text: str) -> bool:
        text = text.strip()
        if re.match(r'^[.\-•▪▫‣⁃]{5,}$', text):
            return True
        if re.match(r'^\d{1,2}\.?$', text):
            return True
        if len(text) <= 3 and not text.isalpha():
            return True
        return False

    def post_process_headings(self, headings: List[HeadingInfo]) -> List[HeadingInfo]:
        cleaned = []
        seen = set()
        for h in headings:
            if self.is_noise(h.text):
                continue
            key = (h.text.strip(), h.page)
            if key not in seen:
                seen.add(key)
                cleaned.append(h)
        return sorted(cleaned, key=lambda x: (x.page, -x.font_size))

    def merge_title_candidates(self, title_candidates: List[Tuple[str, float, float]]) -> str:
        # Sort by font size desc, y-pos asc
        title_candidates.sort(key=lambda x: (-x[1], x[2]))
        merged = title_candidates[0][0]
        for i in range(1, len(title_candidates)):
            if abs(title_candidates[i][2] - title_candidates[i-1][2]) < 50:
                merged += ' ' + title_candidates[i][0]
            else:
                break
        return merged.strip()

    def should_skip_page(self, page_text: str) -> bool:
        return 'table of contents' in page_text.lower()


class PDFOutlineExtractor:
    """
    Main class for extracting structured outlines from PDF files
    """
    
    def __init__(self):
        self.font_size_threshold = {
            'title': 16.0,
            'h1': 14.0,
            'h2': 12.0,
            'h3': 10.0
        }
        self.common_heading_patterns = [
            r'^chapter\s+\d+',
            r'^\d+\.\s',
            r'^\d+\.\d+\s',
            r'^\d+\.\d+\.\d+\s',
            r'^[A-Z][A-Z\s]{2,}$',  # ALL CAPS
            r'^[A-Z][a-z]+\s[A-Z][a-z]+',  # Title Case
        ]
        
    def extract_title_from_metadata(self, pdf_path: str) -> Optional[str]:
        """Extract title from PDF metadata"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if pdf_reader.metadata and pdf_reader.metadata.title:
                    return pdf_reader.metadata.title.strip()
        except Exception as e:
            logger.warning(f"Could not extract metadata title: {e}")
        return None
    
    def extract_title_from_first_page(self, doc) -> Optional[str]:
        """Extract title from the first page using heuristics"""
    try:
        first_page = doc[0]
        blocks = first_page.get_text("dict")["blocks"]
            
        candidates = []
            
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                            text = span["text"].strip()
                            font_size = span["size"]
                            
                            # Skip very short text or common non-title elements
                            if len(text) < 3 or text.lower() in ['page', 'abstract', 'introduction']:
                                continue
                            
                            # Look for largest font sizes in upper portion of page
                            if line["bbox"][1] < first_page.rect.height * 0.3:  # Upper 30% of page
                                candidates.append((text, font_size, line["bbox"][1]))
            
            if candidates:
                # Sort by font size (descending) and then by vertical position (ascending)
                candidates.sort(key=lambda x: (-x[1], x[2]))
                merged = EnhancedPDFOutlineExtractor().merge_title_candidates(candidates)
        #return merged
          
    except Exception as e:
        logger.warning(f"Could not extract title from first page: {e}")
        #return None
    
    def is_heading_by_pattern(self, text: str) -> bool:
        """Check if text matches common heading patterns"""
        text_stripped = text.strip()
        
        for pattern in self.common_heading_patterns:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return True
        
        return False
    
    def classify_heading_level(self, font_size: float, is_bold: bool, text: str, page_num: int) -> Optional[str]:
        """Classify heading level based on font size, formatting, and patterns"""
        
        # Pattern-based classification first
        if re.match(r'^chapter\s+\d+', text.strip(), re.IGNORECASE):
            return 'H1'
        elif re.match(r'^\d+\.\s', text.strip()):
            return 'H1'
        elif re.match(r'^\d+\.\d+\s', text.strip()):
            return 'H2'
        elif re.match(r'^\d+\.\d+\.\d+\s', text.strip()):
            return 'H3'
        
        # Font size-based classification
        if font_size >= self.font_size_threshold['h1']:
            return 'H1'
        elif font_size >= self.font_size_threshold['h2']:
            return 'H2'
        elif font_size >= self.font_size_threshold['h3']:
            return 'H3'
        
        # Additional heuristics
        if is_bold and len(text.strip()) < 100:  # Bold and reasonably short
            if font_size >= 11.0:
                return 'H2'
            elif font_size >= 9.0:
                return 'H3'
        
        return None
    
    def clean_heading_text(self, text: str) -> str:
        """Clean and normalize heading text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove page numbers at the end
        text = re.sub(r'\s+\d+$', '', text)
        
        # Remove common artifacts
        text = re.sub(r'[•▪▫‣⁃]', '', text)  # Remove bullet points
        text = re.sub(r'^\s*[-–—]\s*', '', text)  # Remove leading dashes
        
        return text.strip()
    
    def extract_headings_from_pdf(self, pdf_path: str) -> Tuple[Optional[str], List[HeadingInfo]]:
        """Extract title and headings from PDF"""
        
        logger.info(f"Processing: {pdf_path}")
        
        # Try to get title from metadata first
        title = self.extract_title_from_metadata(pdf_path)
        
        headings = []
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract title from first page if not found in metadata
            if not title:
                title = self.extract_title_from_first_page(doc)
            
            # Analyze font sizes across the document to set dynamic thresholds
            all_font_sizes = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["text"].strip():
                                    all_font_sizes.append(span["size"])
            
            if all_font_sizes:
                # Update thresholds based on document's font size distribution
                sorted_sizes = sorted(set(all_font_sizes), reverse=True)
                if len(sorted_sizes) >= 4:
                    self.font_size_threshold['h1'] = sorted_sizes[1]  # Second largest
                    self.font_size_threshold['h2'] = sorted_sizes[2]  # Third largest
                    self.font_size_threshold['h3'] = sorted_sizes[3]  # Fourth largest
            
            # Extract headings
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            avg_font_size = 0
                            is_bold = False
                            font_name = ""
                            span_count = 0
                            
                            for span in line["spans"]:
                                text = span["text"]
                                if text.strip():
                                    line_text += text
                                    avg_font_size += span["size"]
                                    span_count += 1
                                    
                                    # Check if bold
                                    if "bold" in span["font"].lower() or span.get("flags", 0) & (1 << 4):
                                        is_bold = True
                                    
                                    font_name = span["font"]
                            
                            if span_count > 0:
                                avg_font_size /= span_count
                            
                            line_text = self.clean_heading_text(line_text)
                            
                            # Skip very short or very long text
                            if len(line_text) < 2 or len(line_text) > 200:
                                continue
                            
                            # Check if this could be a heading
                            is_potential_heading = (
                                self.is_heading_by_pattern(line_text) or
                                avg_font_size > 10.0 or
                                is_bold or
                                line_text.isupper()
                            )
                            
                            if is_potential_heading:
                                heading_level = self.classify_heading_level(
                                    avg_font_size, is_bold, line_text, page_num + 1
                                )
                                
                                if heading_level:
                                    heading_info = HeadingInfo(
                                        level=heading_level,
                                        text=line_text,
                                        page=page_num + 1,
                                        font_size=avg_font_size,
                                        font_name=font_name,
                                        is_bold=is_bold
                                    )
                                    headings.append(heading_info)
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None, []
        
        # Post-process headings to remove duplicates and improve quality
        headings = self.post_process_headings(headings)
        
        return title, headings
    
    def post_process_headings(self, headings: List[HeadingInfo]) -> List[HeadingInfo]:
        """Post-process headings to remove duplicates and improve quality"""
        
        if not headings:
            return headings
        
        # Remove duplicates (same text on same page)
        seen = set()
        unique_headings = []
        
        for heading in headings:
            key = (heading.text, heading.page)
            if key not in seen:
                seen.add(key)
                unique_headings.append(heading)
        
        # Sort by page number and then by estimated position
        unique_headings.sort(key=lambda h: (h.page, -h.font_size))
        
        return unique_headings
    
    def format_output(self, title: Optional[str], headings: List[HeadingInfo]) -> Dict:
        """Format the output according to the required JSON structure"""
        
        # Use a default title if none found
        if not title:
            title = "Document"
        
        outline = []
        for heading in headings:
            outline.append({
                "level": heading.level,
                "text": heading.text,
                "page": heading.page
            })
        
        return {
            "title": title,
            "outline": outline
        }
    
    def process_pdf(self, input_path: str, output_path: str) -> bool:
        """Process a single PDF file"""
        try:
            title, headings = self.extract_headings_from_pdf(input_path)
            output_data = self.format_output(title, headings)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully processed {input_path} -> {output_path}")
            logger.info(f"Extracted title: {output_data['title']}")
            logger.info(f"Found {len(output_data['outline'])} headings")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process {input_path}: {e}")
            return False

def main():
    """Main function to process all PDFs in the input directory"""
    
    parser = argparse.ArgumentParser(description='PDF Outline Extractor for Adobe Hackathon Challenge 1A')
    parser.add_argument('--input-dir', default='/app/input', help='Input directory containing PDF files')
    parser.add_argument('--output-dir', default='/app/output', help='Output directory for JSON files')
    
    args = parser.parse_args()
    
    input_dir = Path("e:/adobe hackathon/Challenge_1a/sample_dataset/pdfs")
    output_dir = Path("e:/adobe hackathon/Challenge_1a/sample_dataset/outputs")
    
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        return
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    extractor = PDFOutlineExtractor()
    success_count = 0
    
    for pdf_file in pdf_files:
        output_file = output_dir / f"{pdf_file.stem}.json"
        
        if extractor.process_pdf(str(pdf_file), str(output_file)):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count}/{len(pdf_files)} files")

def process_single_pdf(pdf_path: str) -> Dict:

    extractor = PDFOutlineExtractor()
    title, headings = extractor.extract_headings_from_pdf(pdf_path)

    return {
        "filename": os.path.basename(pdf_path),
        "sections": [
            {
                "heading": h.text,
                "page": h.page,
                "score": 0.90  
            }
            for h in headings[:5]  
        ]
    }



if __name__ == "__main__":
    main()