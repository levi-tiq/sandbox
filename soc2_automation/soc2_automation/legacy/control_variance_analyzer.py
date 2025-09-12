#!/usr/bin/env python3
"""
SOC2 Control Variance Analyzer

Analyzes how tests_applied language varies across different companies for the same controls.
This helps understand patterns for automating report writing.

Usage:
    python3 control_variance_analyzer.py
    
    Or programmatically:
    from control_variance_analyzer import ControlVarianceAnalyzer
    
    analyzer = ControlVarianceAnalyzer()
    analyzer.load_reports("company_organized_reports.json")
    variance_data = analyzer.analyze_variance()
"""

import json
import os
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import difflib
import re

class ControlVarianceAnalyzer:
    """
    Analyze variance in tests_applied language across different companies
    """
    
    def __init__(self):
        self.reports = []
        self.control_matrix = {}  # Key: (control_id, control_name), Value: company variations
        self.variance_stats = {}
    
    def load_reports(self, reports_file: str):
        """Load the company organized reports"""
        with open(reports_file, 'r', encoding='utf-8') as f:
            self.reports = json.load(f)
        
        print(f"📊 Loaded {len(self.reports)} company reports")
    
    def create_control_key(self, control_id: str, control_name: str, control_description: str = "") -> str:
        """
        Create a unique key for control identification
        Handles cases where control_name might be empty
        """
        if control_name.strip():
            return f"{control_id}||{control_name.strip()}"
        else:
            # Fallback to using description (truncated)
            desc_key = control_description.strip()[:100] if control_description else "NO_NAME"
            return f"{control_id}||{desc_key}"
    
    def extract_control_matrix(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract all controls and organize by control_id + control_name pairs
        """
        print("🔍 Building control comparison matrix...")
        
        control_matrix = defaultdict(lambda: {
            'control_id': '',
            'control_name': '',
            'control_description': '',
            'companies': {},
            'total_companies': 0,
            'missing_from': []
        })
        
        all_companies = set()
        
        # First pass: collect all controls from all companies
        for report in self.reports:
            company_name = report['company_name']
            all_companies.add(company_name)
            
            for control in report['controls']:
                control_id = control['control_id']
                control_name = control.get('control_name', '')
                control_description = control.get('control_description', '')
                tests_applied = control.get('tests_applied', [])
                
                # Create unique key
                key = self.create_control_key(control_id, control_name, control_description)
                
                # Store control metadata
                if not control_matrix[key]['control_id']:
                    control_matrix[key]['control_id'] = control_id
                    control_matrix[key]['control_name'] = control_name or "NO_NAME"
                    control_matrix[key]['control_description'] = control_description
                
                # Store company-specific test data
                control_matrix[key]['companies'][company_name] = {
                    'tests_applied': tests_applied,
                    'test_count': len(tests_applied),
                    'test_result': control.get('test_result', ''),
                    'source_file': report.get('source_file', ''),
                    'completion_date': report.get('completion_date', '')
                }
        
        # Second pass: identify missing controls for each company
        for key, control_data in control_matrix.items():
            control_data['total_companies'] = len(control_data['companies'])
            
            # Find which companies are missing this control
            missing_companies = all_companies - set(control_data['companies'].keys())
            control_data['missing_from'] = list(missing_companies)
        
        self.control_matrix = dict(control_matrix)
        self.all_companies = all_companies
        
        print(f"✅ Found {len(self.control_matrix)} unique control variants")
        print(f"📈 Across {len(all_companies)} companies")
        
        return self.control_matrix
    
    def analyze_test_language_variance(self) -> Dict[str, Any]:
        """
        Analyze variance in test language for each control
        """
        print("📝 Analyzing test language variance...")
        
        variance_analysis = {}
        
        for key, control_data in self.control_matrix.items():
            control_id = control_data['control_id']
            control_name = control_data['control_name']
            companies = control_data['companies']
            
            # Collect all test variations
            all_test_variations = []
            company_test_map = {}
            
            for company, company_data in companies.items():
                tests = company_data['tests_applied']
                company_test_map[company] = tests
                
                for test in tests:
                    all_test_variations.append({
                        'company': company,
                        'test_text': test,
                        'test_length': len(test),
                        'word_count': len(test.split())
                    })
            
            # Analyze variance
            variance_data = {
                'control_id': control_id,
                'control_name': control_name,
                'total_companies_with_control': len(companies),
                'missing_from_companies': control_data['missing_from'],
                'company_tests': company_test_map,
                'all_variations': all_test_variations,
                'variance_metrics': self._calculate_variance_metrics(all_test_variations),
                'similarity_analysis': self._analyze_test_similarities(all_test_variations),
                'common_patterns': self._find_common_patterns(all_test_variations)
            }
            
            variance_analysis[key] = variance_data
        
        self.variance_stats = variance_analysis
        return variance_analysis
    
    def _calculate_variance_metrics(self, test_variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate variance metrics for test language"""
        if not test_variations:
            return {}
        
        test_lengths = [v['test_length'] for v in test_variations]
        word_counts = [v['word_count'] for v in test_variations]
        
        return {
            'total_test_instances': len(test_variations),
            'unique_test_texts': len(set(v['test_text'] for v in test_variations)),
            'avg_test_length': sum(test_lengths) / len(test_lengths),
            'min_test_length': min(test_lengths),
            'max_test_length': max(test_lengths),
            'avg_word_count': sum(word_counts) / len(word_counts),
            'min_word_count': min(word_counts),
            'max_word_count': max(word_counts)
        }
    
    def _analyze_test_similarities(self, test_variations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze similarities between test variations"""
        similarities = []
        test_texts = [v['test_text'] for v in test_variations]
        
        for i in range(len(test_texts)):
            for j in range(i + 1, len(test_texts)):
                text1 = test_texts[i]
                text2 = test_texts[j]
                
                # Calculate similarity ratio
                similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
                
                if similarity > 0.3:  # Only store meaningful similarities
                    similarities.append({
                        'company1': test_variations[i]['company'],
                        'company2': test_variations[j]['company'],
                        'similarity_ratio': similarity,
                        'text1_preview': text1[:100] + "..." if len(text1) > 100 else text1,
                        'text2_preview': text2[:100] + "..." if len(text2) > 100 else text2
                    })
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity_ratio'], reverse=True)
        
        return similarities[:10]  # Return top 10 most similar
    
    def _find_common_patterns(self, test_variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common patterns in test language"""
        all_texts = [v['test_text'] for v in test_variations]
        
        # Common starting words/phrases
        starting_phrases = defaultdict(int)
        action_verbs = defaultdict(int)
        
        verb_pattern = r'^(inquired|inspected|observed|reviewed|tested|verified|confirmed|obtained|selected|performed|compared|evaluated|reperformed)'
        
        for text in all_texts:
            # Extract first few words
            words = text.lower().split()
            if len(words) >= 3:
                starting_phrases[' '.join(words[:3])] += 1
            
            # Extract action verbs
            match = re.match(verb_pattern, text.lower())
            if match:
                action_verbs[match.group(1)] += 1
        
        # Sort by frequency
        top_starting_phrases = sorted(starting_phrases.items(), key=lambda x: x[1], reverse=True)[:10]
        top_action_verbs = sorted(action_verbs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'top_starting_phrases': top_starting_phrases,
            'top_action_verbs': top_action_verbs,
            'total_unique_texts': len(set(all_texts))
        }
    
    def generate_variance_report(self, output_file: str = "control_variance_report.json"):
        """Generate comprehensive variance report"""
        print("📋 Generating variance report...")
        
        from datetime import datetime
        
        report_data = {
            'generation_timestamp': datetime.now().isoformat(),
            'analysis_summary': {
                'total_unique_controls': len(self.control_matrix),
                'total_companies': len(self.all_companies),
                'companies_analyzed': list(self.all_companies)
            },
            'control_matrix': self.control_matrix,
            'variance_analysis': self.variance_stats,
            'global_patterns': self._analyze_global_patterns()
        }
        
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Variance report saved to: {output_file}")
        return report_data
    
    def _analyze_global_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across all controls"""
        all_action_verbs = defaultdict(int)
        all_starting_phrases = defaultdict(int)
        control_coverage = defaultdict(int)
        
        for key, variance_data in self.variance_stats.items():
            patterns = variance_data.get('common_patterns', {})
            
            # Aggregate action verbs
            for verb, count in patterns.get('top_action_verbs', []):
                all_action_verbs[verb] += count
            
            # Aggregate starting phrases
            for phrase, count in patterns.get('top_starting_phrases', []):
                all_starting_phrases[phrase] += count
            
            # Control coverage by company count
            company_count = variance_data['total_companies_with_control']
            control_coverage[company_count] += 1
        
        return {
            'most_common_action_verbs': sorted(all_action_verbs.items(), key=lambda x: x[1], reverse=True)[:20],
            'most_common_starting_phrases': sorted(all_starting_phrases.items(), key=lambda x: x[1], reverse=True)[:20],
            'control_coverage_distribution': dict(control_coverage)
        }
    
    def print_summary_stats(self):
        """Print summary statistics"""
        print("\n📊 VARIANCE ANALYSIS SUMMARY:")
        print("=" * 60)
        
        total_controls = len(self.control_matrix)
        total_companies = len(self.all_companies)
        
        print(f"🎯 Total unique controls: {total_controls}")
        print(f"🏢 Companies analyzed: {total_companies}")
        
        # Coverage statistics
        coverage_stats = defaultdict(int)
        high_variance_controls = []
        
        for key, variance_data in self.variance_stats.items():
            company_count = variance_data['total_companies_with_control']
            coverage_stats[company_count] += 1
            
            metrics = variance_data.get('variance_metrics', {})
            unique_tests = metrics.get('unique_test_texts', 0)
            total_tests = metrics.get('total_test_instances', 0)
            
            if total_tests > 0 and unique_tests / total_tests > 0.7:  # High variance
                high_variance_controls.append({
                    'key': key,
                    'control_id': variance_data['control_id'],
                    'control_name': variance_data['control_name'],
                    'variance_ratio': unique_tests / total_tests,
                    'unique_tests': unique_tests,
                    'total_tests': total_tests
                })
        
        print(f"\n📈 Control Coverage Distribution:")
        for company_count, control_count in sorted(coverage_stats.items()):
            print(f"   {company_count} companies: {control_count} controls")
        
        print(f"\n🌡️ High Variance Controls (>70% unique test language):")
        high_variance_controls.sort(key=lambda x: x['variance_ratio'], reverse=True)
        for control in high_variance_controls[:10]:
            print(f"   {control['control_id']} - {control['control_name'][:50]}... "
                  f"({control['unique_tests']}/{control['total_tests']} = {control['variance_ratio']:.1%})")

def main():
    """Main execution function"""
    analyzer = ControlVarianceAnalyzer()
    
    # Load reports
    reports_file = "company_organized_reports.json"
    if not os.path.exists(reports_file):
        print(f"❌ Reports file not found: {reports_file}")
        print("   Please run the enhanced batch extractor first")
        return
    
    analyzer.load_reports(reports_file)
    
    # Build control matrix
    analyzer.extract_control_matrix()
    
    # Analyze variance
    analyzer.analyze_test_language_variance()
    
    # Generate report
    analyzer.generate_variance_report()
    
    # Print summary
    analyzer.print_summary_stats()
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 Detailed report: control_variance_report.json")
    print(f"💡 Next: Use the CLI query tool to explore specific controls")

if __name__ == "__main__":
    main()