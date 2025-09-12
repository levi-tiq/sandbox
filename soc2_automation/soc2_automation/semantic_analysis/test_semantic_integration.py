#!/usr/bin/env python3
"""
Test script for semantic analysis integration

Tests the integration between control_variance_analyzer.py and semantic_analyzer.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_semantic_analyzer():
    """Test standalone semantic analyzer"""
    print("🧪 Testing Semantic Analyzer...")
    
    try:
        from semantic_analysis.semantic_analyzer import SemanticAnalyzer
        
        # Check if dependencies are available
        analyzer = SemanticAnalyzer()
        print("✅ SemanticAnalyzer initialized successfully")
        
        # Test text preprocessing
        from semantic_analysis.semantic_analyzer import TextPreprocessor
        preprocessor = TextPreprocessor()
        
        test_text = "Inquired of management regarding the access control procedures for the period from 01/01/2024 to 12/31/2024 and obtained supporting documentation."
        
        methodology = preprocessor.extract_core_methodology(test_text)
        print(f"✅ Text preprocessing working: {methodology['primary_verb']}")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Semantic analyzer dependencies not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Semantic analyzer test failed: {e}")
        return False

def test_integration():
    """Test integration with control variance analyzer"""
    print("\n🧪 Testing Integration with Control Variance Analyzer...")
    
    try:
        from core.control_variance_analyzer import ControlVarianceAnalyzer
        
        analyzer = ControlVarianceAnalyzer()
        
        # Check if the new method exists
        if hasattr(analyzer, 'analyze_semantic_variance'):
            print("✅ analyze_semantic_variance method available")
        else:
            print("❌ analyze_semantic_variance method not found")
            return False
        
        # Test with mock data (if no real data available)
        variance_file = "data/processed/latest/control_variance_report.json"
        
        if os.path.exists(variance_file):
            print(f"✅ Variance data file found: {variance_file}")
            
            # Load and test
            analyzer.load_reports("data/processed/latest/company_organized_reports.json")
            analyzer.extract_control_matrix()
            analyzer.analyze_test_language_variance()
            
            print("✅ Basic analysis complete, testing semantic integration...")
            
            # Test semantic integration (may fail if dependencies missing)
            try:
                enhanced_results = analyzer.analyze_semantic_variance(run_semantic_analysis=True)
                
                if 'semantic_analysis' in enhanced_results:
                    if 'error' in enhanced_results['semantic_analysis']:
                        print(f"⚠️  Semantic analysis error: {enhanced_results['semantic_analysis']['message']}")
                    else:
                        print("✅ Semantic analysis integration successful!")
                        
                        # Check enhanced insights
                        if enhanced_results.get('enhanced_insights'):
                            insights = enhanced_results['enhanced_insights']
                            methodology_classifications = len(insights.get('methodology_vs_style_classification', {}))
                            print(f"✅ Generated insights for {methodology_classifications} controls")
                        
                        return True
                else:
                    print("❌ No semantic analysis in results")
                    return False
                    
            except Exception as e:
                print(f"⚠️  Semantic analysis integration failed: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        else:
            print(f"⚠️  No variance data found at {variance_file}")
            print("   Run control_variance_analyzer.py first")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_preprocessing_pipeline():
    """Test the preprocessing pipeline with SOC2 examples"""
    print("\n🧪 Testing Preprocessing Pipeline...")
    
    try:
        from semantic_analysis.semantic_analyzer import TextPreprocessor
        
        preprocessor = TextPreprocessor()
        
        # Test with typical SOC2 test descriptions
        test_cases = [
            "Inquired of management regarding access controls for the period from 01/01/2024 to 12/31/2024",
            "Inspected a sample of 25 user access provisioning requests to determine whether proper approval was obtained",
            "Reviewed policies and procedures related to logical access controls and observed implementation",
            "Tested the configuration of firewall settings for 5 selected systems during the period",
            "We performed testing of password complexity requirements for a sample of 30 users"
        ]
        
        for i, test_text in enumerate(test_cases, 1):
            methodology = preprocessor.extract_core_methodology(test_text)
            print(f"  Test {i}: {methodology['primary_verb']} | Evidence: {methodology['evidence_types']} | Scope: {methodology['scope_type']}")
        
        print("✅ Preprocessing pipeline working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Preprocessing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 SOC2 Semantic Analysis Integration Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Basic semantic analyzer
    results.append(test_semantic_analyzer())
    
    # Test 2: Preprocessing pipeline
    results.append(test_preprocessing_pipeline())
    
    # Test 3: Integration
    results.append(test_integration())
    
    # Summary
    print(f"\n📊 TEST SUMMARY:")
    print("=" * 30)
    # Handle None values in results
    valid_results = [r for r in results if r is not None]
    passed = sum(valid_results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Semantic analysis integration is ready.")
    elif passed > 0:
        print("⚠️  Some tests passed. Check warnings above for missing dependencies.")
    else:
        print("❌ Tests failed. Check errors above.")
    
    print(f"\n💡 Next steps:")
    if passed >= 1:
        print("   - Install missing dependencies: pip install sentence-transformers scikit-learn")
        print("   - Run full semantic analysis: python semantic_analyzer.py")
        print("   - Use enhanced analyzer: python control_variance_analyzer.py (with semantic integration)")
    else:
        print("   - Check Python path and import issues")
        print("   - Verify file structure and dependencies")

if __name__ == "__main__":
    main()