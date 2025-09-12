from docx import Document

doc_path = "soc2t2-report-template-unqualified_completed.docx"
doc = Document(doc_path)

def replace_text_in_paragraph(paragraph, search_text, replace_text):
    for run in paragraph.runs:
        if search_text in run.text:
            run.text = run.text.replace(search_text, replace_text)

def replace_text_in_table(table, search_text, replace_text):
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                replace_text_in_paragraph(paragraph, search_text, replace_text)

def replace_text_in_headers_footers(doc, search_text, replace_text):
    for section in doc.sections:
        for container in [section.header, section.footer]:
            for paragraph in container.paragraphs:
                replace_text_in_paragraph(paragraph, search_text, replace_text)
            for table in container.tables:
                replace_text_in_table(table, search_text, replace_text)

def find_and_replace_all(doc, search_text, replace_text):
    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, search_text, replace_text)
    for table in doc.tables:
        replace_text_in_table(table, search_text, replace_text)
    replace_text_in_headers_footers(doc, search_text, replace_text)

def find_and_replace_multiple(doc, replacements: dict):
    for search_text, replace_text in replacements.items():
        find_and_replace_all(doc, search_text, replace_text)

# Integration with advanced logo replacement
def generate_complete_soc2_report(template_path, company_data, company_logo_path, output_path, logo_sizes=None):
    """
    Complete SOC2 report generation including text replacements and logo
    
    Args:
        template_path: Path to SOC2 template
        company_data: Dict of text replacements
        company_logo_path: Path to company logo image
        output_path: Final output path
        logo_sizes: Optional dict of logo context -> size in inches
    """
    # Load the template
    doc = Document(template_path)
    
    # Do text replacements
    find_and_replace_multiple(doc, company_data)
    
    # Save intermediate file
    intermediate_path = template_path.replace('.docx', '_with_text.docx')
    doc.save(intermediate_path)
    
    # Replace logos if logo path provided
    if company_logo_path and os.path.exists(company_logo_path):
        from advanced_logo_replacer import replace_soc2_logos
        replacements = replace_soc2_logos(intermediate_path, company_logo_path, output_path, logo_sizes)
        print(f"✅ Made {replacements} logo replacements with size control")
        # Clean up intermediate file
        import os
        os.remove(intermediate_path)
    else:
        # Just rename the intermediate file if no logo
        import os
        os.rename(intermediate_path, output_path)
        if company_logo_path:
            print(f"⚠️  Logo file not found: {company_logo_path}")
    
    return output_path

# Example usage
if __name__ == "__main__":
    placeholders = {
        "[Client Name]": "WorldWideShipping",
        "[start_date]": "June 30, 2025",
        "[end_date]": "Levi Willms"
    }
    
    # Example with logo and custom sizes
    # custom_logo_sizes = {
    #     'title_page': 3.0,      # Larger title page logo  
    #     'header_small': 0.5,    # Smaller header logos
    #     'closing_page': 2.5     # Larger closing logo
    # }
    # 
    # generate_complete_soc2_report(
    #     "soc2t2-report-template-unqualified.docx",
    #     placeholders,
    #     "path/to/company_logo.png",
    #     "soc2t2-report-final.docx",
    #     custom_logo_sizes
    # )
    
    # Example with logo using default sizes
    # generate_complete_soc2_report(
    #     "soc2t2-report-template-unqualified.docx", 
    #     placeholders,
    #     "path/to/company_logo.png",
    #     "soc2t2-report-final.docx"
    # )
    
    # Example without logo (existing functionality)
    doc = Document("soc2t2-report-template-unqualified_completed.docx")
    find_and_replace_multiple(doc, placeholders)
    doc.save("soc2t2-report-template-unqualified_completed_filled.docx")
    print("Document updated and saved successfully.")
