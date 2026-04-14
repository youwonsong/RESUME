from docx import Document

# adds a section given the section header name and the description under header
def add_section(doc, heading, paragraph):
    doc.add_heading(heading, level=1)
    doc.add_paragraph(paragraph)