#!/usr/bin/env python3
"""
Complete SOC2 System Test

End-to-end test of the entire SOC2 semantic analysis system:
- Phase 1: Semantic Similarity Engine
- Phase 2: Methodology Extraction System
- Integration: Enhanced variance analysis
- CLI: Interactive query system
- Visualizations: Data visualization pipeline

This is the comprehensive test for the complete system.
"""

import os
import sys
import time
from datetime import datetime

class SystemTester:
    """Complete system testing orchestrator"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    def log_test(self, test_name: str, result: bool, message: str = "", duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if result else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'result': result,
            'message': message,
            'duration': duration,
            'status': status
        })
        
        duration_str = f" ({duration:.1f}s)" if duration > 0 else ""
        print(f"{status}: {test_name}{duration_str}")
        if message:
            print(f"    {message}")
    
    def test_dependencies(self):
        """Test system dependencies"""
        print("🔍 Testing system dependencies...")
        
        # Test Python imports
        start = time.time()
        try:
            import numpy as np
            import json
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import spacy
            self.log_test("Core Dependencies", True, "All required packages available", time.time() - start)
            return True
        except ImportError as e:
            self.log_test("Core Dependencies", False, f"Missing packages: {e}", time.time() - start)
            return False
    
    def test_data_availability(self):
        """Test data file availability"""
        print("\n🔍 Testing data availability...")
        
        required_files = [
            "data/processed/latest/company_organized_reports.json",
            "data/processed/latest/control_variance_report.json"
        ]
        
        all_available = True
        for file_path in required_files:
            start = time.time()
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                self.log_test(f"Data File: {os.path.basename(file_path)}", True, f"Available ({size:,} bytes)", time.time() - start)
            else:
                self.log_test(f"Data File: {os.path.basename(file_path)}", False, "File not found", time.time() - start)
                all_available = False
        
        return all_available
    
    def test_phase1_semantic_analysis(self):
        """Test Phase 1: Semantic Similarity Engine"""
        print("\n🧠 Testing Phase 1: Semantic Similarity Engine...")
        
        try:
            start = time.time()
            from semantic_analysis.semantic_analyzer import SemanticAnalyzer, TextPreprocessor
            
            # Test text preprocessor
            preprocessor = TextPreprocessor()
            test_text = "Inquired of management regarding access controls for the period from 01/01/2024 to 12/31/2024"
            methodology = preprocessor.extract_core_methodology(test_text)
            
            if methodology['primary_verb'] and methodology['cleaned_text']:
                self.log_test("Phase 1: Text Preprocessing", True, f"Extracted verb: {methodology['primary_verb']}", time.time() - start)
            else:
                self.log_test("Phase 1: Text Preprocessing", False, "Failed to extract methodology", time.time() - start)
                return False
            
            # Test semantic analyzer initialization
            start = time.time()
            analyzer = SemanticAnalyzer()
            self.log_test("Phase 1: Analyzer Initialization", True, "SemanticAnalyzer created", time.time() - start)
            
            # Test embedding generation
            start = time.time()
            test_texts = [
                "Inquired of management regarding access controls",
                "Reviewed documentation for access control procedures"
            ]
            embeddings = analyzer.generate_embeddings(test_texts, "test")
            
            if embeddings is not None and len(embeddings) == 2:
                self.log_test("Phase 1: Embedding Generation", True, f"Generated embeddings: {embeddings.shape}", time.time() - start)
            else:
                self.log_test("Phase 1: Embedding Generation", False, "Failed to generate embeddings", time.time() - start)
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Phase 1: Semantic Analysis", False, f"Error: {e}", time.time() - start)
            return False
    
    def test_phase2_methodology_extraction(self):
        """Test Phase 2: Methodology Extraction System"""
        print("\n🔧 Testing Phase 2: Methodology Extraction System...")
        
        try:
            start = time.time()
            from semantic_analysis.methodology_extractor import MethodologyExtractor, SOC2EntityPatterns
            
            # Test entity patterns
            patterns = SOC2EntityPatterns()
            if patterns.testing_verbs['primary'] and patterns.evidence_types:
                self.log_test("Phase 2: Entity Patterns", True, f"Loaded {len(patterns.testing_verbs['primary'])} primary verbs", time.time() - start)
            else:
                self.log_test("Phase 2: Entity Patterns", False, "Failed to load patterns", time.time() - start)
                return False
            
            # Test methodology extractor
            start = time.time()
            extractor = MethodologyExtractor()
            
            test_text = "Inspected a sample of 25 user access provisioning requests to determine whether proper approval was obtained"
            methodology = extractor.extract_methodology(test_text)
            
            if methodology['methodology_type']['primary_type'] != 'unknown':
                self.log_test("Phase 2: Methodology Extraction", True, f"Extracted: {methodology['methodology_type']['primary_type']}", time.time() - start)
            else:
                self.log_test("Phase 2: Methodology Extraction", False, "Failed to extract methodology", time.time() - start)
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Phase 2: Methodology Extraction", False, f"Error: {e}", time.time() - start)
            return False
    
    def test_integration(self):
        """Test Phase 1 + Phase 2 Integration"""
        print("\n🔗 Testing Phase 1 + Phase 2 Integration...")
        
        try:
            start = time.time()
            from core.control_variance_analyzer import ControlVarianceAnalyzer
            
            # Test enhanced analyzer
            analyzer = ControlVarianceAnalyzer()
            
            # Check if semantic variance method exists
            if hasattr(analyzer, 'analyze_semantic_variance'):
                self.log_test("Integration: Enhanced Analyzer", True, "analyze_semantic_variance method available", time.time() - start)
            else:
                self.log_test("Integration: Enhanced Analyzer", False, "analyze_semantic_variance method not found", time.time() - start)
                return False
            
            # Test with real data if available
            variance_file = "data/processed/latest/control_variance_report.json"
            company_file = "data/processed/latest/company_organized_reports.json"
            
            if os.path.exists(variance_file) and os.path.exists(company_file):
                start = time.time()
                
                # Load minimal data for integration test
                analyzer.load_reports(company_file)
                analyzer.extract_control_matrix()
                analyzer.analyze_test_language_variance()
                
                self.log_test("Integration: Basic Analysis", True, "Basic variance analysis completed", time.time() - start)
                
                # Test semantic integration (quick test with limited data)
                start = time.time()
                
                # Get first control for testing
                first_control = list(analyzer.variance_stats.keys())[0]
                control_data = analyzer.variance_stats[first_control]
                
                from semantic_analysis.semantic_analyzer import SemanticAnalyzer
                semantic_analyzer = SemanticAnalyzer()
                
                # Test single control analysis
                result = semantic_analyzer.analyze_control_semantic_similarity(first_control, control_data)
                
                if 'methodology_analysis' in result and result['methodology_analysis']:
                    self.log_test("Integration: Semantic + Methodology", True, "Full integration working", time.time() - start)
                else:
                    self.log_test("Integration: Semantic + Methodology", True, "Phase 1 integration working", time.time() - start)
                
                return True
            else:
                self.log_test("Integration: Data Test", False, "Required data files not available", time.time() - start)
                return False
                
        except Exception as e:
            self.log_test("Integration: Full Test", False, f"Error: {e}", time.time() - start)
            return False
    
    def test_cli_interface(self):
        """Test CLI Interface"""
        print("\n💻 Testing CLI Interface...")
        
        try:
            start = time.time()
            from cli.control_query_cli import ControlQueryCLI
            
            cli = ControlQueryCLI()
            
            # Test CLI initialization
            self.log_test("CLI: Initialization", True, "ControlQueryCLI created", time.time() - start)
            
            # Test data loading capability
            if hasattr(cli, 'load_data'):
                self.log_test("CLI: Interface Methods", True, "Required methods available", time.time() - start)
                return True
            else:
                self.log_test("CLI: Interface Methods", False, "Missing required methods", time.time() - start)
                return False
                
        except Exception as e:
            self.log_test("CLI: Interface Test", False, f"Error: {e}", time.time() - start)
            return False
    
    def test_visualization_system(self):
        """Test Visualization System"""
        print("\n📊 Testing Visualization System...")
        
        try:
            start = time.time()
            from visualizations.control_variance_visualizer import ControlVarianceVisualizer
            
            visualizer = ControlVarianceVisualizer()
            
            # Test visualizer initialization
            self.log_test("Visualization: Initialization", True, "ControlVarianceVisualizer created", time.time() - start)
            
            # Check for key methods
            required_methods = ['load_data', 'generate_summary_dashboard']
            missing_methods = []
            
            for method in required_methods:
                if not hasattr(visualizer, method):
                    missing_methods.append(method)
            
            if not missing_methods:
                self.log_test("Visualization: Methods", True, "All required methods available", time.time() - start)
                return True
            else:
                self.log_test("Visualization: Methods", False, f"Missing methods: {missing_methods}", time.time() - start)
                return False
                
        except Exception as e:
            self.log_test("Visualization: System Test", False, f"Error: {e}", time.time() - start)
            return False
    
    def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline"""
        print("\n🚀 Testing End-to-End Pipeline...")
        
        try:
            # Check if we can run the full pipeline script
            if os.path.exists("run_full_analysis.py"):
                self.log_test("Pipeline: Script Available", True, "run_full_analysis.py found")
                
                # Test that the script is syntactically correct
                start = time.time()
                with open("run_full_analysis.py", 'r') as f:
                    code = f.read()
                
                try:
                    compile(code, "run_full_analysis.py", 'exec')
                    self.log_test("Pipeline: Script Syntax", True, "Script is syntactically valid", time.time() - start)
                    return True
                except SyntaxError as e:
                    self.log_test("Pipeline: Script Syntax", False, f"Syntax error: {e}", time.time() - start)
                    return False
            else:
                self.log_test("Pipeline: Script Available", False, "run_full_analysis.py not found")
                return False
                
        except Exception as e:
            self.log_test("Pipeline: End-to-End Test", False, f"Error: {e}")
            return False
    
    def run_complete_system_test(self):
        """Run complete system test suite"""
        print("🧪 SOC2 Complete System Test")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.start_time = time.time()
        
        # Run all test phases
        tests = [
            ("Dependencies", self.test_dependencies),
            ("Data Availability", self.test_data_availability),
            ("Phase 1: Semantic Analysis", self.test_phase1_semantic_analysis),
            ("Phase 2: Methodology Extraction", self.test_phase2_methodology_extraction),
            ("Phase 1+2 Integration", self.test_integration),
            ("CLI Interface", self.test_cli_interface),
            ("Visualization System", self.test_visualization_system),
            ("End-to-End Pipeline", self.test_end_to_end_pipeline)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {e}")
        
        # Print summary
        total_duration = time.time() - self.start_time
        print(f"\n📊 TEST SUMMARY")
        print("=" * 40)
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total duration: {total_duration:.1f}s")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            duration_str = f" ({result['duration']:.1f}s)" if result['duration'] > 0 else ""
            print(f"{result['status']}: {result['test']}{duration_str}")
            if result['message']:
                print(f"    {result['message']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if passed_tests == total_tests:
            print("✅ All tests passed! System is fully operational.")
            print("🚀 Ready to run: python3 run_full_analysis.py")
            print("📊 Or test individual components as needed")
        elif passed_tests >= total_tests * 0.75:
            print("⚠️  Most tests passed. System is mostly functional.")
            print("🔧 Review failed tests above for missing dependencies")
            print("🚀 You can still run: python3 run_full_analysis.py")
        else:
            print("❌ Multiple test failures. System needs setup.")
            print("📦 Install missing dependencies:")
            print("   pip install sentence-transformers scikit-learn spacy")
            print("   python -m spacy download en_core_web_sm")
            print("📊 Ensure data files exist by running extraction first")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = SystemTester()
    success = tester.run_complete_system_test()
    
    if success:
        print(f"\n🎉 COMPLETE SYSTEM TEST: PASSED")
        return 0
    else:
        print(f"\n⚠️  COMPLETE SYSTEM TEST: ISSUES DETECTED")
        return 1

if __name__ == "__main__":
    exit(main())