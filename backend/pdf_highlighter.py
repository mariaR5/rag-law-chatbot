from pathlib import Path
import fitz
from typing import List, Dict

DATA_FOLDER = Path("data")

# Configuration for the fallback search if an exact match isn't found
MIN_PART_LENGTH = 3
MIN_WINDOW_SIZE = 3

# Search for text and apply highlights
def _search_and_highlight(page: fitz.Page, text: str) -> bool:
    matches = page.search_for(text)
    if not matches:
        return False
        
    for inst in matches:
        page.add_highlight_annot(inst).update()
    return True


def highlight_snippet_on_page(page: fitz.Page, snippet: str) -> bool:
    snippet_clean = " ".join(snippet.split())
    if not snippet_clean:
        return False

    # 1. Tries to find the exact match
    if _search_and_highlight(page, snippet_clean):
        return True

    # 2. Sliding window fallback for cases where text may be split accross two lines
    words = snippet_clean.split()
    for window_size in range(len(words) - 1, MIN_WINDOW_SIZE, -1):
        for start in range(len(words) - window_size + 1):
            phrase = " ".join(words[start:start + window_size])
            if _search_and_highlight(page, phrase):
                return True

    return False

def highlight_pages(source_pdf: str, citations: List[dict]) -> bytes:
    input_path = DATA_FOLDER / source_pdf
    
    with fitz.open(input_path) as doc, fitz.open() as output_doc:
        # Group the snippets by page number
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
            
            # Highlight all snippets on the page
            results = [highlight_snippet_on_page(page, snip) for snip in snippets]
            
            # if highlighted succesfully, add the page to result
            if any(results):
                output_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)
                pages_added = True

        if not pages_added:
            raise ValueError("No valid citations found")

        return output_doc.tobytes()