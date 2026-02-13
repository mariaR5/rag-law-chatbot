from pathlib import Path
import fitz
import uuid

DATA_FOLDER = Path("data")
OUTPUT_FOLDER = Path("highlighted_pdfs")
OUTPUT_FOLDER.mkdir(exist_ok = True)

def highlight_pdf(source_pdf: str, page_number: int, snippet: str) -> str:
    input_path = DATA_FOLDER / source_pdf
    output_file_name = f"{uuid.uuid4()}.pdf"
    output_path = OUTPUT_FOLDER / output_file_name

    doc = fitz.open(input_path)
    page = doc[page_number - 1]

    text_instances = page.search_for(snippet[:100])
    if not text_instances:
        raise ValueError("Snippet not found on the page")

    for instances in text_instances:
        highlight = page.add_highlight_annot(instances)
        highlight.update()

    output_doc = fitz.open()
    output_doc.insert_pdf(doc, from_page = page_number - 1, to_page = page_number - 1)
    output_doc.save(output_path)
    output_doc.close()

    doc.close()

    return output_file_name