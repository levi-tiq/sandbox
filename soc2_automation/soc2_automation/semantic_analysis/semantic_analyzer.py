#!/usr/bin/env python3
"""
SOC2 Semantic Analyzer

Core semantic similarity engine for analyzing control test descriptions.
Distinguishes between semantic meaning differences vs. superficial text differences.

This module implements Phase 1 of the semantic analysis roadmap:
- Sentence-BERT based semantic embeddings
- Cosine similarity calculations
- Similarity threshold classification (High >0.8, Medium 0.5-0.8, Low <0.5)

Usage:
    from semantic_analyzer import SemanticAnalyzer
    
    analyzer = SemanticAnalyzer()
    analyzer.load_variance_data("../data/processed/latest/control_variance_report.json")
    semantic_results = analyzer.analyze_semantic_similarity()
"""

import json
import os
import pickle
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import re
import sys
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager
except ImportError:
    # Fallback for different execution contexts
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import AgglomerativeClustering
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️  Warning: sentence-transformers or scikit-learn not available. Please run:")
    print("   pip install sentence-transformers scikit-learn")

class TextPreprocessor:
    """Text preprocessing pipeline for SOC2 test descriptions"""
    
    def __init__(self):
        # Common SOC2 testing action verbs
        self.action_verbs = [
            'inquired', 'inspected', 'observed', 'reviewed', 'tested', 
            'verified', 'confirmed', 'obtained', 'selected', 'performed',
            'compared', 'evaluated', 'reperformed', 'examined', 'analyzed'
        ]
        
        # Common SOC2 terms that may introduce noise
        self.noise_patterns = [
            r'\b(during|for|the|period|from|to|through)\s+\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',  # Date ranges
            r'\b(sample|samples)\s+of\s+\d+\b',  # Sample sizes
            r'\b\d+\s+(users?|systems?|transactions?|controls?)\b',  # Numeric references
            r'\b(management|we|auditor|tester)\b',  # Subject references
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize test description text"""
        if not text:
            return ""
        
        # Convert to lowercase
        cleaned = text.lower().strip()
        
        # Remove noise patterns while preserving core meaning
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove leading/trailing punctuation but preserve internal structure
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned)
        
        return cleaned
    
    def extract_core_methodology(self, text: str) -> Dict[str, Any]:
        """Extract core methodology components from test description"""
        if not text:
            return {}
        
        cleaned = self.clean_text(text)
        
        # Extract primary action verb
        primary_verb = None
        for verb in self.action_verbs:
            if verb in cleaned:
                primary_verb = verb
                break
        
        # Extract evidence types mentioned
        evidence_patterns = {
            'documentation': r'\b(document|report|policy|procedure|log|record|manual)\b',
            'personnel': r'\b(interview|discussion|inquiry|personnel|staff|employee)\b',
            'technical': r'\b(scan|configuration|setting|system|database|network|access)\b',
            'sample': r'\b(sample|transaction|user|account|entry)\b'
        }
        
        evidence_types = []
        for evidence_type, pattern in evidence_patterns.items():
            if re.search(pattern, cleaned, re.IGNORECASE):
                evidence_types.append(evidence_type)
        
        # Extract scope indicators
        scope_patterns = {
            'comprehensive': r'\b(all|every|complete|comprehensive|entire)\b',
            'sample': r'\b(sample|selected|subset)\b',
            'specific': r'\b(specific|particular|certain)\b'
        }
        
        scope_type = 'standard'
        for scope, pattern in scope_patterns.items():
            if re.search(pattern, cleaned, re.IGNORECASE):
                scope_type = scope
                break
        
        return {
            'primary_verb': primary_verb,
            'evidence_types': evidence_types,
            'scope_type': scope_type,
            'cleaned_text': cleaned,
            'original_length': len(text),
            'cleaned_length': len(cleaned)
        }

class SemanticAnalyzer:
    """Main semantic similarity analyzer for SOC2 control tests"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic analyzer
        
        Args:
            model_name: Sentence-BERT model to use for embeddings
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available. Please install sentence-transformers and scikit-learn.")
        
        self.model_name = model_name
        self.model = None
        self.preprocessor = TextPreprocessor()
        
        # Data storage
        self.variance_data = None
        self.embeddings_cache = {}
        self.similarity_matrices = {}
        
        # Analysis results
        self.semantic_results = {}
        
        # Similarity thresholds (as defined in roadmap)
        self.similarity_thresholds = {
            'high': 0.8,    # Style differences only
            'medium': 0.5,  # Minor methodology differences
            'low': 0.0      # Major methodology differences
        }
    
    def _load_model(self):
        """Load the Sentence-BERT model"""
        if self.model is None:
            print(f"🤖 Loading Sentence-BERT model: {self.model_name}")
            try:
                self.model = SentenceTransformer(self.model_name)
                print("✅ Model loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                raise
    
    def load_variance_data(self, variance_file: str = "data/processed/latest/control_variance_report.json"):
        """Load control variance data from analysis report"""
        print(f"📊 Loading variance data from: {variance_file}")
        
        if not os.path.exists(variance_file):
            raise FileNotFoundError(f"Variance report not found: {variance_file}")
        
        with open(variance_file, 'r', encoding='utf-8') as f:
            self.variance_data = json.load(f)
        
        variance_analysis = self.variance_data.get('variance_analysis', {})
        print(f"✅ Loaded variance data for {len(variance_analysis)} controls")
        
        return self.variance_data
    
    def generate_embeddings(self, texts: List[str], cache_key: str = None) -> np.ndarray:
        """Generate semantic embeddings for a list of texts"""
        if not texts:
            return np.array([])
        
        # Check cache first
        if cache_key and cache_key in self.embeddings_cache:
            print(f"📦 Using cached embeddings for {cache_key}")
            return self.embeddings_cache[cache_key]
        
        # Load model if needed
        self._load_model()
        
        # Preprocess texts
        processed_texts = []
        for text in texts:
            methodology = self.preprocessor.extract_core_methodology(text)
            processed_texts.append(methodology['cleaned_text'])
        
        print(f"🧠 Generating embeddings for {len(processed_texts)} texts...")
        
        # Generate embeddings
        try:
            embeddings = self.model.encode(processed_texts, convert_to_tensor=False)
            embeddings = np.array(embeddings)
            
            # Cache if key provided
            if cache_key:
                self.embeddings_cache[cache_key] = embeddings
            
            print(f"✅ Generated embeddings: shape {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            print(f"❌ Failed to generate embeddings: {e}")
            raise
    
    def calculate_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity matrix for embeddings"""
        if embeddings.size == 0:
            return np.array([])
        
        try:
            similarity_matrix = cosine_similarity(embeddings)
            return similarity_matrix
        except Exception as e:
            print(f"❌ Failed to calculate similarity matrix: {e}")
            raise
    
    def classify_similarity(self, similarity_score: float) -> Dict[str, Any]:
        """Classify similarity score into categories"""
        if similarity_score >= self.similarity_thresholds['high']:
            category = 'high'
            description = 'Style differences only'
            methodology_difference = 'minimal'
        elif similarity_score >= self.similarity_thresholds['medium']:
            category = 'medium'  
            description = 'Minor methodology differences'
            methodology_difference = 'moderate'
        else:
            category = 'low'
            description = 'Major methodology differences'
            methodology_difference = 'significant'
        
        return {
            'category': category,
            'score': similarity_score,
            'description': description,
            'methodology_difference': methodology_difference
        }
    
    def analyze_control_semantic_similarity(self, control_key: str, control_data: Dict[str, Any], include_methodology: bool = True) -> Dict[str, Any]:
        """Analyze semantic similarity for a single control"""
        print(f"🔍 Analyzing semantic similarity for: {control_key}")
        
        # Extract test texts and company mapping
        company_tests = control_data.get('company_tests', {})
        
        all_texts = []
        text_to_company = {}
        company_to_texts = defaultdict(list)
        
        for company, tests in company_tests.items():
            if isinstance(tests, list):
                test_list = tests
            else:
                test_list = tests.get('tests_applied', []) if isinstance(tests, dict) else []
            
            for i, test in enumerate(test_list):
                all_texts.append(test)
                text_key = len(all_texts) - 1
                text_to_company[text_key] = company
                company_to_texts[company].append({
                    'text': test,
                    'index': text_key,
                    'methodology': self.preprocessor.extract_core_methodology(test)
                })
        
        if len(all_texts) < 2:
            return {
                'control_key': control_key,
                'total_texts': len(all_texts),
                'companies': list(company_tests.keys()),
                'semantic_analysis': 'insufficient_data',
                'similarity_matrix': [],
                'pairwise_similarities': [],
                'clustering_results': None
            }
        
        # Generate embeddings
        cache_key = f"control_{hash(control_key)}"
        embeddings = self.generate_embeddings(all_texts, cache_key)
        
        # Calculate similarity matrix
        similarity_matrix = self.calculate_similarity_matrix(embeddings)
        
        # Analyze pairwise similarities
        pairwise_similarities = []
        for i in range(len(all_texts)):
            for j in range(i + 1, len(all_texts)):
                similarity_score = similarity_matrix[i][j]
                classification = self.classify_similarity(similarity_score)
                
                pairwise_similarities.append({
                    'text1_index': int(i),
                    'text2_index': int(j),
                    'company1': text_to_company[i],
                    'company2': text_to_company[j],
                    'similarity_score': float(similarity_score),
                    'classification': classification,
                    'text1_preview': all_texts[i][:100] + "..." if len(all_texts[i]) > 100 else all_texts[i],
                    'text2_preview': all_texts[j][:100] + "..." if len(all_texts[j]) > 100 else all_texts[j]
                })
        
        # Sort by similarity score (highest first)
        pairwise_similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Clustering analysis
        clustering_results = None
        if len(all_texts) >= 3:
            try:
                # Use agglomerative clustering
                clustering = AgglomerativeClustering(
                    n_clusters=min(3, len(all_texts)//2 + 1),
                    metric='precomputed',
                    linkage='average'
                )
                
                # Convert similarity to distance
                distance_matrix = 1 - similarity_matrix
                cluster_labels = clustering.fit_predict(distance_matrix)
                
                clusters = defaultdict(list)
                for idx, label in enumerate(cluster_labels):
                    clusters[int(label)].append({
                        'text_index': idx,
                        'company': text_to_company[idx],
                        'text_preview': all_texts[idx][:100] + "..." if len(all_texts[idx]) > 100 else all_texts[idx]
                    })
                
                clustering_results = {
                    'num_clusters': len(clusters),
                    'clusters': dict(clusters),
                    'silhouette_analysis': 'TODO'  # Can be implemented later
                }
            except Exception as e:
                print(f"⚠️  Clustering failed for {control_key}: {e}")
                clustering_results = None
        
        # Summary statistics
        similarity_scores = [pair['similarity_score'] for pair in pairwise_similarities]
        
        summary_stats = {
            'mean_similarity': float(np.mean(similarity_scores)) if similarity_scores else 0.0,
            'median_similarity': float(np.median(similarity_scores)) if similarity_scores else 0.0,
            'min_similarity': float(np.min(similarity_scores)) if similarity_scores else 0.0,
            'max_similarity': float(np.max(similarity_scores)) if similarity_scores else 0.0,
            'std_similarity': float(np.std(similarity_scores)) if similarity_scores else 0.0
        }
        
        # Classification distribution
        classification_counts = defaultdict(int)
        for pair in pairwise_similarities:
            classification_counts[pair['classification']['category']] += 1
        
        # Enhanced methodology analysis (Phase 2 integration)
        methodology_analysis = None
        if include_methodology:
            try:
                methodology_analysis = self._analyze_control_methodology(all_texts)
            except Exception as e:
                print(f"⚠️  Methodology analysis failed for {control_key}: {e}")
                methodology_analysis = {'error': str(e)}
        
        return {
            'control_key': control_key,
            'control_id': control_data.get('control_id', ''),
            'control_name': control_data.get('control_name', ''),
            'total_texts': len(all_texts),
            'total_companies': len(company_tests),
            'companies': list(company_tests.keys()),
            'company_to_texts': dict(company_to_texts),
            'similarity_matrix': similarity_matrix.tolist() if similarity_matrix.size > 0 else [],
            'pairwise_similarities': pairwise_similarities,
            'clustering_results': clustering_results,
            'summary_stats': summary_stats,
            'classification_distribution': dict(classification_counts),
            'methodology_analysis': methodology_analysis,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def analyze_semantic_similarity(self) -> Dict[str, Any]:
        """Analyze semantic similarity for all controls in variance data"""
        if not self.variance_data:
            raise ValueError("No variance data loaded. Call load_variance_data() first.")
        
        print("🧠 Starting comprehensive semantic similarity analysis...")
        
        variance_analysis = self.variance_data.get('variance_analysis', {})
        total_controls = len(variance_analysis)
        
        results = {}
        processed_count = 0
        
        for control_key, control_data in variance_analysis.items():
            try:
                processed_count += 1
                print(f"📊 Processing {processed_count}/{total_controls}: {control_key[:60]}...")
                
                control_results = self.analyze_control_semantic_similarity(control_key, control_data)
                results[control_key] = control_results
                
                # Progress indicator
                if processed_count % 10 == 0:
                    print(f"✅ Completed {processed_count}/{total_controls} controls")
                    
            except Exception as e:
                print(f"❌ Error processing {control_key}: {e}")
                results[control_key] = {
                    'control_key': control_key,
                    'error': str(e),
                    'analysis_timestamp': datetime.now().isoformat()
                }
        
        # Global analysis summary
        global_summary = self._generate_global_semantic_summary(results)
        
        self.semantic_results = {
            'analysis_metadata': {
                'total_controls_analyzed': len(results),
                'model_name': self.model_name,
                'similarity_thresholds': self.similarity_thresholds,
                'analysis_timestamp': datetime.now().isoformat(),
                'source_variance_file': getattr(self, '_source_file', 'unknown')
            },
            'controls_analysis': results,
            'global_summary': global_summary
        }
        
        print(f"✅ Semantic analysis complete for {len(results)} controls")
        return self.semantic_results
    
    def _generate_global_semantic_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate global summary statistics across all controls"""
        
        all_similarities = []
        classification_totals = defaultdict(int)
        controls_by_category = defaultdict(list)
        
        for control_key, control_results in results.items():
            if 'error' in control_results:
                continue
                
            # Collect similarity scores
            for pair in control_results.get('pairwise_similarities', []):
                all_similarities.append(pair['similarity_score'])
                classification_totals[pair['classification']['category']] += 1
            
            # Categorize controls by dominant similarity type
            classification_dist = control_results.get('classification_distribution', {})
            if classification_dist:
                dominant_category = max(classification_dist.items(), key=lambda x: x[1])[0]
                controls_by_category[dominant_category].append({
                    'control_key': control_key,
                    'control_id': control_results.get('control_id', ''),
                    'mean_similarity': control_results.get('summary_stats', {}).get('mean_similarity', 0)
                })
        
        # Sort controls by similarity within each category
        for category in controls_by_category:
            controls_by_category[category].sort(key=lambda x: x['mean_similarity'], reverse=True)
        
        return {
            'total_pairwise_comparisons': int(len(all_similarities)),
            'overall_similarity_stats': {
                'mean': float(np.mean(all_similarities)) if all_similarities else 0.0,
                'median': float(np.median(all_similarities)) if all_similarities else 0.0,
                'std': float(np.std(all_similarities)) if all_similarities else 0.0,
                'min': float(np.min(all_similarities)) if all_similarities else 0.0,
                'max': float(np.max(all_similarities)) if all_similarities else 0.0
            },
            'classification_distribution': dict(classification_totals),
            'controls_by_similarity_category': dict(controls_by_category),
            'automation_candidates': {
                'high_similarity_controls': int(len(controls_by_category.get('high', []))),
                'medium_similarity_controls': int(len(controls_by_category.get('medium', []))),
                'low_similarity_controls': int(len(controls_by_category.get('low', [])))
            }
        }
    
    def save_results(self, output_dir: str = None):
        """Save semantic analysis results to timestamped run directory"""
        if not self.semantic_results:
            raise ValueError("No semantic results to save. Run analyze_semantic_similarity() first.")
        
        # Use output manager for consistent path generation
        output_manager = get_output_manager()
        
        # Save main results
        results_file = output_manager.get_output_path('json', "semantic_analysis_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.semantic_results, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
        
        print(f"💾 Semantic analysis results saved to: {results_file}")
        
        # Save embeddings cache
        if self.embeddings_cache:
            embeddings_file = output_manager.get_output_path('json', "semantic_embeddings.pkl")
            with open(embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            print(f"💾 Embeddings cache saved to: {embeddings_file}")
        
        return results_file
    
    def _analyze_control_methodology(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze methodology for control texts using Phase 2 methodology extractor
        """
        try:
            # Dynamic import to handle missing spaCy dependencies gracefully
            from methodology_extractor import MethodologyExtractor
            
            print(f"🔧 Running Phase 2 methodology analysis on {len(texts)} texts...")
            
            # Initialize methodology extractor
            extractor = MethodologyExtractor()
            
            # Analyze all texts
            methodology_results = extractor.analyze_multiple_texts(texts)
            
            # Extract key insights for semantic analysis integration
            comparative = methodology_results['comparative_analysis']
            
            # Enhanced methodology classification
            enhanced_classification = {
                'dominant_methodology': max(comparative['methodology_distribution'].items(), key=lambda x: x[1])[0] if comparative['methodology_distribution'] else 'unknown',
                'methodology_consistency': self._assess_methodology_consistency(methodology_results['individual_results']),
                'evidence_diversity': len(comparative['evidence_type_frequency']),
                'testing_rigor_consistency': self._assess_rigor_consistency(methodology_results['individual_results']),
                'automation_readiness': comparative['automation_potential']['mean_feasibility'],
                
                # Detailed breakdown
                'methodology_distribution': comparative['methodology_distribution'],
                'evidence_type_frequency': comparative['evidence_type_frequency'],
                'rigor_distribution': comparative['rigor_distribution'],
                'complexity_analysis': comparative['complexity_analysis'],
                
                # Individual analysis
                'individual_methodologies': [
                    {
                        'text_preview': result['original_text'][:100] + "..." if len(result['original_text']) > 100 else result['original_text'],
                        'methodology_type': result['methodology_type']['primary_type'],
                        'evidence_types': result['evidence_types']['types_found'],
                        'rigor_level': result['rigor_assessment']['rigor_level'],
                        'automation_feasibility': result['automation_feasibility']['feasibility_score'],
                        'complexity_score': result['complexity_score']
                    }
                    for result in methodology_results['individual_results']
                ]
            }
            
            return enhanced_classification
            
        except ImportError:
            print("⚠️  Phase 2 methodology extractor not available (spaCy dependency)")
            return {'error': 'methodology_extractor_unavailable', 'phase_1_only': True}
        except Exception as e:
            print(f"❌ Phase 2 methodology analysis failed: {e}")
            return {'error': str(e)}
    
    def _assess_methodology_consistency(self, individual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess consistency of methodologies across texts"""
        
        methodology_types = [r['methodology_type']['primary_type'] for r in individual_results if r['methodology_type']['primary_type'] != 'unknown']
        
        if not methodology_types:
            return {'consistency_level': 'unknown', 'consistency_score': 0}
        
        # Calculate consistency score based on methodology type distribution
        from collections import Counter
        type_counts = Counter(methodology_types)
        most_common_count = type_counts.most_common(1)[0][1] if type_counts else 0
        consistency_score = most_common_count / len(methodology_types) if methodology_types else 0
        
        if consistency_score >= 0.8:
            consistency_level = 'high'
        elif consistency_score >= 0.6:
            consistency_level = 'moderate'
        else:
            consistency_level = 'low'
        
        return {
            'consistency_level': consistency_level,
            'consistency_score': float(consistency_score),
            'dominant_type': type_counts.most_common(1)[0][0] if type_counts else 'unknown',
            'type_diversity': len(type_counts)
        }
    
    def _assess_rigor_consistency(self, individual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess consistency of testing rigor across texts"""
        
        rigor_levels = [r['rigor_assessment']['rigor_level'] for r in individual_results if r['rigor_assessment']['rigor_level'] != 'unknown']
        
        if not rigor_levels:
            return {'consistency_level': 'unknown', 'consistency_score': 0}
        
        # Calculate rigor consistency
        from collections import Counter
        rigor_counts = Counter(rigor_levels)
        most_common_count = rigor_counts.most_common(1)[0][1] if rigor_counts else 0
        consistency_score = most_common_count / len(rigor_levels) if rigor_levels else 0
        
        if consistency_score >= 0.8:
            consistency_level = 'high'
        elif consistency_score >= 0.6:
            consistency_level = 'moderate'
        else:
            consistency_level = 'low'
        
        return {
            'consistency_level': consistency_level,
            'consistency_score': float(consistency_score),
            'dominant_rigor': rigor_counts.most_common(1)[0][0] if rigor_counts else 'unknown',
            'rigor_diversity': len(rigor_counts)
        }

def main():
    """Main execution function for standalone usage"""
    print("🧠 SOC2 Semantic Analyzer - Phase 1 Implementation")
    print("=" * 60)
    
    try:
        # Initialize analyzer
        analyzer = SemanticAnalyzer()
        
        # Load variance data
        variance_file = "data/processed/latest/control_variance_report.json"
        if not os.path.exists(variance_file):
            print(f"❌ Variance report not found: {variance_file}")
            print("   Please run control_variance_analyzer.py first")
            return
        
        analyzer.load_variance_data(variance_file)
        
        # Run semantic analysis
        results = analyzer.analyze_semantic_similarity()
        
        # Save results
        output_file = analyzer.save_results()
        
        # Print summary
        metadata = results['analysis_metadata']
        global_summary = results['global_summary']
        
        print(f"\n📊 SEMANTIC ANALYSIS SUMMARY:")
        print("=" * 50)
        print(f"🎯 Controls analyzed: {metadata['total_controls_analyzed']}")
        print(f"🤖 Model used: {metadata['model_name']}")
        print(f"📈 Total comparisons: {global_summary['total_pairwise_comparisons']}")
        
        similarity_stats = global_summary['overall_similarity_stats']
        print(f"📊 Average similarity: {similarity_stats['mean']:.3f}")
        print(f"📊 Similarity range: {similarity_stats['min']:.3f} - {similarity_stats['max']:.3f}")
        
        classification_dist = global_summary['classification_distribution']
        print(f"\n🏷️ Classification Distribution:")
        for category, count in classification_dist.items():
            percentage = (count / global_summary['total_pairwise_comparisons']) * 100 if global_summary['total_pairwise_comparisons'] > 0 else 0
            print(f"   {category.title()}: {count} ({percentage:.1f}%)")
        
        automation = global_summary['automation_candidates']
        print(f"\n🤖 Automation Potential:")
        print(f"   High similarity (template ready): {automation['high_similarity_controls']} controls")
        print(f"   Medium similarity (minor customization): {automation['medium_similarity_controls']} controls")
        print(f"   Low similarity (manual approach): {automation['low_similarity_controls']} controls")
        
        print(f"\n✅ Semantic analysis complete!")
        print(f"📁 Detailed results: {output_file}")
        print(f"💡 Next: Run methodology_extractor.py for Phase 2")
        
    except Exception as e:
        print(f"❌ Semantic analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()