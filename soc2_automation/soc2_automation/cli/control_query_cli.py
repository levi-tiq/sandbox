#!/usr/bin/env python3
"""
SOC2 Control Query CLI

Interactive command-line interface to explore control variance data.
Allows querying specific controls to see how test language varies across companies.

Usage:
    python3 control_query_cli.py
    
Commands:
    search <control_id>              - Find all controls with this ID
    show <control_id> <control_name> - Show detailed variance for specific control
    list high-variance               - Show controls with highest language variance
    list missing                     - Show controls missing from multiple companies
    compare <control_id>             - Compare all variations of a control ID
    patterns                         - Show common language patterns
    stats                            - Show overall statistics
    export <control_id>              - Export control data to JSON
    help                             - Show this help
    quit                             - Exit
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
import difflib
from tabulate import tabulate

class ControlQueryCLI:
    """
    Interactive CLI for querying control variance data
    """
    
    def __init__(self):
        self.variance_data = None
        self.control_matrix = None
        self.companies = set()
        self.loaded = False
    
    def load_data(self, variance_file: str = "data/processed/latest/control_variance_report.json"):
        """Load the variance analysis data"""
        if not os.path.exists(variance_file):
            print(f"❌ Variance report not found: {variance_file}")
            print("   Please run control_variance_analyzer.py first")
            return False
        
        try:
            with open(variance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.variance_data = data.get('variance_analysis', {})
            self.control_matrix = data.get('control_matrix', {})
            self.companies = set(data.get('analysis_summary', {}).get('companies_analyzed', []))
            self.loaded = True
            
            print(f"✅ Loaded data for {len(self.variance_data)} controls across {len(self.companies)} companies")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def search_controls(self, control_id: str) -> List[Dict[str, Any]]:
        """Search for all controls matching a control ID"""
        matches = []
        
        for key, variance_data in self.variance_data.items():
            if variance_data['control_id'].lower() == control_id.lower():
                matches.append({
                    'key': key,
                    'control_id': variance_data['control_id'],
                    'control_name': variance_data['control_name'],
                    'companies_with_control': variance_data['total_companies_with_control'],
                    'missing_from': len(variance_data['missing_from_companies']),
                    'unique_tests': variance_data['variance_metrics'].get('unique_test_texts', 0),
                    'total_tests': variance_data['variance_metrics'].get('total_test_instances', 0)
                })
        
        return matches
    
    def show_control_detail(self, control_id: str, control_name: str = None) -> Optional[Dict[str, Any]]:
        """Show detailed variance analysis for a specific control"""
        # Find the exact match
        target_key = None
        
        for key, variance_data in self.variance_data.items():
            if variance_data['control_id'].lower() == control_id.lower():
                if control_name is None or control_name.lower() in variance_data['control_name'].lower():
                    target_key = key
                    break
        
        if not target_key:
            return None
        
        return self.variance_data[target_key]
    
    def list_high_variance_controls(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """List controls with highest language variance"""
        variance_controls = []
        
        for key, variance_data in self.variance_data.items():
            metrics = variance_data.get('variance_metrics', {})
            unique_tests = metrics.get('unique_test_texts', 0)
            total_tests = metrics.get('total_test_instances', 0)
            
            if total_tests > 0:
                variance_ratio = unique_tests / total_tests
                variance_controls.append({
                    'key': key,
                    'control_id': variance_data['control_id'],
                    'control_name': variance_data['control_name'],
                    'variance_ratio': variance_ratio,
                    'unique_tests': unique_tests,
                    'total_tests': total_tests,
                    'companies_count': variance_data['total_companies_with_control']
                })
        
        variance_controls.sort(key=lambda x: x['variance_ratio'], reverse=True)
        return variance_controls[:top_n]
    
    def list_missing_controls(self, min_missing: int = 2) -> List[Dict[str, Any]]:
        """List controls missing from multiple companies"""
        missing_controls = []
        
        for key, variance_data in self.variance_data.items():
            missing_count = len(variance_data['missing_from_companies'])
            
            if missing_count >= min_missing:
                missing_controls.append({
                    'key': key,
                    'control_id': variance_data['control_id'],
                    'control_name': variance_data['control_name'],
                    'missing_from_count': missing_count,
                    'missing_from_companies': variance_data['missing_from_companies'],
                    'present_in_count': variance_data['total_companies_with_control']
                })
        
        missing_controls.sort(key=lambda x: x['missing_from_count'], reverse=True)
        return missing_controls
    
    def compare_control_variations(self, control_id: str) -> Dict[str, Any]:
        """Compare all variations of a control ID across companies"""
        variations = {}
        
        for key, variance_data in self.variance_data.items():
            if variance_data['control_id'].lower() == control_id.lower():
                variations[key] = {
                    'control_name': variance_data['control_name'],
                    'company_tests': variance_data['company_tests'],
                    'similarities': variance_data['similarity_analysis'],
                    'patterns': variance_data['common_patterns']
                }
        
        return variations
    
    def export_control_data(self, control_id: str, output_file: str = None) -> bool:
        """Export specific control data to JSON"""
        if not output_file:
            output_file = f"{control_id.replace(' ', '_').replace('.', '_')}_analysis.json"
        
        variations = self.compare_control_variations(control_id)
        
        if not variations:
            return False
        
        export_data = {
            'control_id': control_id,
            'export_timestamp': json.dumps({}).__class__().__name__,  # Will be replaced
            'variations': variations
        }
        
        from datetime import datetime
        export_data['export_timestamp'] = datetime.now().isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def run_interactive(self):
        """Run the interactive CLI"""
        if not self.loaded:
            print("❌ No data loaded. Loading variance report...")
            if not self.load_data():
                return
        
        print("🔍 SOC2 Control Variance Query CLI")
        print("Type 'help' for available commands, 'quit' to exit")
        print("=" * 60)
        
        while True:
            try:
                command = input("\n🎯 Query> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    print("👋 Goodbye!")
                    break
                
                elif cmd == 'help':
                    self.show_help()
                
                elif cmd == 'search' and len(parts) >= 2:
                    control_id = parts[1]
                    self.handle_search(control_id)
                
                elif cmd == 'show' and len(parts) >= 2:
                    control_id = parts[1]
                    control_name = ' '.join(parts[2:]) if len(parts) > 2 else None
                    self.handle_show(control_id, control_name)
                
                elif cmd == 'list' and len(parts) >= 2:
                    list_type = parts[1].lower()
                    if list_type == 'high-variance':
                        self.handle_list_high_variance()
                    elif list_type == 'missing':
                        self.handle_list_missing()
                    else:
                        print(f"❌ Unknown list type: {list_type}")
                
                elif cmd == 'compare' and len(parts) >= 2:
                    control_id = parts[1]
                    self.handle_compare(control_id)
                
                elif cmd == 'patterns':
                    self.handle_patterns()
                
                elif cmd == 'stats':
                    self.handle_stats()
                
                elif cmd == 'export' and len(parts) >= 2:
                    control_id = parts[1]
                    output_file = parts[2] if len(parts) > 2 else None
                    self.handle_export(control_id, output_file)
                
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("Type 'help' for available commands")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show available commands"""
        help_text = """
🔍 Available Commands:

search <control_id>              - Find all controls with this ID
                                  Example: search CC1.1

show <control_id> [control_name] - Show detailed variance for specific control
                                  Example: show CC1.1
                                  Example: show CC1.1 "Sets the Tone"

list high-variance              - Show controls with highest language variance
list missing                    - Show controls missing from multiple companies

compare <control_id>            - Compare all variations of a control ID
                                 Example: compare CC1.1

patterns                        - Show common language patterns across all controls
stats                          - Show overall statistics
export <control_id> [filename] - Export control data to JSON

help                           - Show this help
quit                          - Exit the CLI
        """
        print(help_text)
    
    def handle_search(self, control_id: str):
        """Handle search command"""
        matches = self.search_controls(control_id)
        
        if not matches:
            print(f"❌ No controls found with ID: {control_id}")
            return
        
        print(f"🔍 Found {len(matches)} control(s) with ID '{control_id}':")
        
        headers = ['Control Name', 'Companies', 'Missing', 'Unique Tests', 'Total Tests', 'Variance %']
        rows = []
        
        for match in matches:
            variance_pct = (match['unique_tests'] / match['total_tests'] * 100) if match['total_tests'] > 0 else 0
            rows.append([
                match['control_name'][:50] + ("..." if len(match['control_name']) > 50 else ""),
                f"{match['companies_with_control']}/{len(self.companies)}",
                match['missing_from'],
                match['unique_tests'],
                match['total_tests'],
                f"{variance_pct:.1f}%"
            ])
        
        print(tabulate(rows, headers=headers, tablefmt='grid'))
    
    def handle_show(self, control_id: str, control_name: str = None):
        """Handle show command"""
        control_data = self.show_control_detail(control_id, control_name)
        
        if not control_data:
            print(f"❌ Control not found: {control_id}" + (f" '{control_name}'" if control_name else ""))
            return
        
        print(f"\n📋 Control Details: {control_data['control_id']} - {control_data['control_name']}")
        print("=" * 80)
        
        print(f"📊 Coverage: {control_data['total_companies_with_control']}/{len(self.companies)} companies")
        
        if control_data['missing_from_companies']:
            print(f"❌ Missing from: {', '.join(control_data['missing_from_companies'])}")
        
        metrics = control_data.get('variance_metrics', {})
        if metrics:
            print(f"📈 Variance: {metrics.get('unique_test_texts', 0)}/{metrics.get('total_test_instances', 0)} unique tests")
            print(f"📏 Avg length: {metrics.get('avg_test_length', 0):.0f} chars, {metrics.get('avg_word_count', 0):.0f} words")
        
        print(f"\n🏢 Test Variations by Company:")
        for company, company_data in control_data['company_tests'].items():
            tests = company_data if isinstance(company_data, list) else company_data.get('tests_applied', [])
            print(f"\n  📌 {company}:")
            for i, test in enumerate(tests, 1):
                preview = test[:100] + "..." if len(test) > 100 else test
                print(f"     {i}. {preview}")
    
    def handle_list_high_variance(self):
        """Handle list high-variance command"""
        high_variance = self.list_high_variance_controls()
        
        print(f"🌡️ Top {len(high_variance)} High Variance Controls:")
        
        headers = ['Control ID', 'Control Name', 'Companies', 'Unique/Total', 'Variance %']
        rows = []
        
        for control in high_variance:
            rows.append([
                control['control_id'],
                control['control_name'][:40] + ("..." if len(control['control_name']) > 40 else ""),
                f"{control['companies_count']}/{len(self.companies)}",
                f"{control['unique_tests']}/{control['total_tests']}",
                f"{control['variance_ratio']:.1%}"
            ])
        
        print(tabulate(rows, headers=headers, tablefmt='grid'))
    
    def handle_list_missing(self):
        """Handle list missing command"""
        missing = self.list_missing_controls()
        
        print(f"❌ Controls Missing from Multiple Companies:")
        
        headers = ['Control ID', 'Control Name', 'Present In', 'Missing From', 'Missing Companies']
        rows = []
        
        for control in missing[:15]:  # Top 15
            missing_companies = ', '.join(control['missing_from_companies'][:3])
            if len(control['missing_from_companies']) > 3:
                missing_companies += f" (+{len(control['missing_from_companies']) - 3} more)"
            
            rows.append([
                control['control_id'],
                control['control_name'][:30] + ("..." if len(control['control_name']) > 30 else ""),
                f"{control['present_in_count']}/{len(self.companies)}",
                control['missing_from_count'],
                missing_companies
            ])
        
        print(tabulate(rows, headers=headers, tablefmt='grid'))
    
    def handle_compare(self, control_id: str):
        """Handle compare command"""
        variations = self.compare_control_variations(control_id)
        
        if not variations:
            print(f"❌ No variations found for control ID: {control_id}")
            return
        
        print(f"🔀 Comparing all variations of {control_id}:")
        print("=" * 80)
        
        for key, variation in variations.items():
            print(f"\n📋 Variation: {variation['control_name']}")
            print(f"🏢 Companies with this variation: {len(variation['company_tests'])}")
            
            # Show unique test patterns
            all_tests = []
            for company, tests in variation['company_tests'].items():
                if isinstance(tests, list):
                    all_tests.extend(tests)
                else:
                    all_tests.extend(tests.get('tests_applied', []))
            
            unique_tests = list(set(all_tests))
            print(f"🎯 Unique test patterns: {len(unique_tests)}")
            
            # Show top similarities if available
            similarities = variation.get('similarities', [])
            if similarities:
                print(f"🔗 Top similarity: {similarities[0]['similarity_ratio']:.1%} between "
                      f"{similarities[0]['company1']} and {similarities[0]['company2']}")
    
    def handle_patterns(self):
        """Handle patterns command"""
        # This would need to be loaded from the global patterns in the variance report
        print("📊 Common Language Patterns:")
        print("(This feature requires loading global patterns from the variance report)")
        # TODO: Implement pattern display from loaded data
    
    def handle_stats(self):
        """Handle stats command"""
        print("📊 Overall Statistics:")
        print(f"   🎯 Total unique controls: {len(self.variance_data)}")
        print(f"   🏢 Companies analyzed: {len(self.companies)}")
        print(f"   📈 Companies: {', '.join(sorted(self.companies))}")
    
    def handle_export(self, control_id: str, output_file: str = None):
        """Handle export command"""
        success = self.export_control_data(control_id, output_file)
        
        if success:
            filename = output_file or f"{control_id.replace(' ', '_').replace('.', '_')}_analysis.json"
            print(f"✅ Exported {control_id} data to: {filename}")
        else:
            print(f"❌ Failed to export data for: {control_id}")

def main():
    """Main CLI entry point"""
    cli = ControlQueryCLI()
    
    # Check if we have arguments for direct query
    if len(sys.argv) > 1:
        # Handle direct command execution
        command = ' '.join(sys.argv[1:])
        print(f"Executing: {command}")
        # TODO: Implement direct command execution
    else:
        # Run interactive mode
        cli.run_interactive()

if __name__ == "__main__":
    main()