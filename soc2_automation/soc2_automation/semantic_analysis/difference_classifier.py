#!/usr/bin/env python3
"""
SOC2 Difference Classification Engine

Distinguishes between methodology differences vs. style differences in control testing.
This is Phase 3 of the semantic analysis enhancement roadmap.

Key Classifications:
- Style Differences: Same methodology, different wording/presentation
- Methodology Differences: Fundamentally different testing approaches

Usage:
    from semantic_analysis.difference_classifier import DifferenceClassifier
    classifier = DifferenceClassifier()
    results = classifier.classify_differences(semantic_data, methodology_data)
"""

import json
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
from datetime import datetime
import sys
import os
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager
except ImportError:
    # Fallback for different execution contexts
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DifferenceClassification:
    """Classification result for a pair of test descriptions"""
    text1: str
    text2: str
    semantic_similarity: float
    methodology_similarity: float
    difference_type: str  # 'style', 'minor_methodology', 'major_methodology'
    confidence: float
    style_indicators: List[str]
    methodology_indicators: List[str]
    evidence_type_match: bool
    testing_verb_match: bool
    scope_similarity: float
    explanation: str

@dataclass
class ControlDifferenceProfile:
    """Comprehensive difference analysis for a control"""
    control_key: str
    total_comparisons: int
    style_differences_count: int
    minor_methodology_count: int
    major_methodology_count: int
    style_percentage: float
    methodology_percentage: float
    average_semantic_similarity: float
    average_methodology_similarity: float
    standardization_opportunity: str  # 'high', 'medium', 'low'
    automation_feasibility: str  # 'ready', 'needs_standardization', 'too_diverse'
    key_variations: List[str]
    recommendations: List[str]

class DifferenceClassifier:
    """
    Advanced classifier for distinguishing methodology vs style differences
    """
    
    def __init__(self):
        self.style_indicators = {
            # Linguistic style indicators
            'word_choice': [
                'review/examine', 'inspect/check', 'test/verify', 'obtain/acquire',
                'assess/evaluate', 'confirm/validate', 'observe/monitor'
            ],
            'sentence_structure': [
                'active vs passive voice', 'long vs short sentences',
                'technical vs plain language', 'formal vs informal tone'
            ],
            'detail_level': [
                'comprehensive description vs brief summary',
                'specific steps vs general approach',
                'technical details vs high-level overview'
            ]
        }
        
        self.methodology_indicators = {
            # Core methodology differences
            'evidence_types': [
                'documentation vs interviews', 'manual vs automated testing',
                'sample testing vs full population', 'observation vs inquiry'
            ],
            'testing_approach': [
                'substantive vs control testing', 'walk-through vs detailed testing',
                'risk-based vs comprehensive approach', 'continuous vs periodic testing'
            ],
            'validation_method': [
                'independent verification vs management representation',
                'third-party confirmation vs internal validation',
                'system-generated vs manual evidence'
            ],
            'scope_parameters': [
                'sample size differences', 'testing period variations',
                'system coverage differences', 'population selection criteria'
            ]
        }
        
        # Thresholds for classification
        self.STYLE_SEMANTIC_THRESHOLD = 0.75  # High semantic similarity suggests style difference
        self.METHODOLOGY_SEMANTIC_THRESHOLD = 0.50  # Low semantic similarity suggests methodology difference
        self.METHODOLOGY_SIMILARITY_THRESHOLD = 0.70  # Methodology structure similarity
        
    def classify_differences(self, semantic_data: Dict[str, Any], 
                           methodology_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main classification method - analyzes both semantic and methodology data
        """
        logger.info("🔍 Starting difference classification analysis...")
        
        results = {
            'classification_metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'semantic_threshold_style': self.STYLE_SEMANTIC_THRESHOLD,
                'semantic_threshold_methodology': self.METHODOLOGY_SEMANTIC_THRESHOLD,
                'methodology_similarity_threshold': self.METHODOLOGY_SIMILARITY_THRESHOLD,
                'total_controls_analyzed': 0
            },
            'control_profiles': {},
            'overall_insights': {},
            'standardization_opportunities': {},
            'automation_recommendations': {}
        }
        
        # Process each control
        control_profiles = []
        for control_key in semantic_data.get('controls_analysis', {}):
            if control_key in methodology_data.get('methodology_analysis', {}):
                profile = self._analyze_control_differences(
                    control_key,
                    semantic_data['controls_analysis'][control_key],
                    methodology_data['methodology_analysis'][control_key]
                )
                control_profiles.append(profile)
                results['control_profiles'][control_key] = asdict(profile)
        
        results['classification_metadata']['total_controls_analyzed'] = len(control_profiles)
        
        # Generate overall insights
        results['overall_insights'] = self._generate_overall_insights(control_profiles)
        results['standardization_opportunities'] = self._identify_standardization_opportunities(control_profiles)
        results['automation_recommendations'] = self._generate_automation_recommendations(control_profiles)
        
        logger.info(f"✅ Classification complete for {len(control_profiles)} controls")
        return results
    
    def _analyze_control_differences(self, control_key: str, 
                                   semantic_data: Dict[str, Any],
                                   methodology_data: Dict[str, Any]) -> ControlDifferenceProfile:
        """
        Analyze differences for a single control
        """
        classifications = []
        
        # Get similarity data (it's a 2D matrix, not a dictionary)
        similarity_matrix = semantic_data.get('similarity_matrix', [])
        methodology_classifications = methodology_data.get('text_methodologies', {})
        
        # Get company list from semantic data
        companies = semantic_data.get('companies', [])
        
        # Analyze all pairwise comparisons
        for i, company1 in enumerate(companies):
            for j, company2 in enumerate(companies[i+1:], i+1):
                
                # Get texts
                text1_data = methodology_classifications.get(company1, {})
                text2_data = methodology_classifications.get(company2, {})
                
                if not text1_data or not text2_data:
                    continue
                
                # Get semantic similarity from matrix
                semantic_sim = 0.0
                if (similarity_matrix and len(similarity_matrix) > i and 
                    len(similarity_matrix[i]) > j):
                    semantic_sim = similarity_matrix[i][j]
                
                # Classify this pair
                classification = self._classify_text_pair(
                    text1_data, text2_data, semantic_sim, company1, company2
                )
                classifications.append(classification)
        
        # Generate control profile
        return self._create_control_profile(control_key, classifications)
    
    def _classify_text_pair(self, text1_data: Dict[str, Any], text2_data: Dict[str, Any],
                           semantic_similarity: float, company1: str, company2: str) -> DifferenceClassification:
        """
        Classify a single pair of text descriptions
        """
        # Extract key methodology features
        methodology_sim = self._calculate_methodology_similarity(text1_data, text2_data)
        
        # Determine difference type
        difference_type, confidence = self._determine_difference_type(
            semantic_similarity, methodology_sim, text1_data, text2_data
        )
        
        # Identify specific indicators
        style_indicators = self._identify_style_indicators(text1_data, text2_data, semantic_similarity)
        methodology_indicators = self._identify_methodology_indicators(text1_data, text2_data)
        
        # Check specific matches
        evidence_match = self._check_evidence_type_match(text1_data, text2_data)
        verb_match = self._check_testing_verb_match(text1_data, text2_data)
        scope_sim = self._calculate_scope_similarity(text1_data, text2_data)
        
        # Generate explanation
        explanation = self._generate_explanation(
            difference_type, semantic_similarity, methodology_sim,
            style_indicators, methodology_indicators, company1, company2
        )
        
        return DifferenceClassification(
            text1=text1_data.get('original_text', '')[:100] + '...',
            text2=text2_data.get('original_text', '')[:100] + '...',
            semantic_similarity=semantic_similarity,
            methodology_similarity=methodology_sim,
            difference_type=difference_type,
            confidence=confidence,
            style_indicators=style_indicators,
            methodology_indicators=methodology_indicators,
            evidence_type_match=evidence_match,
            testing_verb_match=verb_match,
            scope_similarity=scope_sim,
            explanation=explanation
        )
    
    def _calculate_methodology_similarity(self, text1_data: Dict[str, Any], 
                                        text2_data: Dict[str, Any]) -> float:
        """
        Calculate similarity based on methodology features
        """
        similarities = []
        
        # Compare methodology types
        method1 = text1_data.get('methodology_type', {}).get('primary_type', 'unknown')
        method2 = text2_data.get('methodology_type', {}).get('primary_type', 'unknown')
        
        if method1 != 'unknown' and method2 != 'unknown':
            similarities.append(1.0 if method1 == method2 else 0.0)
        
        # Compare evidence types
        evidence1 = set(text1_data.get('evidence_analysis', {}).get('primary_types', []))
        evidence2 = set(text2_data.get('evidence_analysis', {}).get('primary_types', []))
        
        if evidence1 and evidence2:
            evidence_sim = len(evidence1.intersection(evidence2)) / len(evidence1.union(evidence2))
            similarities.append(evidence_sim)
        
        # Compare testing rigor
        rigor1 = text1_data.get('testing_depth', {}).get('rigor_level', 'unknown')
        rigor2 = text2_data.get('testing_depth', {}).get('rigor_level', 'unknown')
        
        if rigor1 != 'unknown' and rigor2 != 'unknown':
            # Convert to numeric for comparison
            rigor_map = {'basic': 1, 'standard': 2, 'comprehensive': 3}
            r1_val = rigor_map.get(rigor1, 0)
            r2_val = rigor_map.get(rigor2, 0)
            
            if r1_val > 0 and r2_val > 0:
                rigor_sim = 1.0 - abs(r1_val - r2_val) / 2.0  # Normalize to 0-1
                similarities.append(rigor_sim)
        
        # Compare scope parameters
        scope_sim = self._calculate_scope_similarity(text1_data, text2_data)
        if scope_sim >= 0:  # Valid similarity score
            similarities.append(scope_sim)
        
        # Return average similarity
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_scope_similarity(self, text1_data: Dict[str, Any], 
                                  text2_data: Dict[str, Any]) -> float:
        """
        Calculate similarity of scope parameters
        """
        scope1 = text1_data.get('scope_analysis', {})
        scope2 = text2_data.get('scope_analysis', {})
        
        similarities = []
        
        # Compare sample sizes
        size1 = scope1.get('sample_size', {}).get('primary_size', 0)
        size2 = scope2.get('sample_size', {}).get('primary_size', 0)
        
        if size1 > 0 and size2 > 0:
            # Calculate similarity based on size ratio
            ratio = min(size1, size2) / max(size1, size2)
            similarities.append(ratio)
        
        # Compare scope types
        type1 = scope1.get('scope_type', 'unknown')
        type2 = scope2.get('scope_type', 'unknown')
        
        if type1 != 'unknown' and type2 != 'unknown':
            similarities.append(1.0 if type1 == type2 else 0.0)
        
        return sum(similarities) / len(similarities) if similarities else -1.0
    
    def _determine_difference_type(self, semantic_sim: float, methodology_sim: float,
                                 text1_data: Dict[str, Any], text2_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Determine if differences are style-based or methodology-based
        """
        # High semantic similarity + high methodology similarity = Style differences
        if semantic_sim >= self.STYLE_SEMANTIC_THRESHOLD and methodology_sim >= self.METHODOLOGY_SIMILARITY_THRESHOLD:
            return 'style', min(semantic_sim, methodology_sim)
        
        # Low semantic similarity + low methodology similarity = Major methodology differences
        elif semantic_sim < self.METHODOLOGY_SEMANTIC_THRESHOLD and methodology_sim < self.METHODOLOGY_SIMILARITY_THRESHOLD:
            return 'major_methodology', 1.0 - max(semantic_sim, methodology_sim)
        
        # Mixed signals = Minor methodology differences
        else:
            confidence = abs(semantic_sim - methodology_sim)  # Higher difference = more confident
            return 'minor_methodology', confidence
    
    def _identify_style_indicators(self, text1_data: Dict[str, Any], text2_data: Dict[str, Any],
                                 semantic_sim: float) -> List[str]:
        """
        Identify specific style difference indicators
        """
        indicators = []
        
        # High semantic similarity suggests style differences
        if semantic_sim >= self.STYLE_SEMANTIC_THRESHOLD:
            indicators.append('high_semantic_similarity')
        
        # Compare verb usage
        verb1 = text1_data.get('methodology_type', {}).get('primary_verb', '')
        verb2 = text2_data.get('methodology_type', {}).get('primary_verb', '')
        
        # Check for synonym verbs
        synonym_pairs = [
            ('inquired', 'asked'), ('reviewed', 'examined'), ('inspected', 'checked'),
            ('tested', 'verified'), ('observed', 'monitored'), ('obtained', 'acquired')
        ]
        
        for pair in synonym_pairs:
            if (verb1 in pair and verb2 in pair) or (verb2 in pair and verb1 in pair):
                indicators.append(f'synonym_verbs_{verb1}_{verb2}')
        
        # Check text length differences (detailed vs brief)
        len1 = len(text1_data.get('original_text', ''))
        len2 = len(text2_data.get('original_text', ''))
        
        if abs(len1 - len2) > 100:  # Significant length difference
            if len1 > len2:
                indicators.append('detailed_vs_brief_description')
            else:
                indicators.append('brief_vs_detailed_description')
        
        return indicators
    
    def _identify_methodology_indicators(self, text1_data: Dict[str, Any], 
                                       text2_data: Dict[str, Any]) -> List[str]:
        """
        Identify specific methodology difference indicators
        """
        indicators = []
        
        # Different evidence types
        evidence1 = set(text1_data.get('evidence_analysis', {}).get('primary_types', []))
        evidence2 = set(text2_data.get('evidence_analysis', {}).get('primary_types', []))
        
        if evidence1 and evidence2 and not evidence1.intersection(evidence2):
            indicators.append(f'different_evidence_types_{list(evidence1)[0]}_vs_{list(evidence2)[0]}')
        
        # Different testing rigor
        rigor1 = text1_data.get('testing_depth', {}).get('rigor_level', '')
        rigor2 = text2_data.get('testing_depth', {}).get('rigor_level', '')
        
        if rigor1 and rigor2 and rigor1 != rigor2:
            indicators.append(f'different_rigor_{rigor1}_vs_{rigor2}')
        
        # Different sample sizes (significant difference)
        size1 = text1_data.get('scope_analysis', {}).get('sample_size', {}).get('primary_size', 0)
        size2 = text2_data.get('scope_analysis', {}).get('sample_size', {}).get('primary_size', 0)
        
        if size1 > 0 and size2 > 0:
            ratio = max(size1, size2) / min(size1, size2)
            if ratio >= 2.0:  # Significant size difference
                indicators.append(f'sample_size_difference_{size1}_vs_{size2}')
        
        # Different methodology types
        method1 = text1_data.get('methodology_type', {}).get('primary_type', '')
        method2 = text2_data.get('methodology_type', {}).get('primary_type', '')
        
        if method1 and method2 and method1 != method2:
            indicators.append(f'different_methodology_{method1}_vs_{method2}')
        
        return indicators
    
    def _check_evidence_type_match(self, text1_data: Dict[str, Any], 
                                 text2_data: Dict[str, Any]) -> bool:
        """
        Check if evidence types match
        """
        evidence1 = set(text1_data.get('evidence_analysis', {}).get('primary_types', []))
        evidence2 = set(text2_data.get('evidence_analysis', {}).get('primary_types', []))
        
        if not evidence1 or not evidence2:
            return False
        
        return len(evidence1.intersection(evidence2)) > 0
    
    def _check_testing_verb_match(self, text1_data: Dict[str, Any], 
                                text2_data: Dict[str, Any]) -> bool:
        """
        Check if testing verbs match (including synonyms)
        """
        verb1 = text1_data.get('methodology_type', {}).get('primary_verb', '')
        verb2 = text2_data.get('methodology_type', {}).get('primary_verb', '')
        
        if not verb1 or not verb2:
            return False
        
        # Exact match
        if verb1 == verb2:
            return True
        
        # Check synonyms
        synonym_groups = [
            ['inquired', 'asked', 'questioned'],
            ['reviewed', 'examined', 'analyzed'],
            ['inspected', 'checked', 'verified'],
            ['tested', 'validated', 'confirmed'],
            ['observed', 'monitored', 'watched'],
            ['obtained', 'acquired', 'collected']
        ]
        
        for group in synonym_groups:
            if verb1 in group and verb2 in group:
                return True
        
        return False
    
    def _generate_explanation(self, difference_type: str, semantic_sim: float,
                            methodology_sim: float, style_indicators: List[str],
                            methodology_indicators: List[str], company1: str, company2: str) -> str:
        """
        Generate human-readable explanation of the classification
        """
        if difference_type == 'style':
            explanation = f"Style difference: {company1} and {company2} use similar testing methodology "
            explanation += f"(methodology similarity: {methodology_sim:.2f}) but express it differently "
            explanation += f"(semantic similarity: {semantic_sim:.2f})."
            
            if style_indicators:
                explanation += f" Key style variations: {', '.join(style_indicators[:3])}."
        
        elif difference_type == 'major_methodology':
            explanation = f"Major methodology difference: {company1} and {company2} use fundamentally "
            explanation += f"different testing approaches (methodology similarity: {methodology_sim:.2f}, "
            explanation += f"semantic similarity: {semantic_sim:.2f})."
            
            if methodology_indicators:
                explanation += f" Key differences: {', '.join(methodology_indicators[:3])}."
        
        else:  # minor_methodology
            explanation = f"Minor methodology difference: {company1} and {company2} have similar overall "
            explanation += f"approaches but with notable variations (semantic similarity: {semantic_sim:.2f}, "
            explanation += f"methodology similarity: {methodology_sim:.2f})."
            
            if methodology_indicators:
                explanation += f" Variations: {', '.join(methodology_indicators[:2])}."
        
        return explanation
    
    def _create_control_profile(self, control_key: str, 
                              classifications: List[DifferenceClassification]) -> ControlDifferenceProfile:
        """
        Create comprehensive profile for a control's differences
        """
        if not classifications:
            return ControlDifferenceProfile(
                control_key=control_key,
                total_comparisons=0,
                style_differences_count=0,
                minor_methodology_count=0,
                major_methodology_count=0,
                style_percentage=0.0,
                methodology_percentage=0.0,
                average_semantic_similarity=0.0,
                average_methodology_similarity=0.0,
                standardization_opportunity='low',
                automation_feasibility='too_diverse',
                key_variations=[],
                recommendations=[]
            )
        
        # Count difference types
        type_counts = Counter(c.difference_type for c in classifications)
        total = len(classifications)
        
        style_count = type_counts.get('style', 0)
        minor_method_count = type_counts.get('minor_methodology', 0)
        major_method_count = type_counts.get('major_methodology', 0)
        
        style_pct = (style_count / total) * 100
        method_pct = ((minor_method_count + major_method_count) / total) * 100
        
        # Calculate averages
        avg_semantic = sum(c.semantic_similarity for c in classifications) / total
        avg_methodology = sum(c.methodology_similarity for c in classifications) / total
        
        # Determine standardization opportunity
        if style_pct >= 70:
            standardization = 'high'
        elif style_pct >= 40:
            standardization = 'medium'
        else:
            standardization = 'low'
        
        # Determine automation feasibility
        if style_pct >= 80 and avg_semantic >= 0.7:
            automation = 'ready'
        elif style_pct >= 50 and major_method_count / total < 0.3:
            automation = 'needs_standardization'
        else:
            automation = 'too_diverse'
        
        # Collect key variations
        all_indicators = []
        for c in classifications:
            all_indicators.extend(c.methodology_indicators)
        
        key_variations = [indicator for indicator, count in 
                         Counter(all_indicators).most_common(5)]
        
        # Generate recommendations
        recommendations = self._generate_control_recommendations(
            style_pct, method_pct, standardization, automation, key_variations
        )
        
        return ControlDifferenceProfile(
            control_key=control_key,
            total_comparisons=total,
            style_differences_count=style_count,
            minor_methodology_count=minor_method_count,
            major_methodology_count=major_method_count,
            style_percentage=style_pct,
            methodology_percentage=method_pct,
            average_semantic_similarity=avg_semantic,
            average_methodology_similarity=avg_methodology,
            standardization_opportunity=standardization,
            automation_feasibility=automation,
            key_variations=key_variations,
            recommendations=recommendations
        )
    
    def _generate_control_recommendations(self, style_pct: float, method_pct: float,
                                        standardization: str, automation: str,
                                        key_variations: List[str]) -> List[str]:
        """
        Generate specific recommendations for a control
        """
        recommendations = []
        
        if automation == 'ready':
            recommendations.append("HIGH PRIORITY: Ready for template automation")
            recommendations.append("Standardize language to single template")
        elif automation == 'needs_standardization':
            recommendations.append("MEDIUM PRIORITY: Standardize methodology before automation")
            recommendations.append("Focus on methodology alignment across companies")
        else:
            recommendations.append("LOW PRIORITY: Too much methodology diversity for automation")
            recommendations.append("Consider separate templates for different approaches")
        
        if style_pct >= 60:
            recommendations.append("Style differences dominate - focus on language standardization")
        
        if method_pct >= 50:
            recommendations.append("Significant methodology differences - review testing approaches")
        
        if key_variations:
            recommendations.append(f"Address key variations: {', '.join(key_variations[:2])}")
        
        return recommendations
    
    def _generate_overall_insights(self, profiles: List[ControlDifferenceProfile]) -> Dict[str, Any]:
        """
        Generate overall insights across all controls
        """
        if not profiles:
            return {}
        
        total_controls = len(profiles)
        
        # Calculate overall statistics
        avg_style_pct = sum(p.style_percentage for p in profiles) / total_controls
        avg_method_pct = sum(p.methodology_percentage for p in profiles) / total_controls
        avg_semantic_sim = sum(p.average_semantic_similarity for p in profiles) / total_controls
        avg_method_sim = sum(p.average_methodology_similarity for p in profiles) / total_controls
        
        # Count standardization opportunities
        standardization_counts = Counter(p.standardization_opportunity for p in profiles)
        automation_counts = Counter(p.automation_feasibility for p in profiles)
        
        return {
            'total_controls_analyzed': total_controls,
            'average_style_percentage': round(avg_style_pct, 1),
            'average_methodology_percentage': round(avg_method_pct, 1),
            'average_semantic_similarity': round(avg_semantic_sim, 3),
            'average_methodology_similarity': round(avg_method_sim, 3),
            'standardization_distribution': dict(standardization_counts),
            'automation_distribution': dict(automation_counts),
            'key_finding': self._generate_key_finding(avg_style_pct, avg_method_pct, automation_counts)
        }
    
    def _generate_key_finding(self, avg_style_pct: float, avg_method_pct: float,
                            automation_counts: Counter) -> str:
        """
        Generate key finding summary
        """
        ready_count = automation_counts.get('ready', 0)
        total_controls = sum(automation_counts.values())
        
        if avg_style_pct >= 60:
            finding = f"Style differences dominate ({avg_style_pct:.1f}% average). "
            if ready_count / total_controls >= 0.3:
                finding += f"{ready_count} controls ready for automation."
            else:
                finding += "Focus on language standardization for automation."
        elif avg_method_pct >= 60:
            finding = f"Methodology differences dominate ({avg_method_pct:.1f}% average). "
            finding += "Significant diversity in testing approaches."
        else:
            finding = "Mixed style and methodology differences. "
            finding += f"{ready_count} controls ready for automation template."
        
        return finding
    
    def _identify_standardization_opportunities(self, profiles: List[ControlDifferenceProfile]) -> Dict[str, Any]:
        """
        Identify specific standardization opportunities
        """
        high_opportunity = [p for p in profiles if p.standardization_opportunity == 'high']
        medium_opportunity = [p for p in profiles if p.standardization_opportunity == 'medium']
        
        ready_for_automation = [p for p in profiles if p.automation_feasibility == 'ready']
        needs_standardization = [p for p in profiles if p.automation_feasibility == 'needs_standardization']
        
        return {
            'high_standardization_opportunity': [p.control_key for p in high_opportunity],
            'medium_standardization_opportunity': [p.control_key for p in medium_opportunity],
            'ready_for_automation': [p.control_key for p in ready_for_automation],
            'needs_methodology_alignment': [p.control_key for p in needs_standardization],
            'summary': {
                'high_opportunity_count': len(high_opportunity),
                'automation_ready_count': len(ready_for_automation),
                'standardization_needed_count': len(needs_standardization)
            }
        }
    
    def _generate_automation_recommendations(self, profiles: List[ControlDifferenceProfile]) -> Dict[str, Any]:
        """
        Generate automation strategy recommendations
        """
        ready = [p for p in profiles if p.automation_feasibility == 'ready']
        needs_work = [p for p in profiles if p.automation_feasibility == 'needs_standardization']
        too_diverse = [p for p in profiles if p.automation_feasibility == 'too_diverse']
        
        return {
            'immediate_automation_candidates': {
                'controls': [p.control_key for p in ready[:10]],  # Top 10
                'count': len(ready),
                'approach': 'Create standardized templates with minor variations'
            },
            'standardization_first_candidates': {
                'controls': [p.control_key for p in needs_work[:10]],  # Top 10
                'count': len(needs_work),
                'approach': 'Align methodologies before template creation'
            },
            'manual_approach_recommended': {
                'controls': [p.control_key for p in too_diverse[:5]],  # Top 5 most diverse
                'count': len(too_diverse),
                'approach': 'Maintain company-specific approaches or create multiple templates'
            },
            'automation_strategy': self._create_automation_strategy(ready, needs_work, too_diverse)
        }
    
    def _create_automation_strategy(self, ready: List[ControlDifferenceProfile],
                                  needs_work: List[ControlDifferenceProfile],
                                  too_diverse: List[ControlDifferenceProfile]) -> Dict[str, str]:
        """
        Create comprehensive automation strategy
        """
        total = len(ready) + len(needs_work) + len(too_diverse)
        
        if not total:
            return {'phase1': 'No controls analyzed', 'phase2': '', 'phase3': ''}
        
        ready_pct = (len(ready) / total) * 100
        needs_pct = (len(needs_work) / total) * 100
        diverse_pct = (len(too_diverse) / total) * 100
        
        strategy = {
            'phase1': f'Immediate automation for {len(ready)} controls ({ready_pct:.1f}%) with high style consistency',
            'phase2': f'Standardization effort for {len(needs_work)} controls ({needs_pct:.1f}%) with methodology alignment needs',
            'phase3': f'Manual approach for {len(too_diverse)} controls ({diverse_pct:.1f}%) with fundamental methodology differences',
            'overall_automation_potential': f'{ready_pct + needs_pct:.1f}% of controls suitable for automation'
        }
        
        return strategy


def main():
    """
    Test the difference classifier
    """
    print("🔍 SOC2 Difference Classifier - Phase 3 Test")
    print("=" * 50)
    
    # This would typically be called by the main analysis pipeline
    # For testing, we'll check if semantic and methodology data exists
    
    # Get latest output run for loading data
    output_manager = get_output_manager()
    latest_run = output_manager.get_latest_run()
    
    if latest_run:
        semantic_file = os.path.join(latest_run, "json", "semantic_analysis_results.json")
        methodology_file = os.path.join(latest_run, "json", "methodology_analysis_results.json")
    else:
        # Fallback to old structure
        semantic_file = "data/processed/latest/semantic_analysis/semantic_analysis_results.json"
        methodology_file = "data/processed/latest/semantic_analysis/methodology_analysis_results.json"
    
    import os
    
    if not os.path.exists(semantic_file):
        print(f"❌ Semantic analysis results not found: {semantic_file}")
        print("   Run semantic analysis first: python semantic_analysis/semantic_analyzer.py")
        return False
    
    if not os.path.exists(methodology_file):
        print(f"❌ Methodology analysis results not found: {methodology_file}")
        print("   Will attempt to generate minimal methodology data from semantic results...")
        
        # Try to create basic methodology data from semantic results for testing
        try:
            with open(semantic_file, 'r') as f:
                semantic_data = json.load(f)
            
            # Create minimal methodology data for testing
            methodology_data = {
                'methodology_analysis': {}
            }
            
            # For each control in semantic analysis, create basic methodology structure
            controls_analysis = semantic_data.get('controls_analysis', {})
            for control_key, control_data in controls_analysis.items():
                methodology_data['methodology_analysis'][control_key] = {
                    'text_methodologies': {}
                }
                
                # Add basic methodology info for each company
                if 'companies' in control_data:
                    for company in control_data['companies']:
                        methodology_data['methodology_analysis'][control_key]['text_methodologies'][company] = {
                            'original_text': f'Sample text for {company}',
                            'methodology_type': {'primary_type': 'inquiry_based', 'primary_verb': 'inquired'},
                            'evidence_analysis': {'primary_types': ['documentation']},
                            'testing_depth': {'rigor_level': 'standard'},
                            'scope_analysis': {'sample_size': {'primary_size': 1}, 'scope_type': 'full_population'}
                        }
                        
        except Exception as e:
            print(f"❌ Could not create minimal methodology data: {e}")
            return False
    
    try:
        # Load semantic data
        with open(semantic_file, 'r') as f:
            semantic_data = json.load(f)
        
        # Load or use generated methodology data
        if os.path.exists(methodology_file):
            with open(methodology_file, 'r') as f:
                methodology_data = json.load(f)
        else:
            # Use the generated minimal data from above
            print("   Using generated minimal methodology data for testing...")
        
        # Run classification
        classifier = DifferenceClassifier()
        results = classifier.classify_differences(semantic_data, methodology_data)
        
        # Save results
        output_manager = get_output_manager()
        output_file = output_manager.get_output_path('json', 'difference_classification_results.json')
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        insights = results.get('overall_insights', {})
        print(f"✅ Classification complete!")
        print(f"   Controls analyzed: {insights.get('total_controls_analyzed', 0)}")
        print(f"   Average style differences: {insights.get('average_style_percentage', 0):.1f}%")
        print(f"   Average methodology differences: {insights.get('average_methodology_percentage', 0):.1f}%")
        print(f"   Key finding: {insights.get('key_finding', 'N/A')}")
        print(f"   Results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()