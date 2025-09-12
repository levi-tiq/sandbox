from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
import shutil

# File setup
input_path = "soc2t2-report-template-unqualified.docx"
output_path = "soc2t2-report-unqualified_completed.docx"
shutil.copy(input_path, output_path)
doc = Document(output_path)

# Availability control group
availability_control_group = {
    "heading": "A1.0 Additional Criteria for Availability",
    "control_number": "A1.0",
    "sub_controls": [
        {
            "description": "Measures Current Usage—The use of the system components is measured to establish a baseline for capacity management...",
            "test": "\nInquired to determine the mechanism in use to ensure baseline for capacity management and monitoring.\n\nInspected network and server monitoring software management console.\n\nInspected capacity forecasting and planning activities to confirm the establishment of a baseline...",
            "result": "No Exception Noted."
        },
        {
            "description": "Forecasts Capacity—The expected average and peak use of system components is forecasted...",
            "test": "Inquired to determine the mechanism in use to ensure system components usage is forecasted, compared to capacity tolerances.\nInspected capacity forecasting and planning activities to ensure that the expected usage is forecasted and compared to capacity.",
            "result": "No Exception Noted."
        },
        {
            "description": "Makes Changes Based on Forecasts—The system change management process is initiated when forecasted usage exceeds capacity tolerances.",
            "test": "Inquired to determine the mechanism in use to ensure system change management process is initiated.\nInspected network and server monitoring software management console.",
            "result": "No Exception Noted."
        }
    ],
    "style": {
        "header_bold": True,
        "font_size": 10,
        "font_name": "Calibri",
        "header_bg_color": "FF419C",
        "header_font_color": "262626"
    }
}

# Helper functions
def set_cell_background(cell, color_hex):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def set_repeat_table_header(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    trPr.append(tblHeader)

# Main insertion logic
def insert_grouped_control_table_with_bullets(doc, heading, control_data):
    heading_para = doc.add_paragraph(heading)
    heading_para.style = 'Heading 1'

    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'

    headers = ["Control Number", "Description of Control Activities", "Test Applied by the Service Auditor", "Test Results"]
    hdr_cells = table.rows[0].cells
    #hdr_cells.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    for i, header in enumerate(headers):
        para = hdr_cells[i].paragraphs[0]
        run = para.add_run(header)
        run.font.bold = control_data["style"]["header_bold"]
        run.font.size = Pt(control_data["style"]["font_size"])
        run.font.name = control_data["style"]["font_name"]
        run.font.color.rgb = RGBColor.from_string(control_data["style"]["header_font_color"])
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_background(hdr_cells[i], control_data["style"]["header_bg_color"])
    set_repeat_table_header(table.rows[0])

    # Add rows for each sub-control
    for sub in control_data["sub_controls"]:
        row_cells = table.add_row().cells

        # Description
        desc_cell = row_cells[1]
        desc_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        desc_para = desc_cell.paragraphs[0]
        desc_run = desc_para.add_run(sub["description"])
        desc_run.font.size = Pt(control_data["style"]["font_size"])
        desc_run.font.name = control_data["style"]["font_name"]
        desc_para.alignment = WD_ALIGN_PARAGRAPH.CENTER


        # Test Applied (bullet points)
        test_cell = row_cells[2]
        test_cell.text = ""
        test_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for line in sub["test"].split("\n"):
            if line.strip():
                para = test_cell.add_paragraph(f"- {line.strip()}")
                run = para.runs[0]
                run.font.size = Pt(control_data["style"]["font_size"])
                run.font.name = control_data["style"]["font_name"]
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para.alignment = WD_ALIGN_VERTICAL.CENTER

        # Test Result
        result_cell = row_cells[3]
        result_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        result_para = result_cell.paragraphs[0]
        result_run = result_para.add_run(sub["result"])
        result_run.font.size = Pt(control_data["style"]["font_size"])
        result_run.font.name = control_data["style"]["font_name"]
        result_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Merge "Control Number" cells
    control_number_cell = table.cell(1, 0)
    control_number_cell.text = control_data["control_number"]
    control_number_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for para in control_number_cell.paragraphs:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for merge_row in range(2, len(table.rows)):
        control_number_cell.merge(table.cell(merge_row, 0))

# Run insertion
insert_grouped_control_table_with_bullets(doc, availability_control_group["heading"], availability_control_group)





# Save output
doc.save(output_path)
print(f"✔ Document saved to: {output_path}")


# # Update table of contents.
# def update_toc_with_libreoffice(docx_path, output_dir):
#     subprocess.run([
#         "libreoffice",
#         "--headless",
#         "--convert-to", "docx",
#         docx_path,
#         "--outdir", output_dir
#     ], check=True)

# # Example:
# update_toc_with_libreoffice("soc2t2-report-template-unqualified_completed.docx", ".")
