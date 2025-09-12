#!/usr/bin/env python3
"""
Enhanced SOC2 Batch Table Extractor with Company and Date Organization

This script processes an array of Word documents to extract control table data
and organizes it by company name and completion date.

Output structure:
{
  "company_name": "A-1 Credit Recovery & Collection Services Inc.",
  "completion_date": "2024-06-15",
  "source_file": "A1CRS-SOC 2-Type 2-Attestation-Report_Final.docx",
  "controls": [
    {
      "control_id": "CC1.1",
      "control_description": "Sets the Tone at the Top...",
      "tests_applied": ["Inquired to determine..."],
      "test_result": "No Exception Noted"
    },
    ...
  ],
  "summary": {
    "total_controls": 197,
    "unique_control_ids": 33,
    "control_id_counts": {"CC1.1": 5, "CC1.2": 4, ...}
  }
}
"""

import os
import json
import glob
import re
from typing import List, Dict, Any, Optional
from table_extractor import SOC2TableExtractor
from report_metadata_extractor import ReportMetadataExtractor

class EnhancedSOC2Extractor:
    """
    Enhanced extractor that organizes data by company and date
    """
    
    def __init__(self):
        self.table_extractor = SOC2TableExtractor()
        self.metadata_extractor = ReportMetadataExtractor()
    
    def parse_control_name_and_description(self, full_description: str) -> Dict[str, str]:
        """
        Split control description into name and description using '—' or '-' as separator
        """
        # Look for em dash (—) first, then regular dash (-)
        separators = ['—', '–', '-']
        
        for separator in separators:
            if separator in full_description:
                parts = full_description.split(separator, 1)  # Split on first occurrence only
                if len(parts) == 2:
                    control_name = parts[0].strip()
                    description = parts[1].strip()
                    return {
                        'control_name': control_name,
                        'control_description': description
                    }
        
        # If no separator found, treat entire text as description
        return {
            'control_name': '',
            'control_description': full_description.strip()
        }
    
    def parse_tests_applied(self, tests_text: str) -> List[str]:
        """
        Parse tests applied text into separate bullet points
        Handles various bullet point formats including dashes and action verbs
        """
        if not tests_text or not tests_text.strip():
            return []
        
        # Clean up the text
        text = tests_text.strip()
        
        # Split by common bullet point indicators and action verbs
        # Look for patterns like:
        # - "Inquired to determine..."
        # - "Inspected the..."  
        # - "Observed that..."
        # - "Reperformed..."
        
        action_verbs = [
            'inquired', 'inspected', 'observed', 'reperformed', 'reviewed', 
            'examined', 'tested', 'verified', 'confirmed', 'validated',
            'obtained', 'selected', 'performed', 'compared', 'evaluated'
        ]
        
        # First, try splitting on paragraph breaks (double newlines)
        paragraphs = re.split(r'\n\s*\n', text)
        if len(paragraphs) > 1:
            # Clean each paragraph
            parsed_tests = []
            for paragraph in paragraphs:
                clean_para = paragraph.strip()
                if clean_para:
                    # Remove leading dashes or bullets
                    clean_para = re.sub(r'^[-•▪▫‣⁃]\s*', '', clean_para)
                    parsed_tests.append(clean_para)
            return parsed_tests
        
        # Second, try splitting on single newlines followed by action verbs
        lines = text.split('\n')
        if len(lines) > 1:
            parsed_tests = []
            current_test = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with action verb (case insensitive)
                starts_with_verb = any(line.lower().startswith(verb) for verb in action_verbs)
                starts_with_bullet = line.startswith(('-', '•', '▪', '▫', '‣', '⁃'))
                
                if (starts_with_verb or starts_with_bullet) and current_test:
                    # Save previous test and start new one
                    test_text = ' '.join(current_test).strip()
                    if test_text:
                        # Remove leading bullets from the joined text
                        test_text = re.sub(r'^[-•▪▫‣⁃]\s*', '', test_text)
                        parsed_tests.append(test_text)
                    current_test = [line]
                else:
                    # Continue current test
                    current_test.append(line)
            
            # Add the last test
            if current_test:
                test_text = ' '.join(current_test).strip()
                if test_text:
                    test_text = re.sub(r'^[-•▪▫‣⁃]\s*', '', test_text)
                    parsed_tests.append(test_text)
            
            if len(parsed_tests) > 1:
                return parsed_tests
        
        # Third, try splitting on sentence boundaries with action verbs
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        if len(sentences) > 1:
            parsed_tests = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and any(sentence.lower().startswith(verb) for verb in action_verbs):
                    # Remove leading bullets
                    sentence = re.sub(r'^[-•▪▫‣⁃]\s*', '', sentence)
                    parsed_tests.append(sentence)
            
            if len(parsed_tests) > 1:
                return parsed_tests
        
        # Fourth, try splitting on action verbs within continuous text (no line breaks)
        # Look for patterns like "...providers and business partners Inspected the most current..."
        # This handles cases where bullet points are concatenated without proper line breaks
        verb_pattern = r'\b(' + '|'.join(action_verbs) + r')\b'
        
        # Find all positions where action verbs start new sentences
        matches = list(re.finditer(verb_pattern, text, re.IGNORECASE))
        
        if len(matches) > 1:
            parsed_tests = []
            
            for i, match in enumerate(matches):
                start_pos = match.start()
                
                # For the first match, take everything from the beginning
                if i == 0:
                    if start_pos > 0:
                        # There's text before the first verb - might be part of previous test
                        continue
                
                # Find the end position (start of next verb or end of text)
                if i + 1 < len(matches):
                    end_pos = matches[i + 1].start()
                else:
                    end_pos = len(text)
                
                # Extract the test text
                test_text = text[start_pos:end_pos].strip()
                
                if test_text:
                    # Clean up the text
                    test_text = re.sub(r'^[-•▪▫‣⁃]\s*', '', test_text)
                    parsed_tests.append(test_text)
            
            # If we didn't capture the beginning and it doesn't start with a verb
            if matches and matches[0].start() > 0:
                first_part = text[:matches[0].start()].strip()
                if first_part:
                    first_part = re.sub(r'^[-•▪▫‣⁃]\s*', '', first_part)
                    parsed_tests.insert(0, first_part)
            
            if len(parsed_tests) > 1:
                return parsed_tests
        
        # If no clear separation found, return as single item
        clean_text = re.sub(r'^[-•▪▫‣⁃]\s*', '', text)
        return [clean_text] if clean_text else []
    
    def extract_report_data(self, doc_path: str, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Extract complete report data including metadata and controls with enhanced parsing
        """
        # Extract metadata
        metadata = self.metadata_extractor.extract_metadata(doc_path)
        
        # Extract controls using base extractor
        raw_controls = self.table_extractor.extract_from_document(doc_path)
        
        # Enhance controls with new parsing
        enhanced_controls = []
        for control in raw_controls:
            # Parse control name and description
            name_desc = self.parse_control_name_and_description(control['control_description'])
            
            # Parse tests applied into separate bullet points
            tests_applied = self.parse_tests_applied(control.get('raw_tests_text', ''))
            
            # Build enhanced control object
            enhanced_control = {
                'control_id': control['control_id'],
                'control_name': name_desc['control_name'],
                'control_description': name_desc['control_description'],
                'tests_applied': tests_applied,
                'test_result': control['test_result']
            }
            
            # Add metadata fields if requested
            if include_metadata:
                enhanced_control.update({
                    'source_row': control.get('source_row'),
                    'raw_tests_text': control.get('raw_tests_text'),
                    'source_document': control.get('source_document'),
                    'source_table': control.get('source_table')
                })
            
            enhanced_controls.append(enhanced_control)
        
        # Generate summary statistics
        summary = self._generate_control_summary(enhanced_controls)
        
        # Build report object
        report_data = {
            'company_name': metadata['company_name'],
            'completion_date': metadata['completion_date'],
            'source_file': metadata['source_file'],
            'controls': enhanced_controls,
            'summary': summary
        }
        
        return report_data
    
    def _generate_control_summary(self, controls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for controls
        """
        if not controls:
            return {
                'total_controls': 0,
                'unique_control_ids': 0,
                'control_id_counts': {},
                'test_result_counts': {}
            }
        
        # Count by control_id
        control_counts = {}
        for control in controls:
            control_id = control['control_id']
            control_counts[control_id] = control_counts.get(control_id, 0) + 1
        
        # Count test results
        result_counts = {}
        for control in controls:
            result = control.get('test_result', 'Unknown').strip()
            if not result:
                result = 'Not Specified'
            result_counts[result] = result_counts.get(result, 0) + 1
        
        return {
            'total_controls': len(controls),
            'unique_control_ids': len(control_counts),
            'control_id_counts': control_counts,
            'test_result_counts': result_counts
        }
    
    def extract_from_reports(
        self, 
        document_paths: List[str], 
        output_json_path: Optional[str] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract data from multiple reports, organized by company and date
        """
        print(f"🚀 Processing {len(document_paths)} reports...")
        
        reports = []
        
        for i, doc_path in enumerate(document_paths, 1):
            print(f"\n📄 [{i}/{len(document_paths)}] Processing: {os.path.basename(doc_path)}")
            
            if not os.path.exists(doc_path):
                print(f"   ⚠️  File not found, skipping: {doc_path}")
                continue
            
            try:
                report_data = self.extract_report_data(doc_path, include_metadata)
                reports.append(report_data)
                
                print(f"   🏢 Company: {report_data['company_name']}")
                print(f"   📅 Date: {report_data['completion_date']}")
                print(f"   ✅ Extracted {report_data['summary']['total_controls']} controls")
                
            except Exception as e:
                print(f"   ❌ Error processing document: {e}")
                continue
        
        # Sort reports by company name, then by date
        reports.sort(key=lambda x: (x['company_name'], x['completion_date'] or ''))
        
        # Save to JSON if path provided
        if output_json_path:
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(reports, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Saved {len(reports)} reports to {output_json_path}")
            
            # Create combined summary
            combined_summary_path = output_json_path.replace('.json', '_combined_summary.json')
            self._create_combined_summary(reports, combined_summary_path)
        
        # Print overall summary
        self._print_batch_summary(reports)
        
        return reports
    
    def _create_combined_summary(self, reports: List[Dict[str, Any]], output_path: str):
        """
        Create a combined summary JSON from all reports
        """
        if not reports:
            return
        
        # Aggregate data across all reports
        total_controls = 0
        all_control_ids = set()
        all_control_id_counts = {}
        all_test_result_counts = {}
        all_control_names = set()
        
        company_summaries = []
        
        for report in reports:
            summary = report['summary']
            
            # Aggregate totals
            total_controls += summary['total_controls']
            
            # Collect unique control IDs
            for control_id, count in summary['control_id_counts'].items():
                all_control_ids.add(control_id)
                all_control_id_counts[control_id] = all_control_id_counts.get(control_id, 0) + count
            
            # Aggregate test results
            for result, count in summary['test_result_counts'].items():
                all_test_result_counts[result] = all_test_result_counts.get(result, 0) + count
            
            # Collect control names from this report
            report_control_names = set()
            for control in report['controls']:
                if control.get('control_name'):
                    control_name = control['control_name']
                    all_control_names.add(control_name)
                    report_control_names.add(control_name)
            
            # Create company summary
            company_summary = {
                'company_name': report['company_name'],
                'completion_date': report['completion_date'],
                'source_file': report['source_file'],
                'total_controls': summary['total_controls'],
                'unique_control_ids': summary['unique_control_ids'],
                'unique_control_names': len(report_control_names),
                'control_id_counts': summary['control_id_counts'],
                'test_result_counts': summary['test_result_counts']
            }
            company_summaries.append(company_summary)
        
        # Add current timestamp
        from datetime import datetime
        
        # Create overall combined summary
        combined_summary = {
            'generation_timestamp': datetime.now().isoformat(),
            'total_reports': len(reports),
            'total_companies': len(set(report['company_name'] for report in reports)),
            'total_controls_across_all_reports': total_controls,
            'unique_control_ids_across_all_reports': len(all_control_ids),
            'unique_control_names_across_all_reports': len(all_control_names),
            'combined_control_id_counts': all_control_id_counts,
            'combined_test_result_counts': all_test_result_counts,
            'date_range': {
                'earliest_date': min((r['completion_date'] for r in reports if r['completion_date']), default=None),
                'latest_date': max((r['completion_date'] for r in reports if r['completion_date']), default=None)
            },
            'company_summaries': company_summaries,
            'top_control_ids': sorted(all_control_id_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'all_control_ids': sorted(list(all_control_ids)),
            'all_control_names': sorted(list(all_control_names))
        }
        
        # Save combined summary
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined_summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Created combined summary: {output_path}")
        print(f"   📋 {total_controls} total controls across {len(reports)} reports")
        print(f"   🏷️  {len(all_control_ids)} unique control IDs")
        print(f"   📝 {len(all_control_names)} unique control names")
    
    def _print_batch_summary(self, reports: List[Dict[str, Any]]):
        """
        Print summary statistics for the batch
        """
        if not reports:
            return
        
        total_controls = sum(report['summary']['total_controls'] for report in reports)
        companies = set(report['company_name'] for report in reports)
        
        print(f"\n📊 Batch Summary:")
        print(f"   📋 Total controls extracted: {total_controls}")
        print(f"   🏢 Companies processed: {len(companies)}")
        print(f"   📄 Reports processed: {len(reports)}")
        
        print(f"\n🏢 Companies:")
        for report in reports:
            print(f"   • {report['company_name']} ({report['completion_date']}) - {report['summary']['total_controls']} controls")
    
    def find_reports_in_directory(self, directory: str = ".") -> List[str]:
        """
        Find all SOC2 report documents in a directory
        """
        pattern = os.path.join(directory, "*.docx")
        files = glob.glob(pattern)
        
        # Filter out temporary files
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        
        return sorted(files)
    
    def extract_by_company(self, reports: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group reports by company name
        """
        by_company = {}
        
        for report in reports:
            company = report['company_name']
            if company not in by_company:
                by_company[company] = []
            by_company[company].append(report)
        
        return by_company
    
    def extract_by_date_range(
        self, 
        reports: List[Dict[str, Any]], 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Filter reports by date range (YYYY-MM-DD format)
        """
        filtered = []
        
        for report in reports:
            date = report['completion_date']
            if date and start_date <= date <= end_date:
                filtered.append(report)
        
        return filtered

def main():
    """
    Main function for testing with the reports directory
    """
    extractor = EnhancedSOC2Extractor()
    
    # Use the reports directory
    reports_dir = "/home/levi/sandbox/soc2_automation/report_analysis/reports/"
    
    if not os.path.exists(reports_dir):
        print(f"❌ Reports directory not found: {reports_dir}")
        return
    
    # Find all reports
    report_files = extractor.find_reports_in_directory(reports_dir)
    
    if not report_files:
        print(f"❌ No .docx files found in {reports_dir}")
        return
    
    print(f"🔍 Found {len(report_files)} reports:")
    for report in report_files:
        print(f"   📄 {os.path.basename(report)}")
    
    # Extract data from all reports
    output_file = "company_organized_reports.json"
    extracted_reports = extractor.extract_from_reports(report_files, output_file)
    
    # Example analysis operations
    if extracted_reports:
        print(f"\n🔧 Analysis Examples:")
        
        # Group by company
        by_company = extractor.extract_by_company(extracted_reports)
        print(f"   📊 Reports by company:")
        for company, company_reports in by_company.items():
            print(f"     • {company}: {len(company_reports)} report(s)")
        
        # Filter by date range (example: 2024 reports)
        reports_2024 = extractor.extract_by_date_range(extracted_reports, "2024-01-01", "2024-12-31")
        if reports_2024:
            print(f"   📅 2024 reports: {len(reports_2024)} found")
        
        # Save company-specific reports
        for company, company_reports in by_company.items():
            if len(company_reports) > 0:
                company_filename = f"{company.replace(' ', '_').replace('/', '_')}_reports.json"
                with open(company_filename, 'w', encoding='utf-8') as f:
                    json.dump(company_reports, f, indent=2, ensure_ascii=False)
                print(f"   💾 Saved {company} reports to {company_filename}")
    
    print(f"\n✅ Enhanced extraction complete!")
    print(f"   📁 Main output: {output_file}")

if __name__ == "__main__":
    main()