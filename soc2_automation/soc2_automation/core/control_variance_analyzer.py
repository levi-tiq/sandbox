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
    analyzer.load_reports("data/processed/latest/company_organized_reports.json")
    variance_data = analyzer.analyze_variance()
"""

import json
import os
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import difflib
import re
from datetime import datetime
try:
    from .output_manager import get_output_manager
except ImportError:
    # For direct execution
    from output_manager import get_output_manager

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
    
    def generate_variance_report(self, output_file: str = None):
        """Generate comprehensive variance report"""
        print("📋 Generating variance report...")
        
        from datetime import datetime
        import os
        
        # Use output manager for consistent path generation
        if output_file is None:
            output_manager = get_output_manager()
            output_file = output_manager.get_output_path('json', 'control_variance_report.json')
        
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
    
    def analyze_semantic_variance(self, run_semantic_analysis: bool = True) -> Dict[str, Any]:
        """
        Enhanced variance analysis with semantic similarity
        Integrates with semantic_analyzer.py for deeper insights
        """
        print("🧠 Running enhanced variance analysis with semantic similarity...")
        
        # First ensure we have basic variance analysis
        if not self.variance_stats:
            print("📊 Running basic variance analysis first...")
            self.analyze_test_language_variance()
        
        enhanced_results = {
            'basic_variance': self.variance_stats,
            'semantic_analysis': None,
            'enhanced_insights': {}
        }
        
        if run_semantic_analysis:
            try:
                # Import semantic analyzer (dynamic import to handle missing dependencies)
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'semantic_analysis'))
                
                from semantic_analyzer import SemanticAnalyzer
                
                print("🤖 Initializing semantic analyzer...")
                semantic_analyzer = SemanticAnalyzer()
                
                # Create temporary variance report for semantic analysis
                temp_variance_data = {
                    'generation_timestamp': datetime.now().isoformat(),
                    'variance_analysis': self.variance_stats
                }
                
                # Load data into semantic analyzer
                semantic_analyzer.variance_data = temp_variance_data
                
                # Run semantic analysis
                semantic_results = semantic_analyzer.analyze_semantic_similarity()
                enhanced_results['semantic_analysis'] = semantic_results
                
                # Run methodology extraction (Phase 2)
                print("🔧 Running methodology extraction...")
                try:
                    from methodology_extractor import MethodologyExtractor
                    methodology_extractor = MethodologyExtractor()
                    methodology_results = methodology_extractor.analyze_methodology_patterns(temp_variance_data)
                    enhanced_results['methodology_analysis'] = methodology_results
                    print("✅ Methodology extraction complete")
                except Exception as e:
                    print(f"⚠️  Methodology extraction failed: {e}")
                    enhanced_results['methodology_analysis'] = {'error': str(e)}
                
                # Run difference classification (Phase 3)
                print("🔍 Running difference classification...")
                try:
                    from difference_classifier import DifferenceClassifier
                    classifier = DifferenceClassifier()
                    
                    # Only run if we have both semantic and methodology results
                    if ('error' not in enhanced_results['semantic_analysis'] and 
                        'error' not in enhanced_results.get('methodology_analysis', {})):
                        classification_results = classifier.classify_differences(
                            enhanced_results['semantic_analysis'],
                            enhanced_results['methodology_analysis']
                        )
                        enhanced_results['difference_classification'] = classification_results
                        print("✅ Difference classification complete")
                    else:
                        enhanced_results['difference_classification'] = {'error': 'prerequisite_analysis_failed'}
                except Exception as e:
                    print(f"⚠️  Difference classification failed: {e}")
                    enhanced_results['difference_classification'] = {'error': str(e)}
                
                # Generate enhanced insights combining all analyses
                enhanced_results['enhanced_insights'] = self._generate_enhanced_insights(
                    self.variance_stats, 
                    semantic_results,
                    enhanced_results.get('methodology_analysis', {}),
                    enhanced_results.get('difference_classification', {})
                )
                
                print("✅ Semantic analysis integration complete")
                
            except ImportError as e:
                print(f"⚠️  Semantic analysis not available: {e}")
                print("   Install dependencies: pip install sentence-transformers scikit-learn")
                enhanced_results['semantic_analysis'] = {
                    'error': 'dependencies_not_available',
                    'message': str(e)
                }
            except Exception as e:
                print(f"❌ Semantic analysis failed: {e}")
                enhanced_results['semantic_analysis'] = {
                    'error': 'analysis_failed', 
                    'message': str(e)
                }
        
        return enhanced_results
    
    def _generate_enhanced_insights(self, variance_data: Dict[str, Any], semantic_results: Dict[str, Any], 
                                   methodology_results: Dict[str, Any] = None, 
                                   classification_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate insights combining lexical, semantic, methodology, and classification analyses"""
        
        insights = {
            'methodology_vs_style_classification': {},
            'automation_recommendations': {},
            'standardization_opportunities': {},
            'control_complexity_analysis': {},
            'phase3_difference_analysis': {}
        }
        
        # Handle Phase 3 classification results
        if classification_results and 'error' not in classification_results:
            print("📊 Incorporating Phase 3 difference classification results...")
            
            # Extract key insights from Phase 3
            overall_insights = classification_results.get('overall_insights', {})
            automation_recs = classification_results.get('automation_recommendations', {})
            standardization_ops = classification_results.get('standardization_opportunities', {})
            
            insights['phase3_difference_analysis'] = {
                'total_controls_analyzed': overall_insights.get('total_controls_analyzed', 0),
                'average_style_percentage': overall_insights.get('average_style_percentage', 0),
                'average_methodology_percentage': overall_insights.get('average_methodology_percentage', 0),
                'key_finding': overall_insights.get('key_finding', ''),
                'automation_ready_count': automation_recs.get('immediate_automation_candidates', {}).get('count', 0),
                'standardization_needed_count': automation_recs.get('standardization_first_candidates', {}).get('count', 0),
                'manual_approach_count': automation_recs.get('manual_approach_recommended', {}).get('count', 0)
            }
            
            # Update automation recommendations with Phase 3 insights
            insights['automation_recommendations']['immediate_candidates'] = automation_recs.get('immediate_automation_candidates', {}).get('controls', [])
            insights['automation_recommendations']['needs_standardization'] = automation_recs.get('standardization_first_candidates', {}).get('controls', [])
            insights['automation_recommendations']['strategy'] = automation_recs.get('automation_strategy', {})
            
            # Update standardization opportunities with Phase 3 insights  
            insights['standardization_opportunities']['high_opportunity'] = standardization_ops.get('high_standardization_opportunity', [])
            insights['standardization_opportunities']['medium_opportunity'] = standardization_ops.get('medium_standardization_opportunity', [])
            insights['standardization_opportunities']['summary'] = standardization_ops.get('summary', {})
        
        # Legacy semantic analysis (if no Phase 3 results)
        if not semantic_results or 'controls_analysis' not in semantic_results:
            return insights
        
        controls_analysis = semantic_results['controls_analysis']
        
        # Analyze each control for methodology vs style differences (legacy approach)
        for control_key, control_data in variance_data.items():
            semantic_data = controls_analysis.get(control_key, {})
            
            if 'error' in semantic_data or 'summary_stats' not in semantic_data:
                continue
            
            # Basic variance metrics
            variance_metrics = control_data.get('variance_metrics', {})
            unique_tests = variance_metrics.get('unique_test_texts', 0)
            total_tests = variance_metrics.get('total_test_instances', 0)
            lexical_variance_ratio = unique_tests / total_tests if total_tests > 0 else 0
            
            # Semantic metrics
            semantic_stats = semantic_data.get('summary_stats', {})
            mean_semantic_similarity = semantic_stats.get('mean_similarity', 0)
            classification_dist = semantic_data.get('classification_distribution', {})
            
            # Classify control type
            control_classification = self._classify_control_differences(
                lexical_variance_ratio,
                mean_semantic_similarity, 
                classification_dist
            )
            
            insights['methodology_vs_style_classification'][control_key] = {
                'control_id': control_data.get('control_id', ''),
                'control_name': control_data.get('control_name', ''),
                'classification': control_classification,
                'lexical_variance_ratio': lexical_variance_ratio,
                'semantic_similarity_mean': mean_semantic_similarity,
                'companies_count': control_data.get('total_companies_with_control', 0)
            }
            
            # Generate automation recommendations
            automation_recommendation = self._generate_automation_recommendation(
                control_classification,
                mean_semantic_similarity,
                lexical_variance_ratio,
                control_data.get('total_companies_with_control', 0)
            )
            
            insights['automation_recommendations'][control_key] = automation_recommendation
        
        # Generate standardization opportunities
        insights['standardization_opportunities'] = self._identify_standardization_opportunities(
            insights['methodology_vs_style_classification']
        )
        
        # Control complexity analysis
        insights['control_complexity_analysis'] = self._analyze_control_complexity(
            insights['methodology_vs_style_classification']
        )
        
        return insights
    
    def _classify_control_differences(self, lexical_variance: float, semantic_similarity: float, classification_dist: Dict[str, int]) -> Dict[str, Any]:
        """Classify whether differences are primarily methodological or stylistic"""
        
        total_comparisons = sum(classification_dist.values()) if classification_dist else 0
        
        if total_comparisons == 0:
            return {'type': 'insufficient_data', 'confidence': 0}
        
        # Calculate percentages
        high_similarity_pct = classification_dist.get('high', 0) / total_comparisons
        medium_similarity_pct = classification_dist.get('medium', 0) / total_comparisons
        low_similarity_pct = classification_dist.get('low', 0) / total_comparisons
        
        # Classification logic
        if high_similarity_pct >= 0.7:
            # High semantic similarity but potentially high lexical variance = Style differences
            return {
                'type': 'primarily_stylistic',
                'confidence': high_similarity_pct,
                'description': 'Same methodology, different wording',
                'automation_potential': 'high'
            }
        elif low_similarity_pct >= 0.5:
            # Low semantic similarity = Methodology differences  
            return {
                'type': 'primarily_methodological',
                'confidence': low_similarity_pct,
                'description': 'Different testing approaches',
                'automation_potential': 'low'
            }
        else:
            # Mixed similarities = Hybrid differences
            return {
                'type': 'hybrid_differences',
                'confidence': medium_similarity_pct,
                'description': 'Mix of methodology and style differences',
                'automation_potential': 'medium'
            }
    
    def _generate_automation_recommendation(self, classification: Dict[str, Any], semantic_similarity: float, lexical_variance: float, companies_count: int) -> Dict[str, Any]:
        """Generate automation recommendation for a control"""
        
        if classification['type'] == 'insufficient_data':
            return {
                'priority': 'unknown',
                'recommendation': 'Need more data',
                'template_potential': False
            }
        
        # Base recommendation on classification and coverage
        if classification['type'] == 'primarily_stylistic' and companies_count >= 3:
            return {
                'priority': 'high',
                'recommendation': 'Excellent template candidate - semantic similarity indicates consistent methodology',
                'template_potential': True,
                'suggested_approach': 'Create unified template with style variations'
            }
        elif classification['type'] == 'hybrid_differences' and semantic_similarity >= 0.6:
            return {
                'priority': 'medium', 
                'recommendation': 'Template candidate with customization - some methodology differences exist',
                'template_potential': True,
                'suggested_approach': 'Create base template with methodology options'
            }
        else:
            return {
                'priority': 'low',
                'recommendation': 'Manual approach recommended - significant methodology differences',
                'template_potential': False,
                'suggested_approach': 'Company-specific customization required'
            }
    
    def _identify_standardization_opportunities(self, classifications: Dict[str, Any]) -> Dict[str, Any]:
        """Identify opportunities for standardization across controls"""
        
        stylistic_controls = []
        hybrid_controls = []
        methodological_controls = []
        
        for control_key, data in classifications.items():
            classification_type = data['classification']['type']
            
            if classification_type == 'primarily_stylistic':
                stylistic_controls.append({
                    'control_key': control_key,
                    'control_id': data['control_id'],
                    'companies_count': data['companies_count'],
                    'semantic_similarity': data['semantic_similarity_mean']
                })
            elif classification_type == 'hybrid_differences':
                hybrid_controls.append({
                    'control_key': control_key,
                    'control_id': data['control_id'], 
                    'companies_count': data['companies_count'],
                    'semantic_similarity': data['semantic_similarity_mean']
                })
            else:
                methodological_controls.append({
                    'control_key': control_key,
                    'control_id': data['control_id'],
                    'companies_count': data['companies_count'],
                    'semantic_similarity': data['semantic_similarity_mean']
                })
        
        # Sort by priority (company count and semantic similarity)
        stylistic_controls.sort(key=lambda x: (x['companies_count'], x['semantic_similarity']), reverse=True)
        hybrid_controls.sort(key=lambda x: (x['companies_count'], x['semantic_similarity']), reverse=True)
        
        return {
            'high_priority_templates': stylistic_controls[:10],
            'medium_priority_templates': hybrid_controls[:10],
            'manual_approach_controls': methodological_controls,
            'standardization_impact': {
                'template_ready_controls': len(stylistic_controls),
                'customizable_template_controls': len(hybrid_controls),
                'manual_controls': len(methodological_controls),
                'total_automation_potential': len(stylistic_controls) + len(hybrid_controls)
            }
        }
    
    def _analyze_control_complexity(self, classifications: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze control complexity for strategic planning"""
        
        complexity_metrics = {
            'simple': [],  # High semantic similarity, few companies
            'moderate': [], # Medium semantic similarity or medium company count
            'complex': []   # Low semantic similarity or high variance
        }
        
        for control_key, data in classifications.items():
            companies_count = data['companies_count']
            semantic_similarity = data['semantic_similarity_mean']
            lexical_variance = data['lexical_variance_ratio']
            
            # Complexity scoring
            if semantic_similarity >= 0.8 and companies_count <= 4:
                complexity_metrics['simple'].append(control_key)
            elif semantic_similarity <= 0.4 or lexical_variance >= 0.8 or companies_count >= 6:
                complexity_metrics['complex'].append(control_key)
            else:
                complexity_metrics['moderate'].append(control_key)
        
        return {
            'complexity_distribution': {
                'simple': len(complexity_metrics['simple']),
                'moderate': len(complexity_metrics['moderate']),
                'complex': len(complexity_metrics['complex'])
            },
            'complexity_details': complexity_metrics,
            'strategic_recommendations': {
                'focus_on_simple_first': f"Start with {len(complexity_metrics['simple'])} simple controls for quick wins",
                'moderate_controls_planning': f"Plan customization approach for {len(complexity_metrics['moderate'])} moderate controls",
                'complex_controls_research': f"Research methodology differences for {len(complexity_metrics['complex'])} complex controls"
            }
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
    # Create new output run
    output_manager = get_output_manager()
    run_path = output_manager.create_new_run("SOC2 Control Variance Analysis")
    
    analyzer = ControlVarianceAnalyzer()
    
    # Load reports (still from processed data)
    reports_file = "data/processed/latest/company_organized_reports.json"
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
    variance_report = analyzer.generate_variance_report()
    
    # Print summary
    analyzer.print_summary_stats()
    
    # Complete the run
    total_controls = len(variance_report.get('variance_analysis', {}))
    summary = f"Analyzed {total_controls} unique controls across {len(analyzer.all_companies)} companies"
    output_manager.complete_run(summary)
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 Output directory: {run_path}")
    print(f"📁 Detailed report saved to: {output_manager.get_output_path('json', 'control_variance_report.json')}")
    print(f"💡 Next: Use the CLI query tool to explore specific controls")

if __name__ == "__main__":
    main()