from docx import Document
from docx.shared import Inches
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def replace_logo_smart(doc_path, new_logo_path, output_path, placeholder="[COMPANY_LOGO]"):
    """
    Smart logo replacement that preserves surrounding text in paragraphs.
    Can handle logos embedded in text or as standalone placeholders.
    """
    doc = Document(doc_path)
    
    def replace_in_paragraph(paragraph):
        """Replace placeholder in paragraph while preserving other text"""
        full_text = paragraph.text
        if placeholder not in full_text:
            return False
            
        # Split the text around the placeholder
        parts = full_text.split(placeholder)
        
        # Clear the paragraph but keep the paragraph object
        paragraph.clear()
        
        # Add the first part of text (before logo)
        if parts[0]:
            run = paragraph.add_run(parts[0])
        
        # Add the logo
        run = paragraph.add_run()
        run.add_picture(new_logo_path, width=Inches(2))
        
        # Add remaining parts (in case there are multiple placeholders)
        for i, part in enumerate(parts[1:], 1):
            if i < len(parts) - 1:  # More placeholders to come
                paragraph.add_run(part)
                run = paragraph.add_run()
                run.add_picture(new_logo_path, width=Inches(2))
            else:  # Last part
                if part:
                    paragraph.add_run(part)
        
        return True
    
    def replace_in_runs(paragraph):
        """Alternative method: replace within individual runs"""
        replaced = False
        runs_to_process = list(paragraph.runs)  # Create a copy
        
        for run in runs_to_process:
            if placeholder in run.text:
                # Split the run text
                parts = run.text.split(placeholder)
                
                # Get the run's formatting for preservation
                font = run.font
                
                # Clear this run
                run.text = parts[0]  # First part
                
                # Add logo after this run
                logo_run = paragraph.add_run()
                logo_run.add_picture(new_logo_path, width=Inches(2))
                
                # Add remaining text if any
                if len(parts) > 1 and parts[1]:
                    text_run = paragraph.add_run(parts[1])
                    # Preserve original formatting
                    text_run.font.name = font.name
                    text_run.font.size = font.size
                    text_run.font.bold = font.bold
                    text_run.font.italic = font.italic
                
                replaced = True
                break
        
        return replaced
    
    replacements_made = 0
    
    # Process main document paragraphs
    for paragraph in doc.paragraphs:
        if replace_in_paragraph(paragraph):
            replacements_made += 1
    
    # Process tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if replace_in_paragraph(paragraph):
                        replacements_made += 1
    
    # Process headers and footers
    for section in doc.sections:
        for container in [section.header, section.footer]:
            for paragraph in container.paragraphs:
                if replace_in_paragraph(paragraph):
                    replacements_made += 1
            
            # Also check tables in headers/footers
            for table in container.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if replace_in_paragraph(paragraph):
                                replacements_made += 1
    
    doc.save(output_path)
    return replacements_made

def replace_existing_images(doc_path, new_logo_path, output_path, image_index=0):
    """
    Alternative approach: Replace existing images by index
    Useful when you know which image to replace (e.g., first image is always the logo)
    """
    doc = Document(doc_path)
    
    def find_and_replace_images(container):
        """Find images in container and replace the specified one"""
        images_found = 0
        
        for paragraph in container.paragraphs:
            for run in paragraph.runs:
                # Check if run contains an image
                if run._r.xpath('.//a:blip'):  # Image element
                    if images_found == image_index:
                        # Remove the existing image
                        run.clear()
                        # Add new image
                        run.add_picture(new_logo_path, width=Inches(2))
                        return True
                    images_found += 1
        return False
    
    replaced = False
    
    # Try main document first
    if find_and_replace_images(doc):
        replaced = True
    
    # Try headers/footers
    if not replaced:
        for section in doc.sections:
            for container in [section.header, section.footer]:
                if find_and_replace_images(container):
                    replaced = True
                    break
            if replaced:
                break
    
    doc.save(output_path)
    return replaced

# Integration with your existing system
def update_soc2_template_with_logo(template_path, company_logo_path, company_data, output_path):
    """
    Complete function that integrates logo replacement with your existing SOC2 system
    """
    from find_and_replace import find_and_replace_multiple
    
    # First, do the text replacements
    doc = Document(template_path)
    find_and_replace_multiple(doc, company_data)
    
    # Save temporary file
    temp_path = template_path.replace('.docx', '_temp.docx')
    doc.save(temp_path)
    
    # Then replace the logo
    replacements = replace_logo_smart(temp_path, company_logo_path, output_path)
    
    # Clean up temp file
    os.remove(temp_path)
    
    return replacements

# Example usage
if __name__ == "__main__":
    # Test the logo replacement
    template_path = "soc2t2-report-template-unqualified_completed.docx"
    # new_logo_path = "path/to/company_logo.png"  # You'll need to provide this
    output_path = "soc2t2-report-with-logo.docx"
    
    # Example with placeholder method
    # replacements = replace_logo_smart(template_path, new_logo_path, output_path)
    # print(f"Made {replacements} logo replacements")
    
    # Example with existing image replacement
    # replaced = replace_existing_images(template_path, new_logo_path, output_path, 0)
    # print(f"Logo replacement successful: {replaced}")
    
    print("Logo replacement functions ready to use!")