from pypdf import PdfReader, PdfWriter

def clean_pdf(input_path, output_path):
    """
    Remove PDF metadata by copying pages into a new PdfWriter and setting empty metadata.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Clear metadata
    writer.add_metadata({})

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
