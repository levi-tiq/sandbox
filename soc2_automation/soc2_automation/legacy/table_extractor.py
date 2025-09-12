from docx import Document
import json
import re
import os
from typing import List, Dict, Any

class SOC2TableExtractor:
    """
    Extract control tables from SOC2 Word documents and convert to JSON
    """
    
    def __init__(self):
        self.extracted_data = []
    
    def is_control_table(self, table) -> bool:
        """
        Determine if a table is a control table based on structure and headers
        """
        # Must have exactly 4 columns
        if len(table.columns) != 4:
            return False
        
        # Must have at least 2 rows (header + data)
        if len(table.rows) < 2:
            return False
        
        # Check header row for expected patterns
        if len(table.rows) > 0:
            headers = [cell.text.strip().lower() for cell in table.rows[0].cells]
            
            # Expected header patterns
            expected_patterns = [
                ['control', 'description', 'test', 'result'],
                ['number', 'activities', 'applied', 'results'],
                ['control number', 'description of control activities', 'test applied', 'test results']
            ]
            
            # Check if headers match any pattern
            for pattern in expected_patterns:
                matches = sum(1 for i, header in enumerate(headers) 
                            if i < len(pattern) and pattern[i] in header)
                if matches >= 3:  # At least 3 out of 4 headers match
                    return True
        
        return False
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def extract_bullet_points(self, text: str) -> List[str]:
        """
        Extract bullet points from text, splitting by newlines
        """
        if not text:
            return []
        
        # Split by newlines and clean each line
        lines = [self.clean_text(line) for line in text.split('\n')]
        
        # Filter out empty lines
        bullet_points = [line for line in lines if line]
        
        return bullet_points
    
    def extract_table_data(self, table) -> List[Dict[str, Any]]:
        """
        Extract data from a single control table
        """
        if not self.is_control_table(table):
            return []
        
        extracted_controls = []
        
        # Skip header row (index 0)
        for row_idx, row in enumerate(table.rows[1:], 1):
            try:
                # Extract cell data
                cells = [cell.text.strip() for cell in row.cells]
                
                if len(cells) < 4:
                    continue  # Skip incomplete rows
                
                control_id = self.clean_text(cells[0])
                description = self.clean_text(cells[1])
                tests_applied_raw = self.clean_text(cells[2])
                test_result = self.clean_text(cells[3])
                
                # Skip rows where control_id is empty (might be continuation rows)
                if not control_id:
                    continue
                
                # Extract bullet points from tests applied
                tests_applied = self.extract_bullet_points(tests_applied_raw)
                
                # Create control object
                control_obj = {
                    "control_id": control_id,
                    "control_description": description,
                    "tests_applied": tests_applied,
                    "test_result": test_result,
                    "source_row": row_idx,
                    "raw_tests_text": tests_applied_raw  # Keep raw text for debugging
                }
                
                extracted_controls.append(control_obj)
                
            except Exception as e:
                print(f"⚠️  Error processing row {row_idx}: {e}")
                continue
        
        return extracted_controls
    
    def extract_from_document(self, docx_path: str) -> List[Dict[str, Any]]:
        """
        Extract all control table data from a single document
        """
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"Document not found: {docx_path}")
        
        print(f"📄 Processing document: {docx_path}")
        
        doc = Document(docx_path)
        document_data = []
        
        for table_idx, table in enumerate(doc.tables):
            if self.is_control_table(table):
                print(f"  📋 Processing control table {table_idx + 1} ({len(table.rows)} rows)")
                
                table_data = self.extract_table_data(table)
                
                # Add table metadata to each control
                for control in table_data:
                    control['source_document'] = os.path.basename(docx_path)
                    control['source_table'] = table_idx + 1
                
                document_data.extend(table_data)
                print(f"     ✅ Extracted {len(table_data)} controls")
        
        return document_data
    
    def extract_from_documents(self, document_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Extract control data from multiple documents
        """
        all_data = []
        
        for doc_path in document_paths:
            try:
                doc_data = self.extract_from_document(doc_path)
                all_data.extend(doc_data)
            except Exception as e:
                print(f"❌ Error processing {doc_path}: {e}")
        
        return all_data
    
    def save_to_json(self, data: List[Dict[str, Any]], output_path: str, pretty=True):
        """
        Save extracted data to JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        print(f"💾 Saved {len(data)} controls to {output_path}")
    
    def get_summary_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for extracted data
        """
        if not data:
            return {}
        
        # Count by control_id
        control_counts = {}
        for item in data:
            control_id = item['control_id']
            control_counts[control_id] = control_counts.get(control_id, 0) + 1
        
        # Count by document
        doc_counts = {}
        for item in data:
            doc = item.get('source_document', 'unknown')
            doc_counts[doc] = doc_counts.get(doc, 0) + 1
        
        return {
            'total_controls': len(data),
            'unique_control_ids': len(control_counts),
            'control_id_distribution': control_counts,
            'document_distribution': doc_counts,
            'most_common_control_id': max(control_counts.items(), key=lambda x: x[1]) if control_counts else None
        }

def main():
    """
    Main function to test the extractor
    """
    extractor = SOC2TableExtractor()
    
    # Test with the SOC2 template
    template_path = "soc2t2-report-template-unqualified.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return
    
    try:
        # Extract data
        print("🚀 Starting extraction...")
        extracted_data = extractor.extract_from_document(template_path)
        
        # Save to JSON
        output_path = "soc2_controls_extracted.json"
        extractor.save_to_json(extracted_data, output_path)
        
        # Print summary
        stats = extractor.get_summary_stats(extracted_data)
        print(f"\n📊 Extraction Summary:")
        print(f"   Total controls extracted: {stats['total_controls']}")
        print(f"   Unique control IDs: {stats['unique_control_ids']}")
        
        if stats.get('most_common_control_id'):
            most_common = stats['most_common_control_id']
            print(f"   Most common control ID: {most_common[0]} ({most_common[1]} instances)")
        
        # Show sample data
        if extracted_data:
            print(f"\n📋 Sample extracted control:")
            sample = extracted_data[0]
            print(f"   Control ID: {sample['control_id']}")
            print(f"   Description: {sample['control_description'][:100]}...")
            print(f"   Tests Applied: {len(sample['tests_applied'])} items")
            print(f"   Test Result: {sample['test_result']}")
        
        print(f"\n✅ Extraction complete! Data saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()