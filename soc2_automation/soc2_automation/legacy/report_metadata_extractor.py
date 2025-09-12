from docx import Document
import re
from datetime import datetime
import os
from typing import Dict, Optional, List

class ReportMetadataExtractor:
    """
    Extract company name and completion date from SOC2 reports
    """
    
    def __init__(self):
        # Common date patterns found in SOC2 reports
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD or YYYY-MM-DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',  # DD Month YYYY
            r'\b(?:as of|through|ending|ended)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',  # "as of Month DD, YYYY"
        ]
        
        # Company name indicators
        self.company_suffixes = [
            'inc', 'inc.', 'incorporated', 
            'corp', 'corp.', 'corporation',
            'llc', 'l.l.c.', 'limited liability company',
            'ltd', 'ltd.', 'limited',
            'co', 'co.', 'company',
            'technologies', 'tech', 'systems', 'services',
            'group', 'enterprises', 'solutions'
        ]
    
    def extract_company_name(self, doc_path: str) -> str:
        """
        Extract company name from document
        """
        doc = Document(doc_path)
        
        # Method 1: Check first few paragraphs for company name
        for i, para in enumerate(doc.paragraphs[:10]):
            text = para.text.strip()
            
            # Skip empty paragraphs
            if not text:
                continue
            
            # Look for company name patterns in early paragraphs
            # Usually appears in paragraphs 1-5
            if i <= 5:
                # Check if this looks like a company name
                text_lower = text.lower()
                
                # Skip common headers/titles
                skip_patterns = ['system and organization', 'soc 2', 'independent service', 'report', 'section']
                if any(pattern in text_lower for pattern in skip_patterns):
                    continue
                
                # Look for company suffixes
                if any(suffix in text_lower for suffix in self.company_suffixes):
                    return text
                
                # If it's a short line in early paragraphs, likely company name
                if len(text.split()) <= 6 and i <= 3:
                    return text
        
        # Method 2: Extract from filename as fallback
        filename = os.path.basename(doc_path)
        
        # Remove common patterns from filename
        filename_clean = filename.replace('.docx', '')
        filename_clean = re.sub(r'[-_]SOC\s*2.*', '', filename_clean, flags=re.IGNORECASE)
        filename_clean = re.sub(r'[-_]Attestation.*', '', filename_clean, flags=re.IGNORECASE)
        filename_clean = re.sub(r'[-_]Report.*', '', filename_clean, flags=re.IGNORECASE)
        filename_clean = re.sub(r'[-_]Final.*', '', filename_clean, flags=re.IGNORECASE)
        
        # Take the first part (usually company name)
        company_from_filename = filename_clean.split('-')[0].split('_')[0]
        
        return company_from_filename.strip()
    
    def extract_completion_date(self, doc_path: str) -> Optional[str]:
        """
        Extract completion/report date from document
        """
        doc = Document(doc_path)
        
        # Look for dates in first 20 paragraphs (where metadata usually appears)
        found_dates = []
        
        for para in doc.paragraphs[:20]:
            text = para.text
            
            for pattern in self.date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    found_dates.append((match, text))
        
        # Prioritize dates with context indicating completion/report date
        completion_keywords = [
            'as of', 'through', 'ending', 'ended', 'completed', 'report period',
            'examination period', 'audit period', 'period of', 'for the period'
        ]
        
        # First, look for dates with completion context
        for date, context in found_dates:
            context_lower = context.lower()
            if any(keyword in context_lower for keyword in completion_keywords):
                return self.normalize_date(date)
        
        # If no context-specific date found, return the latest date
        if found_dates:
            # Try to parse and find the most recent date
            parsed_dates = []
            for date, _ in found_dates:
                normalized = self.normalize_date(date)
                if normalized:
                    try:
                        parsed = datetime.strptime(normalized, '%Y-%m-%d')
                        parsed_dates.append((parsed, normalized))
                    except:
                        continue
            
            if parsed_dates:
                # Return the most recent date
                latest = max(parsed_dates, key=lambda x: x[0])
                return latest[1]
        
        return None
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date string to YYYY-MM-DD format
        """
        date_str = date_str.strip()
        
        # Remove common prefixes
        date_str = re.sub(r'^(as of|through|ending|ended)\s+', '', date_str, flags=re.IGNORECASE)
        
        # Try to parse various date formats
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%B %d, %Y', '%B %dth, %Y', '%B %dnd, %Y', '%B %dst, %Y', '%B %drd, %Y',
            '%d %B %Y', '%dth %B %Y', '%dnd %B %Y', '%dst %B %Y', '%drd %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def extract_metadata(self, doc_path: str) -> Dict[str, str]:
        """
        Extract both company name and completion date
        """
        company_name = self.extract_company_name(doc_path)
        completion_date = self.extract_completion_date(doc_path)
        
        return {
            'company_name': company_name,
            'completion_date': completion_date,
            'source_file': os.path.basename(doc_path)
        }

def test_metadata_extraction():
    """
    Test the metadata extraction with sample reports
    """
    extractor = ReportMetadataExtractor()
    
    reports_dir = "/home/levi/sandbox/soc2_automation/report_analysis/reports/"
    
    if not os.path.exists(reports_dir):
        print(f"❌ Reports directory not found: {reports_dir}")
        return
    
    reports = [f for f in os.listdir(reports_dir) if f.endswith('.docx')]
    
    print("🔍 Testing metadata extraction on all reports:")
    print("="*60)
    
    for report in reports[:5]:  # Test first 5 reports
        report_path = os.path.join(reports_dir, report)
        print(f"\n📄 {report}")
        
        try:
            metadata = extractor.extract_metadata(report_path)
            print(f"   🏢 Company: {metadata['company_name']}")
            print(f"   📅 Date: {metadata['completion_date']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_metadata_extraction()