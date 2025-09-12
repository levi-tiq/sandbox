#!/usr/bin/env python3
"""
Fast SOC2 Difference Classifier

Lightweight version that creates basic difference classifications for automation insights.
"""

import json
import os
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from collections import Counter
import sys
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager
except ImportError:
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager

class FastDifferenceClassifier:
    """Lightweight difference classifier for automation insights"""
    
    def __init__(self):
        self.output_manager = get_output_manager()
        self.semantic_data = None
        self.variance_data = None
    
    def load_data(self):
        """Load semantic analysis and variance data"""
        # Load semantic data
        latest_run = self.output_manager.get_latest_run()
        if latest_run:
            semantic_path = os.path.join(latest_run, "json", "semantic_analysis_results.json")
            variance_path = os.path.join(latest_run, "json", "control_variance_report.json")
        else:
            semantic_path = "data/processed/latest/semantic_analysis_results.json"
            variance_path = "data/processed/latest/control_variance_report.json"
        
        try:
            with open(semantic_path, 'r', encoding='utf-8') as f:
                self.semantic_data = json.load(f)
            print(f"✅ Loaded semantic analysis data")
        except Exception as e:
            print(f"❌ Could not load semantic data: {e}")
            return False
        
        try:
            with open(variance_path, 'r', encoding='utf-8') as f:
                self.variance_data = json.load(f)
            print(f"✅ Loaded variance data")
        except Exception as e:
            print(f"❌ Could not load variance data: {e}")
            return False
        
        return True
    
    def classify_control_differences(self, control_key: str) -> Dict[str, Any]:
        """Classify differences for a single control"""
        # Get semantic data
        semantic_result = self.semantic_data.get('controls_analysis', {}).get(control_key, {})
        semantic_similarity = semantic_result.get('average_similarity', 0.0)
        
        # Get variance data
        variance_result = self.variance_data.get('variance_analysis', {}).get(control_key, {})
        variance_metrics = variance_result.get('variance_metrics', {})
        
        # Calculate lexical variance (text-based)
        unique_tests = variance_metrics.get('unique_test_texts', 1)
        total_tests = variance_metrics.get('total_test_instances', 1)
        lexical_variance = unique_tests / max(total_tests, 1)
        
        # Simple classification logic
        # High semantic similarity + high lexical variance = Style differences
        # Low semantic similarity + high lexical variance = Methodology differences
        
        style_percentage = 0
        methodology_percentage = 0
        
        if semantic_similarity >= 0.7:
            # High semantic similarity - mostly style differences
            style_percentage = int(lexical_variance * 100)
            methodology_percentage = max(0, 100 - style_percentage)
        elif semantic_similarity >= 0.4:
            # Medium semantic similarity - mixed
            style_percentage = int(lexical_variance * 60)
            methodology_percentage = int(lexical_variance * 40) + (100 - int(lexical_variance * 100))
        else:
            # Low semantic similarity - mostly methodology differences
            methodology_percentage = int(lexical_variance * 100)
            style_percentage = max(0, 100 - methodology_percentage)
        
        # Determine automation feasibility
        if style_percentage >= 70:
            automation_feasibility = 'ready'
        elif style_percentage >= 40:
            automation_feasibility = 'needs_standardization'
        else:
            automation_feasibility = 'too_diverse'
        
        # Determine standardization opportunity
        if semantic_similarity >= 0.6 and lexical_variance <= 0.5:
            standardization_opportunity = 'high'
        elif semantic_similarity >= 0.4:
            standardization_opportunity = 'medium'
        else:
            standardization_opportunity = 'low'
        
        return {
            'control_key': control_key,
            'semantic_similarity': semantic_similarity,
            'lexical_variance': lexical_variance,
            'style_percentage': style_percentage,
            'methodology_percentage': methodology_percentage,
            'automation_feasibility': automation_feasibility,
            'standardization_opportunity': standardization_opportunity
        }
    
    def classify_all_differences(self) -> Dict[str, Any]:
        """Classify differences for all controls"""
        if not self.semantic_data or not self.variance_data:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print("🔧 Starting fast difference classification...")
        
        controls_analysis = self.semantic_data.get('controls_analysis', {})
        control_profiles = {}
        
        for control_key in controls_analysis.keys():
            try:
                profile = self.classify_control_differences(control_key)
                control_profiles[control_key] = profile
            except Exception as e:
                print(f"❌ Error classifying {control_key}: {e}")
                continue
        
        # Generate summary insights
        automation_counts = Counter()
        standardization_counts = Counter()
        style_percentages = []
        methodology_percentages = []
        
        for profile in control_profiles.values():
            automation_counts[profile['automation_feasibility']] += 1
            standardization_counts[profile['standardization_opportunity']] += 1
            style_percentages.append(profile['style_percentage'])
            methodology_percentages.append(profile['methodology_percentage'])
        
        # Create automation recommendations
        immediate_candidates = {
            'count': automation_counts.get('ready', 0),
            'description': 'Controls ready for immediate template automation'
        }
        
        standardization_candidates = {
            'count': automation_counts.get('needs_standardization', 0),
            'description': 'Controls needing standardization before automation'
        }
        
        manual_candidates = {
            'count': automation_counts.get('too_diverse', 0),
            'description': 'Controls requiring manual approach'
        }
        
        # Overall insights
        total_controls = len(control_profiles)
        avg_style = np.mean(style_percentages) if style_percentages else 0
        avg_methodology = np.mean(methodology_percentages) if methodology_percentages else 0
        
        results = {
            'classification_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_controls_analyzed': total_controls,
                'average_style_percentage': float(avg_style),
                'average_methodology_percentage': float(avg_methodology),
                'key_finding': f"Average style differences: {avg_style:.1f}%, methodology differences: {avg_methodology:.1f}%"
            },
            'control_profiles': control_profiles,
            'overall_insights': {
                'total_controls_analyzed': total_controls,
                'average_style_percentage': float(avg_style),
                'average_methodology_percentage': float(avg_methodology),
                'key_finding': f"Style vs methodology split suggests {immediate_candidates['count']} controls ready for automation"
            },
            'automation_recommendations': {
                'immediate_automation_candidates': immediate_candidates,
                'standardization_first_candidates': standardization_candidates,
                'manual_approach_recommended': manual_candidates,
                'automation_strategy': {
                    'phase1': f"Automate {immediate_candidates['count']} ready controls",
                    'phase2': f"Standardize {standardization_candidates['count']} controls then automate",
                    'phase3': f"Keep {manual_candidates['count']} controls manual",
                    'overall_automation_potential': f"{(immediate_candidates['count'] / max(total_controls, 1)) * 100:.1f}% immediately, {((immediate_candidates['count'] + standardization_candidates['count']) / max(total_controls, 1)) * 100:.1f}% after standardization"
                }
            },
            'standardization_opportunities': {
                'summary': {
                    'high_opportunity_count': standardization_counts.get('high', 0),
                    'automation_ready_count': automation_counts.get('ready', 0),
                    'standardization_needed_count': standardization_counts.get('medium', 0) + standardization_counts.get('low', 0)
                }
            }
        }
        
        # Save results
        self.save_results(results)
        
        print(f"✅ Fast difference classification complete!")
        print(f"📊 Analyzed {total_controls} controls")
        print(f"🚀 Ready for automation: {immediate_candidates['count']} controls")
        print(f"🔧 Need standardization: {standardization_candidates['count']} controls")
        print(f"✋ Keep manual: {manual_candidates['count']} controls")
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """Save classification results"""
        output_file = self.output_manager.get_output_path('json', 'difference_classification_results.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Classification results saved to: {output_file}")

def main():
    """Main execution function"""
    classifier = FastDifferenceClassifier()
    
    try:
        if not classifier.load_data():
            print("❌ Could not load required data files")
            return
        
        results = classifier.classify_all_differences()
        
        print(f"\n🎯 Classification Summary:")
        automation_recs = results.get('automation_recommendations', {})
        immediate = automation_recs.get('immediate_automation_candidates', {}).get('count', 0)
        needs_std = automation_recs.get('standardization_first_candidates', {}).get('count', 0)
        manual = automation_recs.get('manual_approach_recommended', {}).get('count', 0)
        
        print(f"   🚀 Ready for automation: {immediate} controls")
        print(f"   🔧 Need standardization first: {needs_std} controls")
        print(f"   ✋ Keep manual: {manual} controls")
        
        strategy = automation_recs.get('automation_strategy', {})
        print(f"   📈 Automation potential: {strategy.get('overall_automation_potential', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error running classification: {e}")

if __name__ == "__main__":
    main()