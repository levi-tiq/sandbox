from docx import Document
import re

def analyze_document_sections(docx_path):
    """
    Analyze the document to find sections and their table structures
    """
    doc = Document(docx_path)
    
    print(f"Analyzing document: {docx_path}")
    print("="*60)
    
    current_section = None
    section_number = 0
    
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        
        # Look for section headers (various patterns)
        section_patterns = [
            r'^(\d+)\.\s*(.+)',  # "4. Section Title"
            r'^Section\s+(\d+)',  # "Section 4"
            r'^(\d+)\s+(.+)',     # "4 Section Title"
        ]
        
        for pattern in section_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                section_number = int(match.group(1))
                section_title = match.group(2) if len(match.groups()) > 1 else ""
                current_section = section_number
                print(f"\n📍 Found Section {section_number}: {section_title}")
                print(f"   Paragraph {i+1}: '{text}'")
                break
        
        # If we're in section 4, look for tables nearby
        if current_section == 4:
            # Check if this paragraph is followed by tables
            if i < len(doc.paragraphs) - 1:
                # Look ahead for tables in the document
                pass
    
    # Now analyze tables and their proximity to sections
    print(f"\n📊 Tables found in document:")
    for table_idx, table in enumerate(doc.tables):
        print(f"\nTable {table_idx + 1}:")
        print(f"  Rows: {len(table.rows)}, Columns: {len(table.columns)}")
        
        # Show first few rows to understand structure
        for row_idx, row in enumerate(table.rows[:3]):  # First 3 rows
            row_text = " | ".join([cell.text.strip()[:50] for cell in row.cells])
            print(f"  Row {row_idx + 1}: {row_text}")
        
        if len(table.rows) > 3:
            print(f"  ... ({len(table.rows) - 3} more rows)")

def find_section_4_tables(docx_path):
    """
    Specifically look for tables in or near section 4
    """
    doc = Document(docx_path)
    section_4_found = False
    section_4_paragraph_index = None
    
    # Find section 4
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if re.match(r'^4\.\s*|^Section\s+4|^4\s+', text, re.IGNORECASE):
            section_4_found = True
            section_4_paragraph_index = i
            print(f"📍 Section 4 found at paragraph {i+1}: '{text}'")
            break
    
    if not section_4_found:
        print("❌ Section 4 not found in document")
        return []
    
    # Find tables that appear after section 4
    section_4_tables = []
    
    # Method 1: Check document-level tables and estimate their position
    print(f"\n🔍 Looking for tables after Section 4...")
    
    for table_idx, table in enumerate(doc.tables):
        print(f"\nAnalyzing Table {table_idx + 1}:")
        
        # Check if table has the expected structure (4 columns based on your description)
        if len(table.columns) == 4:
            print(f"  ✅ Has 4 columns (matches expected structure)")
            
            # Show header row
            if len(table.rows) > 0:
                headers = [cell.text.strip() for cell in table.rows[0].cells]
                print(f"  Headers: {headers}")
                
                # Check if headers match control table pattern
                expected_patterns = ['control', 'description', 'test', 'result']
                header_match = any(any(pattern.lower() in header.lower() for pattern in expected_patterns) 
                                 for header in headers)
                
                if header_match:
                    print(f"  ✅ Headers match control table pattern")
                    section_4_tables.append((table_idx, table))
                else:
                    print(f"  ⚠️  Headers don't match expected pattern")
        else:
            print(f"  ❌ Has {len(table.columns)} columns (expected 4)")
    
    return section_4_tables

if __name__ == "__main__":
    template_path = "soc2t2-report-template-unqualified.docx"
    
    print("=== GENERAL DOCUMENT ANALYSIS ===")
    analyze_document_sections(template_path)
    
    print("\n\n=== SECTION 4 TABLE ANALYSIS ===")
    section_4_tables = find_section_4_tables(template_path)
    
    if section_4_tables:
        print(f"\n✅ Found {len(section_4_tables)} potential control tables")
        
        for table_idx, table in section_4_tables:
            print(f"\n📋 Detailed analysis of Table {table_idx + 1}:")
            print(f"   Rows: {len(table.rows)}, Columns: {len(table.columns)}")
            
            # Show sample data
            for row_idx, row in enumerate(table.rows[:5]):  # First 5 rows
                cells = [cell.text.strip() for cell in row.cells]
                print(f"   Row {row_idx + 1}:")
                for col_idx, cell_text in enumerate(cells):
                    print(f"     Col {col_idx + 1}: {cell_text[:100]}{'...' if len(cell_text) > 100 else ''}")
    else:
        print("❌ No control tables found in Section 4")