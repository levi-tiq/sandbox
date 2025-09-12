#!/usr/bin/env python3
"""
Full SOC2 Analysis Runner

Runs the complete analysis pipeline:
1. Control variance analysis (if needed)
2. Semantic analysis
3. Enhanced integration
"""

import os
import sys

def ensure_variance_data():
    """Ensure we have variance data available"""
    variance_file = "data/processed/latest/control_variance_report.json"
    company_reports = "data/processed/latest/company_organized_reports.json"
    
    if not os.path.exists(variance_file) or not os.path.exists(company_reports):
        print("📊 Variance data not found, generating...")
        
        # Import and run control variance analyzer
        from core.control_variance_analyzer import ControlVarianceAnalyzer
        
        analyzer = ControlVarianceAnalyzer()
        
        # Check if company reports exist
        if not os.path.exists(company_reports):
            print("❌ Company reports not found. Please run:")
            print("   python core/enhanced_batch_extractor.py")
            return False
        
        # Load and analyze
        analyzer.load_reports(company_reports)
        analyzer.extract_control_matrix()
        analyzer.analyze_test_language_variance()
        analyzer.generate_variance_report()
        
        print("✅ Variance data generated")
    else:
        print("✅ Variance data found")
    
    return True

def run_semantic_analysis():
    """Run semantic analysis"""
    print("\n🧠 Running semantic analysis...")
    
    from semantic_analysis.semantic_analyzer import SemanticAnalyzer
    
    analyzer = SemanticAnalyzer()
    analyzer.load_variance_data()
    results = analyzer.analyze_semantic_similarity()
    output_file = analyzer.save_results()
    
    print(f"✅ Semantic analysis complete: {output_file}")
    return results

def run_enhanced_integration():
    """Run enhanced integration analysis"""
    print("\n🔗 Running enhanced integration analysis...")
    
    from core.control_variance_analyzer import ControlVarianceAnalyzer
    
    analyzer = ControlVarianceAnalyzer()
    analyzer.load_reports("data/processed/latest/company_organized_reports.json")
    analyzer.extract_control_matrix()
    
    # Run enhanced analysis with semantic integration
    enhanced_results = analyzer.analyze_semantic_variance(run_semantic_analysis=True)
    
    if 'error' not in enhanced_results.get('semantic_analysis', {}):
        print("✅ Enhanced integration complete")
        
        # Print summary
        semantic_analysis = enhanced_results.get('semantic_analysis', {})
        if semantic_analysis and 'global_summary' in semantic_analysis:
            global_summary = semantic_analysis['global_summary']
            print(f"\n📊 SUMMARY:")
            print(f"   Total comparisons: {global_summary['total_pairwise_comparisons']}")
            
            automation = global_summary.get('automation_candidates', {})
            print(f"   High similarity controls: {automation.get('high_similarity_controls', 0)}")
            print(f"   Medium similarity controls: {automation.get('medium_similarity_controls', 0)}")
            print(f"   Low similarity controls: {automation.get('low_similarity_controls', 0)}")
        
        return enhanced_results
    else:
        print(f"❌ Enhanced integration failed: {enhanced_results['semantic_analysis']['message']}")
        return None

def main():
    """Main execution"""
    print("🚀 SOC2 Full Analysis Pipeline")
    print("=" * 50)
    
    try:
        # Step 1: Ensure variance data
        if not ensure_variance_data():
            print("❌ Failed to generate variance data")
            return
        
        # Step 2: Run semantic analysis
        try:
            semantic_results = run_semantic_analysis()
        except Exception as e:
            print(f"❌ Semantic analysis failed: {e}")
            print("   This might be due to missing dependencies.")
            print("   Try: pip install sentence-transformers scikit-learn")
            return
        
        # Step 3: Run enhanced integration
        try:
            enhanced_results = run_enhanced_integration()
            if enhanced_results:
                print("\n🎉 Full analysis pipeline complete!")
                print("\n💡 Next steps:")
                print("   - View results in data/processed/latest/semantic_analysis/")
                print("   - Use CLI: python cli/control_query_cli.py")
                print("   - Generate visualizations: python visualizations/control_variance_visualizer.py")
            
        except Exception as e:
            print(f"⚠️  Enhanced integration failed: {e}")
            print("   Basic semantic analysis was successful though.")
    
    except Exception as e:
        print(f"❌ Analysis pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()