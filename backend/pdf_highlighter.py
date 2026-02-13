from pathlib import Path
import fitz
import uuid
from typing import List

DATA_FOLDER = Path("data")
OUTPUT_FOLDER = Path("highlighted_pdfs")
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Constants for text matching
MIN_PART_LENGTH = 3  # Minimum length for comma-separated parts
MIN_WINDOW_SIZE = 3  # Minimum phrase length for sliding window search

def highlight_snippet_on_page(page, snippet: str) -> bool:
    """
    Attempt to highlight a text snippet on a PDF page using multiple strategies.
    
    Args:
        page: PyMuPDF page object
        snippet: Text snippet to highlight
        
    Returns:
        True if snippet was found and highlighted, False otherwise
    """
    # 1. Standardize the snippet (normalize whitespace)
    snippet_clean = " ".join(snippet.split())
    
    # 2. Try full literal search first
    matches = page.search_for(snippet_clean)
    if matches:
        for inst in matches:
            page.add_highlight_annot(inst).update()
        return True

    # 3. Try comma-separated parts (for lists or multi-part citations)
    if "," in snippet_clean:
        parts = [p.strip() for p in snippet_clean.split(",") if len(p.strip()) > MIN_PART_LENGTH]
        found_any = False
        for part in parts:
            matches = page.search_for(part)
            if matches:
                for inst in matches:
                    page.add_highlight_annot(inst).update()
                found_any = True
        if found_any:
            return True

    # 4. Sliding window fallback (try progressively smaller phrases)
    words = snippet_clean.split()
    for window_size in range(len(words) - 1, MIN_WINDOW_SIZE, -1):
        for start in range(len(words) - window_size + 1):
            phrase = " ".join(words[start:start + window_size])
            matches = page.search_for(phrase)
            if matches:
                for inst in matches:
                    page.add_highlight_annot(inst).update()
                return True

    return False


def highlight_pages(source_pdf: str, citations: List[dict]) -> str:
    """
    Generate a PDF with highlighted citations from a source PDF.
    
    This function collects all citations per page, applies all highlights
    for each page, and creates an output PDF containing only the pages
    with highlighted citations.
    
    Args:
        source_pdf: Filename of the source PDF in the data folder
        citations: List of dicts with 'page' (int) and 'snippet' (str) keys
        
    Returns:
        Filename of the generated highlighted PDF (UUID-based)
        
    Raises:
        ValueError: If no valid citations are found on any page
    """
    input_path = DATA_FOLDER / source_pdf
    output_file_name = f"{uuid.uuid4()}.pdf"
    output_path = OUTPUT_FOLDER / output_file_name

    doc = fitz.open(input_path)
    output_doc = fitz.open()

    # Collect all snippets per page
    page_snippets = {}
    for citation in citations:
        page_number = citation["page"]
        
        if page_number < 1 or page_number > len(doc):
            continue
            
        if page_number not in page_snippets:
            page_snippets[page_number] = []
        page_snippets[page_number].append(citation["snippet"])

    # Apply all highlights for each page and copy to output
    for page_number in sorted(page_snippets.keys()):
        page = doc[page_number - 1]
        
        # Highlight all snippets on this page
        found_any = False
        for snippet in page_snippets[page_number]:
            if highlight_snippet_on_page(page, snippet):
                found_any = True
        
        # Only add page if at least one snippet was found
        if found_any:
            output_doc.insert_pdf(
                doc,
                from_page=page_number - 1,
                to_page=page_number - 1
            )

    if len(output_doc) == 0:
        doc.close()
        output_doc.close()
        raise ValueError("No valid citations found")

    output_doc.save(output_path)
    output_doc.close()
    doc.close()

    return output_file_name