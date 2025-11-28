from docx import Document

def clean_docx(input_path, output_path):
    """
    Remove core properties from DOCX (author, title, subject, last_modified_by etc.)
    """
    doc = Document(input_path)
    props = doc.core_properties

    # Clear common core properties
    try:
        props.author = None
        props.title = None
        props.subject = None
        props.keywords = None
        props.last_modified_by = None
        props.comments = None
        props.category = None
        props.last_printed = None
        props.revision = None
        # created and modified: some are read-only in certain environments, but converting to None is ok
    except Exception:
        pass

    doc.save(output_path)
    return output_path
