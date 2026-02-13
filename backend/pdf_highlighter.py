from pathlib import Path
import fitz
from typing import List, Dict

DATA_FOLDER = Path("data")

# Constants
MIN_PART_LENGTH = 3
MIN_WINDOW_SIZE = 3

def _search_and_highlight(page: fitz.Page, text: str) -> bool:
    """Helper to search for text and apply highlights."""
    matches = page.search_for(text)
    if not matches:
        return False
        
    for inst in matches:
        page.add_highlight_annot(inst).update()
    return True

def highlight_snippet_on_page(page: fitz.Page, snippet: str) -> bool:
    """
    Attempt to highlight a text snippet using multiple strategies:
    1. Exact match (normalized whitespace)
    2. Comma-separated parts
    3. Sliding window of words
    """
    snippet_clean = " ".join(snippet.split())
    if not snippet_clean:
        return False

    # 1. Exact match
    if _search_and_highlight(page, snippet_clean):
        return True

    # 2. Comma-separated parts
    found_any = False
    if "," in snippet_clean:
        parts = [p.strip() for p in snippet_clean.split(",") if len(p.strip()) > MIN_PART_LENGTH]
        for part in parts:
            if _search_and_highlight(page, part):
                found_any = True
        if found_any:
            return True

    # 3. Sliding window fallback
    words = snippet_clean.split()
    for window_size in range(len(words) - 1, MIN_WINDOW_SIZE, -1):
        for start in range(len(words) - window_size + 1):
            phrase = " ".join(words[start:start + window_size])
            if _search_and_highlight(page, phrase):
                return True

    return False

def highlight_pages(source_pdf: str, citations: List[dict]) -> bytes:
    """
    Generate a PDF with highlighted citations.
    """
    input_path = DATA_FOLDER / source_pdf
    
    # Use context managers for proper resource cleanup
    with fitz.open(input_path) as doc, fitz.open() as output_doc:
        # Group snippets by page
        page_snippets: Dict[int, List[str]] = {}
        for citation in citations:
            page_num = citation.get("page", 0)
            if 1 <= page_num <= len(doc):
                page_snippets.setdefault(page_num, []).append(citation.get("snippet", ""))

        if not page_snippets:
            raise ValueError("No valid citations found")

        # Process pages
        pages_added = False
        for page_num in sorted(page_snippets):
            page = doc[page_num - 1]
            snippets = page_snippets[page_num]
            
            # Highlight all snippets on the page (force evaluation -> no short-circuit)
            results = [highlight_snippet_on_page(page, snip) for snip in snippets]
            
            if any(results):
                output_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)
                pages_added = True

        if not pages_added:
            raise ValueError("No valid citations found")

        return output_doc.tobytes()