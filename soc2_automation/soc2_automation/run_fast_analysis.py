#!/usr/bin/env python3
"""
SOC2 Fast Analysis Runner

Optimized workflow that includes lightweight semantic analysis.
"""

import os
import sys
from datetime import datetime

def run_extraction():
    """Run report extraction"""
    print("🔍 Step 1: Extracting reports from PDFs...")
    os.system("python3 core/enhanced_batch_extractor.py")

def run_variance_analysis():
    """Run control variance analysis"""
    print("\n📊 Step 2: Analyzing control variance...")
    
    # Find latest extraction
    latest_extraction = None
    runs_dir = "data/processed/runs"
    if os.path.exists(runs_dir):
        runs = [d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))]
        if runs:
            latest_extraction = sorted(runs)[-1]
            reports_file = f"data/processed/runs/{latest_extraction}/company_organized_reports.json"
        else:
            reports_file = "data/processed/latest/company_organized_reports.json"
    else:
        reports_file = "data/processed/latest/company_organized_reports.json"
    
    if os.path.exists(reports_file):
        os.system(f"python3 core/control_variance_analyzer.py {reports_file}")
    else:
        print("❌ No reports file found. Run extraction first.")

def run_fast_semantic_analysis():
    """Run fast semantic analysis"""
    print("\n🧠 Step 3: Running fast semantic analysis...")
    os.system("python3 semantic_analysis/fast_semantic_analyzer.py")

def run_fast_classification():
    """Run fast difference classification"""
    print("\n🔧 Step 4: Running fast difference classification...")
    os.system("python3 semantic_analysis/fast_difference_classifier.py")

def run_visualizations():
    """Generate all visualizations"""
    print("\n🎨 Step 5: Generating visualizations...")
    os.system("python3 visualizations/control_variance_visualizer.py")

def show_results():
    """Show where to find results"""
    print("\n" + "="*60)
    print("✅ FAST ANALYSIS COMPLETE!")
    print("="*60)
    
    # Find latest output directory
    outputs_dir = "data/outputs"
    if os.path.exists(outputs_dir):
        runs = [d for d in os.listdir(outputs_dir) if os.path.isdir(os.path.join(outputs_dir, d))]
        if runs:
            latest_run = sorted(runs)[-1]
            print(f"📁 Results location: data/outputs/{latest_run}/")
            print(f"")
            print(f"🎯 Key files:")
            print(f"   📊 Dashboard: visuals/soc2_dashboard.png")
            print(f"   🌟 Interactive: visuals/interactive_control_analysis.html")
            print(f"   🧠 Semantic analysis: json/semantic_analysis_results.json")
            print(f"   🔧 Automation insights: json/difference_classification_results.json")
            print(f"   📈 Gap analysis: visuals/gap_analysis_dashboard.png")
            print(f"")
            print(f"💡 Open the dashboard files to view your analysis!")

def main():
    """Run the complete fast analysis pipeline"""
    print("🚀 SOC2 Fast Analysis Pipeline")
    print("=" * 40)
    print("This optimized workflow includes semantic analysis with performance optimizations.")
    print("")
    
    try:
        # Step 1: Extract reports
        run_extraction()
        
        # Step 2: Analyze variance
        run_variance_analysis()
        
        # Step 3: Fast semantic analysis
        run_fast_semantic_analysis()
        
        # Step 4: Fast classification
        run_fast_classification()
        
        # Step 5: Generate visualizations
        run_visualizations()
        
        # Show results
        show_results()
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error in analysis pipeline: {e}")
        print("💡 You can run individual steps manually if needed")

if __name__ == "__main__":
    main()