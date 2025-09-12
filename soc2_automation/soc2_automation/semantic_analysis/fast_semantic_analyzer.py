#!/usr/bin/env python3
"""
Fast SOC2 Semantic Analyzer

Optimized version with smaller batches and lighter processing for performance.
"""

import json
import os
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import sys
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager
except ImportError:
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from output_manager import get_output_manager

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️  Warning: sentence-transformers or scikit-learn not available. Please run:")
    print("   pip install sentence-transformers scikit-learn")

class FastSemanticAnalyzer:
    """Lightweight semantic analyzer optimized for performance"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', batch_size: int = 8, max_controls: int = 50):
        """
        Initialize fast semantic analyzer
        
        Args:
            model_name: Sentence-BERT model name
            batch_size: Small batch size for memory efficiency
            max_controls: Limit analysis to top N controls for speed
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available.")
        
        self.model_name = model_name
        self.model = None
        self.batch_size = batch_size
        self.max_controls = max_controls
        
        # Data storage
        self.variance_data = None
        self.semantic_results = {}
        
        # Similarity thresholds
        self.similarity_thresholds = {
            'high': 0.8,    # Style differences only
            'medium': 0.5,  # Minor methodology differences  
            'low': 0.0      # Major methodology differences
        }
        
        # Output manager
        self.output_manager = get_output_manager()
    
    def _load_model(self):
        """Load lightweight Sentence-BERT model"""
        if self.model is None:
            print(f"🤖 Loading lightweight model: {self.model_name}")
            try:
                self.model = SentenceTransformer(self.model_name)
                # Disable gradients for inference only
                self.model.eval()
                print("✅ Model loaded and optimized for inference")
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                raise
    
    def load_variance_data(self, variance_file: str = None):
        """Load control variance data"""
        if variance_file is None:
            # Use latest run from output manager
            latest_run = self.output_manager.get_latest_run()
            if latest_run:
                variance_file = os.path.join(latest_run, "json", "control_variance_report.json")
            else:
                variance_file = "data/processed/latest/control_variance_report.json"
        
        print(f"📊 Loading variance data from: {variance_file}")
        
        if not os.path.exists(variance_file):
            raise FileNotFoundError(f"Variance report not found: {variance_file}")
        
        with open(variance_file, 'r', encoding='utf-8') as f:
            self.variance_data = json.load(f)
        
        total_controls = len(self.variance_data.get('variance_analysis', {}))
        print(f"📋 Loaded {total_controls} controls")
        
        # Limit to top controls for performance
        if total_controls > self.max_controls:
            print(f"⚡ Limiting analysis to top {self.max_controls} controls for performance")
    
    def _clean_text(self, text: str) -> str:
        """Simple text cleaning"""
        if not text:
            return ""
        return text.lower().strip()
    
    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings in small batches"""
        self._load_model()
        
        all_embeddings = []
        cleaned_texts = [self._clean_text(text) for text in texts]
        
        # Process in small batches
        for i in range(0, len(cleaned_texts), self.batch_size):
            batch = cleaned_texts[i:i + self.batch_size]
            print(f"🧠 Processing batch {i//self.batch_size + 1}/{(len(cleaned_texts) + self.batch_size - 1)//self.batch_size} ({len(batch)} texts)")
            
            try:
                batch_embeddings = self.model.encode(batch, convert_to_tensor=False, show_progress_bar=False)
                all_embeddings.append(batch_embeddings)
            except Exception as e:
                print(f"❌ Error processing batch: {e}")
                # Fallback: process individually
                for text in batch:
                    try:
                        emb = self.model.encode([text], convert_to_tensor=False, show_progress_bar=False)
                        all_embeddings.append(emb)
                    except:
                        # Use zero vector as fallback
                        all_embeddings.append(np.zeros((1, 384)))
        
        return np.vstack(all_embeddings)
    
    def analyze_control_semantic_similarity(self, control_key: str, control_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze semantic similarity for a single control"""
        company_tests = control_data.get('company_tests', {})
        companies = list(company_tests.keys())
        
        if len(companies) < 2:
            return {
                'control_key': control_key,
                'companies': companies,
                'similarity_matrix': [],
                'average_similarity': 0.0,
                'classification': 'insufficient_data'
            }
        
        # Collect all test texts
        all_texts = []
        text_to_company = {}
        
        for company, tests in company_tests.items():
            if isinstance(tests, list) and tests:
                # Take first test only for speed
                test_text = tests[0] if tests else ""
                all_texts.append(test_text)
                text_to_company[len(all_texts) - 1] = company
        
        if len(all_texts) < 2:
            return {
                'control_key': control_key,
                'companies': companies,
                'similarity_matrix': [],
                'average_similarity': 0.0,
                'classification': 'insufficient_data'
            }
        
        # Generate embeddings
        try:
            embeddings = self.generate_embeddings_batch(all_texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Calculate average similarity (excluding diagonal)
            n = len(similarity_matrix)
            if n > 1:
                upper_triangle = similarity_matrix[np.triu_indices(n, k=1)]
                avg_similarity = float(np.mean(upper_triangle))
            else:
                avg_similarity = 1.0
            
            # Classify based on similarity
            if avg_similarity >= self.similarity_thresholds['high']:
                classification = 'high_similarity'
            elif avg_similarity >= self.similarity_thresholds['medium']:
                classification = 'medium_similarity'
            else:
                classification = 'low_similarity'
            
            return {
                'control_key': control_key,
                'companies': [text_to_company[i] for i in range(len(all_texts))],
                'similarity_matrix': similarity_matrix.tolist(),
                'average_similarity': avg_similarity,
                'classification': classification,
                'text_count': len(all_texts)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {control_key}: {e}")
            return {
                'control_key': control_key,
                'companies': companies,
                'similarity_matrix': [],
                'average_similarity': 0.0,
                'classification': 'analysis_error',
                'error': str(e)
            }
    
    def analyze_semantic_similarity(self) -> Dict[str, Any]:
        """Run fast semantic similarity analysis"""
        if not self.variance_data:
            raise ValueError("No variance data loaded. Call load_variance_data() first.")
        
        print("🧠 Starting fast semantic similarity analysis...")
        print(f"⚡ Configuration: batch_size={self.batch_size}, max_controls={self.max_controls}")
        
        variance_analysis = self.variance_data.get('variance_analysis', {})
        
        # Limit to top controls by coverage for performance
        controls_by_coverage = sorted(
            variance_analysis.items(),
            key=lambda x: x[1].get('total_companies_with_control', 0),
            reverse=True
        )
        
        # Take top N controls
        top_controls = dict(controls_by_coverage[:self.max_controls])
        
        print(f"🎯 Analyzing top {len(top_controls)} controls (out of {len(variance_analysis)} total)")
        
        controls_analysis = {}
        
        for i, (control_key, control_data) in enumerate(top_controls.items(), 1):
            print(f"📊 Processing {i}/{len(top_controls)}: {control_key[:60]}...")
            
            try:
                result = self.analyze_control_semantic_similarity(control_key, control_data)
                controls_analysis[control_key] = result
                
                # Show progress for long-running analysis
                if i % 10 == 0:
                    print(f"✅ Completed {i}/{len(top_controls)} controls")
                    
            except KeyboardInterrupt:
                print(f"\n⚠️  Analysis interrupted at control {i}")
                break
            except Exception as e:
                print(f"❌ Error processing {control_key}: {e}")
                continue
        
        # Generate summary statistics
        similarities = [
            result.get('average_similarity', 0) 
            for result in controls_analysis.values() 
            if result.get('average_similarity', 0) > 0
        ]
        
        classifications = {}
        for result in controls_analysis.values():
            classification = result.get('classification', 'unknown')
            classifications[classification] = classifications.get(classification, 0) + 1
        
        # Compile results
        results = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model_name,
                'total_controls_analyzed': len(controls_analysis),
                'batch_size': self.batch_size,
                'max_controls_limit': self.max_controls,
                'average_similarity_overall': float(np.mean(similarities)) if similarities else 0.0,
                'classification_distribution': classifications
            },
            'controls_analysis': controls_analysis,
            'similarity_thresholds': self.similarity_thresholds
        }
        
        # Save results
        self.save_results(results)
        
        print(f"\n✅ Fast semantic analysis complete!")
        print(f"📊 Analyzed {len(controls_analysis)} controls")
        print(f"📈 Average similarity: {results['analysis_metadata']['average_similarity_overall']:.3f}")
        print(f"📋 Classifications: {classifications}")
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """Save semantic analysis results"""
        output_file = self.output_manager.get_output_path('json', 'semantic_analysis_results.json')
        
        # Convert numpy types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        results_clean = convert_numpy(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_clean, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")

def main():
    """Main execution function"""
    analyzer = FastSemanticAnalyzer(batch_size=4, max_controls=30)  # Very conservative settings
    
    try:
        # Use latest available data
        variance_file = "data/outputs/20250911_160524/json/control_variance_report.json"
        analyzer.load_variance_data(variance_file)
        results = analyzer.analyze_semantic_similarity()
        
        print(f"\n🎯 Fast semantic analysis complete!")
        print(f"📁 Results saved to organized output directory")
        print(f"🔍 Key insights:")
        
        metadata = results.get('analysis_metadata', {})
        print(f"   • Controls analyzed: {metadata.get('total_controls_analyzed', 0)}")
        print(f"   • Average similarity: {metadata.get('average_similarity_overall', 0):.1%}")
        
        classifications = metadata.get('classification_distribution', {})
        for classification, count in classifications.items():
            print(f"   • {classification.replace('_', ' ').title()}: {count} controls")
            
    except Exception as e:
        print(f"❌ Error running semantic analysis: {e}")
        print("💡 Try reducing batch_size or max_controls in the script")

if __name__ == "__main__":
    main()