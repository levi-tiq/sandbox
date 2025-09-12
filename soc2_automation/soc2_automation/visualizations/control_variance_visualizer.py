#!/usr/bin/env python3
"""
SOC2 Control Variance Visualizer

Creates comprehensive data visualizations from control variance analysis.
Shows patterns in control coverage, language variance, and company differences.

Usage:
    python3 control_variance_visualizer.py
    
Generates:
    - Variance distribution charts
    - Company coverage heatmaps
    - Control family analysis
    - Language pattern visualizations
    - Missing control analysis
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import networkx as nx
from matplotlib.patches import Rectangle
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
import re
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

class ControlVarianceVisualizer:
    """
    Create visualizations for control variance analysis
    """
    
    def __init__(self, variance_report_path: str = None):
        # Use output manager to find latest data
        if variance_report_path is None:
            output_manager = get_output_manager()
            latest_run = output_manager.get_latest_run()
            if latest_run:
                self.variance_report_path = os.path.join(latest_run, "json", "control_variance_report.json")
            else:
                # Fallback to old structure
                self.variance_report_path = "data/processed/latest/control_variance_report.json"
        else:
            self.variance_report_path = variance_report_path
        
        self.data = None
        self.companies = []
        self.controls_df = None
        
        # Phase 4: Semantic analysis data
        self.semantic_data = None
        self.difference_classification_data = None
        
        # Output manager for saving visualizations
        self.output_manager = get_output_manager()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        self.load_data()
    
    def load_data(self):
        """Load the variance report data and semantic analysis results"""
        try:
            with open(self.variance_report_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.companies = self.data.get('analysis_summary', {}).get('companies_analyzed', [])
            
            print(f"✅ Loaded variance data: {len(self.data.get('variance_analysis', {}))} controls across {len(self.companies)} companies")
            
            # Load semantic analysis data (Phase 4)
            self._load_semantic_data()
            
            # Convert to DataFrame for easier analysis
            self._create_dataframe()
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    
    def _load_semantic_data(self):
        """Load semantic analysis and difference classification data"""
        # Try to load from latest output run first
        latest_run = self.output_manager.get_latest_run()
        
        # Load semantic analysis results
        if latest_run:
            semantic_path = os.path.join(latest_run, "json", "semantic_analysis_results.json")
        else:
            semantic_path = "data/processed/latest/semantic_analysis/semantic_analysis_results.json"
            
        try:
            with open(semantic_path, 'r', encoding='utf-8') as f:
                self.semantic_data = json.load(f)
            print(f"✅ Loaded semantic analysis data: {self.semantic_data.get('analysis_metadata', {}).get('total_controls_analyzed', 0)} controls")
        except Exception as e:
            print(f"⚠️  Semantic analysis data not available: {e}")
        
        # Load difference classification results  
        if latest_run:
            difference_path = os.path.join(latest_run, "json", "difference_classification_results.json")
        else:
            difference_path = "data/processed/latest/semantic_analysis/difference_classification_results.json"
            
        try:
            with open(difference_path, 'r', encoding='utf-8') as f:
                self.difference_classification_data = json.load(f)
            classification_metadata = self.difference_classification_data.get('classification_metadata', {})
            print(f"✅ Loaded difference classification data: {classification_metadata.get('total_controls_analyzed', 0)} controls")
        except Exception as e:
            print(f"⚠️  Difference classification data not available: {e}")
    
    def _save_visualization(self, filename: str, dpi: int = 300):
        """Helper method to save visualizations to organized output directory"""
        output_path = self.output_manager.get_output_path('visuals', filename)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        print(f"📊 Saved: {output_path}")
        return output_path
    
    def _save_html_visualization(self, fig, filename: str):
        """Helper method to save HTML visualizations"""
        output_path = self.output_manager.get_output_path('visuals', filename)
        fig.write_html(output_path)
        print(f"🌟 Saved: {output_path}")
        return output_path
    
    def _create_dataframe(self):
        """Convert variance data to pandas DataFrame"""
        rows = []
        
        for key, control_data in self.data.get('variance_analysis', {}).items():
            metrics = control_data.get('variance_metrics', {})
            
            # Extract control family (CC1, CC2, A1, etc.)
            control_id = control_data.get('control_id', '')
            control_family = re.match(r'^([A-Z]+\d+)', control_id)
            control_family = control_family.group(1) if control_family else 'OTHER'
            
            row = {
                'key': key,
                'control_id': control_id,
                'control_family': control_family,
                'control_name': control_data.get('control_name', ''),
                'companies_with_control': control_data.get('total_companies_with_control', 0),
                'missing_from_count': len(control_data.get('missing_from_companies', [])),
                'unique_test_texts': metrics.get('unique_test_texts', 0),
                'total_test_instances': metrics.get('total_test_instances', 0),
                'variance_ratio': metrics.get('unique_test_texts', 0) / max(metrics.get('total_test_instances', 1), 1),
                'avg_test_length': metrics.get('avg_test_length', 0),
                'avg_word_count': metrics.get('avg_word_count', 0),
                'coverage_ratio': control_data.get('total_companies_with_control', 0) / len(self.companies)
            }
            
            rows.append(row)
        
        self.controls_df = pd.DataFrame(rows)
        print(f"📊 Created DataFrame: {len(self.controls_df)} controls with {len(self.controls_df.columns)} attributes")
    
    def create_variance_distribution_plot(self):
        """Create variance distribution visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('SOC2 Control Variance Distribution Analysis', fontsize=16, fontweight='bold')
        
        # 1. Variance Ratio Distribution
        ax1.hist(self.controls_df['variance_ratio'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Variance Ratio (Unique Tests / Total Tests)')
        ax1.set_ylabel('Number of Controls')
        ax1.set_title('Distribution of Language Variance Ratios')
        ax1.axvline(self.controls_df['variance_ratio'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {self.controls_df["variance_ratio"].mean():.2f}')
        ax1.legend()
        
        # 2. Company Coverage Distribution
        coverage_counts = self.controls_df['companies_with_control'].value_counts().sort_index()
        ax2.bar(coverage_counts.index, coverage_counts.values, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_xlabel('Number of Companies with Control')
        ax2.set_ylabel('Number of Controls')
        ax2.set_title('Control Coverage Across Companies')
        
        # 3. Variance vs Coverage Scatter
        scatter = ax3.scatter(self.controls_df['coverage_ratio'], self.controls_df['variance_ratio'], 
                            alpha=0.6, c=self.controls_df['avg_word_count'], cmap='viridis')
        ax3.set_xlabel('Coverage Ratio (Companies with Control / Total Companies)')
        ax3.set_ylabel('Variance Ratio (Unique Tests / Total Tests)')
        ax3.set_title('Variance vs Coverage (Color = Avg Word Count)')
        plt.colorbar(scatter, ax=ax3, label='Average Word Count')
        
        # 4. Control Family Distribution
        family_counts = self.controls_df['control_family'].value_counts()
        ax4.pie(family_counts.values, labels=family_counts.index, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Distribution by Control Family')
        
        plt.tight_layout()
        self._save_visualization('control_variance_distribution.png')
        
        return fig
    
    def create_company_coverage_heatmap(self):
        """Create heatmap showing which companies have which controls"""
        print("🔥 Creating company coverage heatmap...")
        
        # Create a matrix: controls x companies
        control_keys = list(self.data.get('variance_analysis', {}).keys())[:50]  # Top 50 for readability
        
        matrix_data = []
        control_labels = []
        
        for key in control_keys:
            control_data = self.data['variance_analysis'][key]
            control_id = control_data['control_id']
            control_name = control_data['control_name'][:30] + "..." if len(control_data['control_name']) > 30 else control_data['control_name']
            
            control_labels.append(f"{control_id}: {control_name}")
            
            row = []
            for company in self.companies:
                # Check if company has this control
                has_control = company in control_data.get('company_tests', {})
                row.append(1 if has_control else 0)
            
            matrix_data.append(row)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 20))
        
        heatmap = sns.heatmap(matrix_data, 
                             xticklabels=self.companies,
                             yticklabels=control_labels,
                             cmap='RdYlBu_r',
                             cbar_kws={'label': 'Control Present'},
                             ax=ax)
        
        ax.set_title('Company-Control Coverage Matrix (Top 50 Controls)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Companies', fontsize=12)
        ax.set_ylabel('Controls', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0, fontsize=8)
        plt.tight_layout()
        self._save_visualization('company_coverage_heatmap.png')
        
        return fig
    
    def create_control_family_analysis(self):
        """Analyze patterns by control family (CC1, CC2, A1, etc.)"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Control Family Analysis', fontsize=16, fontweight='bold')
        
        # 1. Average variance by control family
        family_variance = self.controls_df.groupby('control_family')['variance_ratio'].mean().sort_values(ascending=False)
        ax1.bar(family_variance.index, family_variance.values, alpha=0.7, color='coral')
        ax1.set_xlabel('Control Family')
        ax1.set_ylabel('Average Variance Ratio')
        ax1.set_title('Average Language Variance by Control Family')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Coverage by control family
        family_coverage = self.controls_df.groupby('control_family')['coverage_ratio'].mean().sort_values(ascending=False)
        ax2.bar(family_coverage.index, family_coverage.values, alpha=0.7, color='lightblue')
        ax2.set_xlabel('Control Family')
        ax2.set_ylabel('Average Coverage Ratio')
        ax2.set_title('Average Coverage by Control Family')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Control count by family
        family_counts = self.controls_df['control_family'].value_counts()
        ax3.bar(family_counts.index, family_counts.values, alpha=0.7, color='lightgreen')
        ax3.set_xlabel('Control Family')
        ax3.set_ylabel('Number of Controls')
        ax3.set_title('Control Count by Family')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Variance vs Coverage by Family (box plot)
        families_to_plot = self.controls_df['control_family'].value_counts().head(6).index
        df_filtered = self.controls_df[self.controls_df['control_family'].isin(families_to_plot)]
        
        sns.boxplot(data=df_filtered, x='control_family', y='variance_ratio', ax=ax4)
        ax4.set_xlabel('Control Family')
        ax4.set_ylabel('Variance Ratio')
        ax4.set_title('Variance Distribution by Control Family')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        self._save_visualization('control_family_analysis.png')
        
        return fig
    
    def create_interactive_scatter_plot(self):
        """Create interactive plotly scatter plot"""
        print("🌟 Creating interactive scatter plot...")
        
        # Prepare data for plotly
        df = self.controls_df.copy()
        df['hover_text'] = (df['control_id'] + '<br>' + 
                           df['control_name'].str[:50] + '<br>' +
                           'Companies: ' + df['companies_with_control'].astype(str) + '<br>' +
                           'Variance: ' + (df['variance_ratio'] * 100).round(1).astype(str) + '%')
        
        # Create scatter plot
        fig = px.scatter(df, 
                        x='coverage_ratio',
                        y='variance_ratio', 
                        size='avg_word_count',
                        color='control_family',
                        hover_data=['control_id', 'control_name'],
                        title='SOC2 Control Variance vs Coverage Analysis',
                        labels={
                            'coverage_ratio': 'Coverage Ratio (Companies with Control / Total)',
                            'variance_ratio': 'Variance Ratio (Unique Tests / Total Tests)',
                            'control_family': 'Control Family'
                        })
        
        fig.update_layout(
            width=1000,
            height=600,
            showlegend=True
        )
        
        self._save_html_visualization(fig, 'interactive_control_analysis.html')
        
        return fig
    
    def create_missing_controls_analysis(self):
        """Analyze patterns in missing controls"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Missing Controls Analysis', fontsize=16, fontweight='bold')
        
        # 1. Companies with most missing controls
        company_missing_counts = defaultdict(int)
        
        for control_data in self.data.get('variance_analysis', {}).values():
            for missing_company in control_data.get('missing_from_companies', []):
                company_missing_counts[missing_company] += 1
        
        if company_missing_counts:
            companies_sorted = sorted(company_missing_counts.items(), key=lambda x: x[1], reverse=True)
            companies, missing_counts = zip(*companies_sorted)
            
            ax1.barh(companies, missing_counts, alpha=0.7, color='salmon')
            ax1.set_xlabel('Number of Missing Controls')
            ax1.set_ylabel('Companies')
            ax1.set_title('Missing Controls by Company')
        
        # 2. Controls missing from most companies
        controls_by_missing = self.controls_df.sort_values('missing_from_count', ascending=False).head(15)
        
        control_labels = [(row['control_id'] + ': ' + row['control_name'][:30] + '...') 
                         if len(row['control_name']) > 30 
                         else (row['control_id'] + ': ' + row['control_name'])
                         for _, row in controls_by_missing.iterrows()]
        
        ax2.barh(range(len(control_labels)), controls_by_missing['missing_from_count'], alpha=0.7, color='lightcoral')
        ax2.set_yticks(range(len(control_labels)))
        ax2.set_yticklabels(control_labels, fontsize=8)
        ax2.set_xlabel('Number of Companies Missing This Control')
        ax2.set_title('Most Frequently Missing Controls')
        
        plt.tight_layout()
        self._save_visualization('missing_controls_analysis.png')
        
        return fig
    
    def create_language_pattern_wordcloud(self):
        """Create word cloud of common test language patterns"""
        try:
            from wordcloud import WordCloud
            
            # Extract all test texts
            all_test_texts = []
            for control_data in self.data.get('variance_analysis', {}).values():
                for company_tests in control_data.get('company_tests', {}).values():
                    if isinstance(company_tests, list):
                        all_test_texts.extend(company_tests)
            
            # Combine all text
            combined_text = ' '.join(all_test_texts)
            
            # Create word cloud
            wordcloud = WordCloud(
                width=1200, 
                height=600, 
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(combined_text)
            
            fig, ax = plt.subplots(figsize=(15, 8))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title('Common Words in SOC2 Test Language', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            self._save_visualization('test_language_wordcloud.png')
            
            return fig
            
        except ImportError:
            print("⚠️ WordCloud not available. Install with: pip install wordcloud")
            return None
    
    def generate_summary_dashboard(self):
        """Generate a comprehensive summary dashboard"""
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # Main title
        fig.suptitle('SOC2 Control Variance Analysis Dashboard', fontsize=20, fontweight='bold', y=0.95)
        
        # 1. Key Metrics (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        metrics_text = f"""
        Total Controls: {len(self.controls_df)}
        Companies: {len(self.companies)}
        Avg Variance: {self.controls_df['variance_ratio'].mean():.1%}
        Avg Coverage: {self.controls_df['coverage_ratio'].mean():.1%}
        High Variance (>80%): {len(self.controls_df[self.controls_df['variance_ratio'] > 0.8])}
        """
        ax1.text(0.1, 0.5, metrics_text, fontsize=12, verticalalignment='center', 
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title('Key Metrics', fontweight='bold')
        
        # 2. Variance Distribution (top middle-right)
        ax2 = fig.add_subplot(gs[0, 1:3])
        ax2.hist(self.controls_df['variance_ratio'], bins=15, alpha=0.7, color='skyblue')
        ax2.set_xlabel('Variance Ratio')
        ax2.set_ylabel('Count')
        ax2.set_title('Language Variance Distribution', fontweight='bold')
        ax2.axvline(self.controls_df['variance_ratio'].mean(), color='red', linestyle='--')
        
        # 3. Top High Variance Controls (top right)
        ax3 = fig.add_subplot(gs[0, 3])
        high_var = self.controls_df.nlargest(8, 'variance_ratio')
        y_pos = range(len(high_var))
        ax3.barh(y_pos, high_var['variance_ratio'], alpha=0.7, color='coral')
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels([f"{row['control_id']}" for _, row in high_var.iterrows()], fontsize=8)
        ax3.set_xlabel('Variance Ratio')
        ax3.set_title('Highest Variance Controls', fontweight='bold')
        
        # 4. Control Family Analysis (middle row)
        ax4 = fig.add_subplot(gs[1, :2])
        family_variance = self.controls_df.groupby('control_family')['variance_ratio'].mean().sort_values(ascending=False)
        ax4.bar(family_variance.index, family_variance.values, alpha=0.7, color='lightgreen')
        ax4.set_xlabel('Control Family')
        ax4.set_ylabel('Avg Variance Ratio')
        ax4.set_title('Average Variance by Control Family', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        
        # 5. Coverage Analysis (middle right)
        ax5 = fig.add_subplot(gs[1, 2:])
        coverage_counts = self.controls_df['companies_with_control'].value_counts().sort_index()
        ax5.bar(coverage_counts.index, coverage_counts.values, alpha=0.7, color='gold')
        ax5.set_xlabel('Companies with Control')
        ax5.set_ylabel('Number of Controls')
        ax5.set_title('Control Coverage Distribution', fontweight='bold')
        
        # 6. Variance vs Coverage Scatter (bottom)
        ax6 = fig.add_subplot(gs[2, :])
        scatter = ax6.scatter(self.controls_df['coverage_ratio'], self.controls_df['variance_ratio'],
                             alpha=0.6, c=self.controls_df['avg_word_count'], cmap='viridis')
        ax6.set_xlabel('Coverage Ratio (Companies with Control / Total)')
        ax6.set_ylabel('Variance Ratio (Unique Tests / Total Tests)')
        ax6.set_title('Control Variance vs Coverage Analysis', fontweight='bold')
        
        # Add quadrant labels
        ax6.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
        ax6.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)
        ax6.text(0.25, 0.75, 'Low Coverage\nHigh Variance', ha='center', fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="red", alpha=0.3))
        ax6.text(0.75, 0.75, 'High Coverage\nHigh Variance', ha='center', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="orange", alpha=0.3))
        ax6.text(0.25, 0.25, 'Low Coverage\nLow Variance', ha='center', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3))
        ax6.text(0.75, 0.25, 'High Coverage\nLow Variance', ha='center', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.3))
        
        plt.colorbar(scatter, ax=ax6, label='Avg Word Count')
        
        self._save_visualization('soc2_dashboard.png')
        
        return fig
    
    # =============================================================================
    # Phase 4: Semantic Analysis Visualizations
    # =============================================================================
    
    def create_semantic_similarity_heatmap(self, control_key: str = None):
        """Create semantic similarity heatmap for a specific control or overall"""
        if not self.semantic_data:
            print("⚠️  No semantic analysis data available")
            return None
        
        print("🧠 Creating semantic similarity heatmaps...")
        
        if control_key:
            # Single control heatmap
            return self._create_single_control_heatmap(control_key)
        else:
            # Overall semantic similarity summary heatmap
            return self._create_overall_semantic_heatmap()
    
    def _create_single_control_heatmap(self, control_key: str):
        """Create heatmap for a single control's semantic similarities"""
        controls_analysis = self.semantic_data.get('controls_analysis', {})
        
        if control_key not in controls_analysis:
            print(f"❌ Control {control_key} not found in semantic analysis")
            return None
        
        control_data = controls_analysis[control_key]
        similarity_matrix = control_data.get('similarity_matrix', [])
        companies = control_data.get('companies', [])
        
        if not similarity_matrix or not companies:
            print(f"❌ No similarity data for control {control_key}")
            return None
        
        # Convert to numpy array for easier handling
        similarity_array = np.array(similarity_matrix)
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        mask = np.triu(np.ones_like(similarity_array, dtype=bool))  # Mask upper triangle
        
        sns.heatmap(similarity_array, 
                   mask=mask,
                   annot=True, 
                   fmt='.3f',
                   xticklabels=companies,
                   yticklabels=companies,
                   cmap='RdYlBu_r',
                   vmin=0, vmax=1,
                   cbar_kws={'label': 'Semantic Similarity Score'})
        
        plt.title(f'Semantic Similarity Heatmap\n{control_key}', fontsize=14, fontweight='bold')
        plt.xlabel('Company', fontweight='bold')
        plt.ylabel('Company', fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        filename = f'semantic_heatmap_{control_key.replace("||", "_").replace("/", "_")}.png'
        plt.tight_layout()
        self._save_visualization(filename)
        plt.close()
        
        return filename
    
    def _create_overall_semantic_heatmap(self):
        """Create overall semantic similarity summary heatmap"""
        controls_analysis = self.semantic_data.get('controls_analysis', {})
        
        # Calculate average semantic similarity per control
        control_similarities = {}
        
        for control_key, control_data in controls_analysis.items():
            similarity_matrix = control_data.get('similarity_matrix', [])
            if similarity_matrix:
                # Calculate average similarity (excluding diagonal)
                similarity_array = np.array(similarity_matrix)
                n = len(similarity_array)
                if n > 1:
                    # Get upper triangle (excluding diagonal)
                    upper_triangle = similarity_array[np.triu_indices(n, k=1)]
                    avg_similarity = np.mean(upper_triangle)
                    control_similarities[control_key] = avg_similarity
        
        if not control_similarities:
            print("❌ No similarity data available")
            return None
        
        # Create summary visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left plot: Control similarity distribution
        similarities = list(control_similarities.values())
        control_names = [key.split('||')[1][:30] + '...' if '||' in key and len(key.split('||')[1]) > 30 
                        else key.split('||')[1] if '||' in key else key[:30] + '...' for key in control_similarities.keys()]
        
        # Sort by similarity for better visualization
        sorted_data = sorted(zip(control_names, similarities), key=lambda x: x[1], reverse=True)
        sorted_names, sorted_similarities = zip(*sorted_data)
        
        # Take top 20 for readability
        top_20_names = sorted_names[:20]
        top_20_similarities = sorted_similarities[:20]
        
        colors = ['red' if sim < 0.5 else 'orange' if sim < 0.7 else 'green' for sim in top_20_similarities]
        
        bars = ax1.barh(range(len(top_20_names)), top_20_similarities, color=colors, alpha=0.7)
        ax1.set_yticks(range(len(top_20_names)))
        ax1.set_yticklabels(top_20_names, fontsize=9)
        ax1.set_xlabel('Average Semantic Similarity', fontweight='bold')
        ax1.set_title('Top 20 Controls by Semantic Similarity', fontweight='bold')
        ax1.set_xlim(0, 1)
        
        # Add value labels on bars
        for i, (bar, sim) in enumerate(zip(bars, top_20_similarities)):
            ax1.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                    f'{sim:.3f}', va='center', fontsize=8)
        
        # Right plot: Similarity distribution histogram
        ax2.hist(similarities, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(np.mean(similarities), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(similarities):.3f}')
        ax2.axvline(0.5, color='orange', linestyle='--', alpha=0.7,
                   label='Low Similarity Threshold')
        ax2.axvline(0.7, color='green', linestyle='--', alpha=0.7,
                   label='High Similarity Threshold')
        
        ax2.set_xlabel('Average Semantic Similarity', fontweight='bold')
        ax2.set_ylabel('Number of Controls', fontweight='bold')
        ax2.set_title('Semantic Similarity Distribution', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self._save_visualization('semantic_similarity_summary.png')
        plt.close()
        
        return 'semantic_similarity_summary.png'
    
    def create_methodology_clustering_visualization(self):
        """Create methodology clustering visualizations"""
        if not self.difference_classification_data:
            print("⚠️  No difference classification data available")
            return None
        
        print("🔧 Creating methodology clustering visualizations...")
        
        control_profiles = self.difference_classification_data.get('control_profiles', {})
        
        if not control_profiles:
            print("❌ No control profiles available")
            return None
        
        # Extract data for clustering visualization
        control_names = []
        style_percentages = []
        methodology_percentages = []
        automation_feasibility = []
        standardization_opportunities = []
        
        for control_key, profile in control_profiles.items():
            control_name = control_key.split('||')[1] if '||' in control_key else control_key
            control_names.append(control_name[:30] + '...' if len(control_name) > 30 else control_name)
            style_percentages.append(profile.get('style_percentage', 0))
            methodology_percentages.append(profile.get('methodology_percentage', 0))
            automation_feasibility.append(profile.get('automation_feasibility', 'too_diverse'))
            standardization_opportunities.append(profile.get('standardization_opportunity', 'low'))
        
        # Create the clustering visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Style vs Methodology scatter plot
        colors = {'ready': 'green', 'needs_standardization': 'orange', 'too_diverse': 'red'}
        automation_colors = [colors.get(af, 'gray') for af in automation_feasibility]
        
        scatter = ax1.scatter(style_percentages, methodology_percentages, 
                            c=automation_colors, alpha=0.7, s=60)
        ax1.set_xlabel('Style Differences (%)', fontweight='bold')
        ax1.set_ylabel('Methodology Differences (%)', fontweight='bold')
        ax1.set_title('Style vs Methodology Differences\n(Color = Automation Feasibility)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add quadrant lines
        ax1.axhline(50, color='gray', linestyle='--', alpha=0.5)
        ax1.axvline(50, color='gray', linestyle='--', alpha=0.5)
        
        # Add legend
        for af, color in colors.items():
            ax1.scatter([], [], c=color, label=af.replace('_', ' ').title())
        ax1.legend(title='Automation Feasibility')
        
        # Plot 2: Automation feasibility distribution
        automation_counts = Counter(automation_feasibility)
        wedges, texts, autotexts = ax2.pie(automation_counts.values(), 
                                          labels=[af.replace('_', ' ').title() for af in automation_counts.keys()],
                                          colors=[colors.get(af, 'gray') for af in automation_counts.keys()],
                                          autopct='%1.1f%%',
                                          startangle=90)
        ax2.set_title('Automation Feasibility Distribution', fontweight='bold')
        
        # Plot 3: Standardization opportunities
        standardization_counts = Counter(standardization_opportunities)
        std_colors = {'high': 'darkgreen', 'medium': 'orange', 'low': 'red'}
        
        bars = ax3.bar(standardization_counts.keys(), standardization_counts.values(),
                      color=[std_colors.get(so, 'gray') for so in standardization_counts.keys()],
                      alpha=0.7)
        ax3.set_xlabel('Standardization Opportunity', fontweight='bold')
        ax3.set_ylabel('Number of Controls', fontweight='bold')
        ax3.set_title('Standardization Opportunities', fontweight='bold')
        
        # Add value labels on bars
        for bar, count in zip(bars, standardization_counts.values()):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        # Plot 4: Top controls for automation (style-heavy)
        # Get top 10 controls with highest style percentage and automation readiness
        automation_ready = [(name, style, method) for name, style, method, af in 
                           zip(control_names, style_percentages, methodology_percentages, automation_feasibility) 
                           if af == 'ready']
        
        if automation_ready:
            automation_ready.sort(key=lambda x: x[1], reverse=True)  # Sort by style percentage
            top_automation = automation_ready[:10]
            
            top_names, top_styles, top_methods = zip(*top_automation)
            
            y_pos = range(len(top_names))
            bars = ax4.barh(y_pos, top_styles, alpha=0.7, color='green', label='Style %')
            bars2 = ax4.barh(y_pos, top_methods, left=top_styles, alpha=0.7, color='red', label='Methodology %')
            
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(top_names, fontsize=9)
            ax4.set_xlabel('Percentage', fontweight='bold')
            ax4.set_title('Top Automation Candidates\n(Ready for Template Creation)', fontweight='bold')
            ax4.legend()
            ax4.set_xlim(0, 100)
        else:
            ax4.text(0.5, 0.5, 'No automation-ready controls found', 
                    ha='center', va='center', transform=ax4.transAxes, fontsize=12)
            ax4.set_title('Automation Candidates', fontweight='bold')
        
        plt.tight_layout()
        self._save_visualization('methodology_clustering_analysis.png')
        plt.close()
        
        return 'methodology_clustering_analysis.png'
    
    def create_semantic_vs_lexical_comparison(self):
        """Create semantic vs lexical comparison charts"""
        if not self.semantic_data or not self.difference_classification_data:
            print("⚠️  Incomplete data for semantic vs lexical comparison")
            return None
        
        print("📊 Creating semantic vs lexical comparison charts...")
        
        # Extract semantic and lexical data for comparison
        controls_analysis = self.semantic_data.get('controls_analysis', {})
        control_profiles = self.difference_classification_data.get('control_profiles', {})
        
        # Collect comparison data
        comparison_data = []
        
        for control_key in controls_analysis.keys():
            if control_key in control_profiles:
                semantic_data = controls_analysis[control_key]
                profile = control_profiles[control_key]
                
                # Calculate average semantic similarity
                similarity_matrix = semantic_data.get('similarity_matrix', [])
                if similarity_matrix:
                    similarity_array = np.array(similarity_matrix)
                    n = len(similarity_array)
                    if n > 1:
                        upper_triangle = similarity_array[np.triu_indices(n, k=1)]
                        avg_semantic_sim = np.mean(upper_triangle)
                    else:
                        avg_semantic_sim = 1.0
                else:
                    continue
                
                # Get variance data (lexical similarity proxy)
                variance_data = self.data.get('variance_analysis', {}).get(control_key, {})
                variance_metrics = variance_data.get('variance_metrics', {})
                
                # Calculate lexical similarity (inverse of variance)
                unique_tests = variance_metrics.get('unique_test_texts', 1)
                total_tests = variance_metrics.get('total_test_instances', 1)
                lexical_similarity = 1 - (unique_tests / max(total_tests, 1))
                
                comparison_data.append({
                    'control_key': control_key,
                    'control_name': control_key.split('||')[1] if '||' in control_key else control_key,
                    'semantic_similarity': avg_semantic_sim,
                    'lexical_similarity': lexical_similarity,
                    'style_percentage': profile.get('style_percentage', 0),
                    'methodology_percentage': profile.get('methodology_percentage', 0),
                    'automation_feasibility': profile.get('automation_feasibility', 'too_diverse')
                })
        
        if not comparison_data:
            print("❌ No comparison data available")
            return None
        
        # Create comparison visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        semantic_sims = [d['semantic_similarity'] for d in comparison_data]
        lexical_sims = [d['lexical_similarity'] for d in comparison_data]
        style_pcts = [d['style_percentage'] for d in comparison_data]
        automation_feasibility = [d['automation_feasibility'] for d in comparison_data]
        
        # Plot 1: Semantic vs Lexical scatter
        colors = {'ready': 'green', 'needs_standardization': 'orange', 'too_diverse': 'red'}
        plot_colors = [colors.get(af, 'gray') for af in automation_feasibility]
        
        scatter = ax1.scatter(lexical_sims, semantic_sims, c=plot_colors, alpha=0.7, s=60)
        ax1.set_xlabel('Lexical Similarity (Text-based)', fontweight='bold')
        ax1.set_ylabel('Semantic Similarity (Meaning-based)', fontweight='bold')
        ax1.set_title('Semantic vs Lexical Similarity Analysis', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add diagonal line (perfect correlation)
        min_val = min(min(lexical_sims), min(semantic_sims))
        max_val = max(max(lexical_sims), max(semantic_sims))
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Correlation')
        ax1.legend(title='Reference Line')
        
        # Add legend for colors
        for af, color in colors.items():
            ax1.scatter([], [], c=color, label=af.replace('_', ' ').title())
        ax1.legend(title='Automation Feasibility')
        
        # Plot 2: Difference between semantic and lexical
        differences = [sem - lex for sem, lex in zip(semantic_sims, lexical_sims)]
        
        ax2.hist(differences, bins=20, alpha=0.7, color='purple', edgecolor='black')
        ax2.axvline(0, color='red', linestyle='--', label='No Difference')
        ax2.axvline(np.mean(differences), color='green', linestyle='--', 
                   label=f'Mean Difference: {np.mean(differences):.3f}')
        ax2.set_xlabel('Semantic - Lexical Similarity', fontweight='bold')
        ax2.set_ylabel('Number of Controls', fontweight='bold')
        ax2.set_title('Distribution of Semantic vs Lexical Differences', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Style vs Methodology with similarity correlation
        scatter = ax3.scatter(style_pcts, [d['methodology_percentage'] for d in comparison_data],
                            c=semantic_sims, cmap='viridis', alpha=0.7, s=60)
        ax3.set_xlabel('Style Differences (%)', fontweight='bold')
        ax3.set_ylabel('Methodology Differences (%)', fontweight='bold')
        ax3.set_title('Style vs Methodology Differences\n(Color = Semantic Similarity)', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax3, label='Semantic Similarity')
        
        # Plot 4: Automation readiness analysis
        ready_controls = [d for d in comparison_data if d['automation_feasibility'] == 'ready']
        needs_std_controls = [d for d in comparison_data if d['automation_feasibility'] == 'needs_standardization']
        diverse_controls = [d for d in comparison_data if d['automation_feasibility'] == 'too_diverse']
        
        categories = ['Ready\n(Template)', 'Needs\nStandardization', 'Too Diverse\n(Manual)']
        sem_means = [
            np.mean([d['semantic_similarity'] for d in ready_controls]) if ready_controls else 0,
            np.mean([d['semantic_similarity'] for d in needs_std_controls]) if needs_std_controls else 0,
            np.mean([d['semantic_similarity'] for d in diverse_controls]) if diverse_controls else 0
        ]
        lex_means = [
            np.mean([d['lexical_similarity'] for d in ready_controls]) if ready_controls else 0,
            np.mean([d['lexical_similarity'] for d in needs_std_controls]) if needs_std_controls else 0,
            np.mean([d['lexical_similarity'] for d in diverse_controls]) if diverse_controls else 0
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax4.bar(x - width/2, sem_means, width, label='Semantic Similarity', alpha=0.7, color='blue')
        bars2 = ax4.bar(x + width/2, lex_means, width, label='Lexical Similarity', alpha=0.7, color='orange')
        
        ax4.set_xlabel('Automation Feasibility Category', fontweight='bold')
        ax4.set_ylabel('Average Similarity Score', fontweight='bold')
        ax4.set_title('Similarity Scores by Automation Category', fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(categories)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 1)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        self._save_visualization('semantic_vs_lexical_analysis.png')
        plt.close()
        
        return 'semantic_vs_lexical_analysis.png'
    
    def create_gap_analysis_dashboard(self):
        """Create comprehensive gap analysis dashboard"""
        if not self.difference_classification_data:
            print("⚠️  No difference classification data available")
            return None
        
        print("🎯 Creating gap analysis dashboard...")
        
        overall_insights = self.difference_classification_data.get('overall_insights', {})
        automation_recs = self.difference_classification_data.get('automation_recommendations', {})
        standardization_ops = self.difference_classification_data.get('standardization_opportunities', {})
        
        # Create comprehensive dashboard
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # Main title
        fig.suptitle('SOC2 Semantic Analysis - Gap Analysis Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        # Key metrics (top row)
        ax1 = fig.add_subplot(gs[0, :2])
        ax2 = fig.add_subplot(gs[0, 2:])
        
        # Left: Key findings summary
        key_findings = [
            f"Controls Analyzed: {overall_insights.get('total_controls_analyzed', 0)}",
            f"Average Style Differences: {overall_insights.get('average_style_percentage', 0):.1f}%",
            f"Average Methodology Differences: {overall_insights.get('average_methodology_percentage', 0):.1f}%",
            f"Key Finding: {overall_insights.get('key_finding', 'N/A')}"
        ]
        
        ax1.axis('off')
        ax1.text(0.05, 0.8, "📊 KEY FINDINGS", fontsize=16, fontweight='bold', transform=ax1.transAxes)
        for i, finding in enumerate(key_findings):
            ax1.text(0.05, 0.6 - i*0.15, f"• {finding}", fontsize=12, transform=ax1.transAxes)
        
        # Right: Automation strategy overview
        strategy = automation_recs.get('automation_strategy', {})
        
        ax2.axis('off')
        ax2.text(0.05, 0.8, "🚀 AUTOMATION STRATEGY", fontsize=16, fontweight='bold', transform=ax2.transAxes)
        
        strategy_text = [
            f"Phase 1: {strategy.get('phase1', 'N/A')[:80]}...",
            f"Phase 2: {strategy.get('phase2', 'N/A')[:80]}...",
            f"Phase 3: {strategy.get('phase3', 'N/A')[:80]}...",
            f"Overall Potential: {strategy.get('overall_automation_potential', 'N/A')}"
        ]
        
        for i, text in enumerate(strategy_text):
            ax2.text(0.05, 0.6 - i*0.12, text, fontsize=10, transform=ax2.transAxes, wrap=True)
        
        # Second row: Automation recommendations
        ax3 = fig.add_subplot(gs[1, :2])
        ax4 = fig.add_subplot(gs[1, 2:])
        
        # Automation candidates
        immediate_candidates = automation_recs.get('immediate_automation_candidates', {})
        standardization_needed = automation_recs.get('standardization_first_candidates', {})
        manual_approach = automation_recs.get('manual_approach_recommended', {})
        
        categories = ['Immediate\nAutomation', 'Standardization\nFirst', 'Manual\nApproach']
        counts = [
            immediate_candidates.get('count', 0),
            standardization_needed.get('count', 0),
            manual_approach.get('count', 0)
        ]
        colors_auto = ['green', 'orange', 'red']
        
        bars = ax3.bar(categories, counts, color=colors_auto, alpha=0.7)
        ax3.set_title('Automation Strategy Distribution', fontweight='bold', fontsize=14)
        ax3.set_ylabel('Number of Controls', fontweight='bold')
        
        # Add value labels
        for bar, count in zip(bars, counts):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Standardization opportunities
        summary = standardization_ops.get('summary', {})
        std_categories = ['High Opportunity', 'Automation Ready', 'Needs Alignment']
        std_counts = [
            summary.get('high_opportunity_count', 0),
            summary.get('automation_ready_count', 0),
            summary.get('standardization_needed_count', 0)
        ]
        colors_std = ['darkgreen', 'lightgreen', 'orange']
        
        bars_std = ax4.bar(std_categories, std_counts, color=colors_std, alpha=0.7)
        ax4.set_title('Standardization Opportunities', fontweight='bold', fontsize=14)
        ax4.set_ylabel('Number of Controls', fontweight='bold')
        
        # Add value labels
        for bar, count in zip(bars_std, std_counts):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Third row: Control profiles analysis
        ax5 = fig.add_subplot(gs[2, :])
        
        control_profiles = self.difference_classification_data.get('control_profiles', {})
        
        if control_profiles:
            # Get top 20 controls for analysis
            profile_data = []
            for control_key, profile in list(control_profiles.items())[:20]:
                control_name = control_key.split('||')[1] if '||' in control_key else control_key
                profile_data.append({
                    'name': control_name[:30] + '...' if len(control_name) > 30 else control_name,
                    'style': profile.get('style_percentage', 0),
                    'methodology': profile.get('methodology_percentage', 0),
                    'automation': profile.get('automation_feasibility', 'too_diverse')
                })
            
            names = [d['name'] for d in profile_data]
            styles = [d['style'] for d in profile_data]
            methodologies = [d['methodology'] for d in profile_data]
            
            y_pos = range(len(names))
            
            # Create stacked horizontal bar chart
            bars1 = ax5.barh(y_pos, styles, alpha=0.7, color='lightblue', label='Style Differences')
            bars2 = ax5.barh(y_pos, methodologies, left=styles, alpha=0.7, color='lightcoral', label='Methodology Differences')
            
            ax5.set_yticks(y_pos)
            ax5.set_yticklabels(names, fontsize=9)
            ax5.set_xlabel('Percentage (%)', fontweight='bold')
            ax5.set_title('Control Difference Breakdown (Top 20 Controls)', fontweight='bold', fontsize=14)
            ax5.legend(loc='lower right')
            ax5.set_xlim(0, 100)
        
        # Fourth row: Recommendations and next steps
        ax6 = fig.add_subplot(gs[3, :])
        ax6.axis('off')
        
        ax6.text(0.05, 0.9, "💡 RECOMMENDATIONS & NEXT STEPS", fontsize=16, fontweight='bold', transform=ax6.transAxes)
        
        recommendations = [
            f"1. IMMEDIATE ACTION: Focus on {immediate_candidates.get('count', 0)} controls ready for template automation",
            f"2. STANDARDIZATION: Align methodologies for {standardization_needed.get('count', 0)} controls before automation",
            f"3. MANUAL APPROACH: Maintain current processes for {manual_approach.get('count', 0)} highly diverse controls",
            f"4. PRIORITIZATION: Start with high standardization opportunity controls ({summary.get('high_opportunity_count', 0)} available)",
            "5. MONITORING: Track standardization progress and re-evaluate automation feasibility quarterly"
        ]
        
        for i, rec in enumerate(recommendations):
            ax6.text(0.05, 0.7 - i*0.12, rec, fontsize=11, transform=ax6.transAxes, wrap=True)
        
        self._save_visualization('gap_analysis_dashboard.png')
        plt.close()
        
        return 'gap_analysis_dashboard.png'
    
    def generate_all_visualizations(self):
        """Generate all visualizations including Phase 4 semantic analysis"""
        print("🎨 Generating all visualizations...")
        print("=" * 50)
        
        # Generate traditional plots
        self.create_variance_distribution_plot()
        self.create_company_coverage_heatmap() 
        self.create_control_family_analysis()
        self.create_interactive_scatter_plot()
        self.create_missing_controls_analysis()
        self.create_language_pattern_wordcloud()
        self.generate_summary_dashboard()
        
        # Phase 4: Generate semantic analysis visualizations
        if self.semantic_data or self.difference_classification_data:
            print(f"\n🧠 Generating Phase 4 semantic analysis visualizations...")
            
            # Semantic similarity analysis
            self.create_semantic_similarity_heatmap()
            
            # Methodology clustering
            self.create_methodology_clustering_visualization()
            
            # Semantic vs lexical comparison
            self.create_semantic_vs_lexical_comparison()
            
            # Gap analysis dashboard
            self.create_gap_analysis_dashboard()
            
            print(f"\n✅ All visualizations generated (including Phase 4)!")
            print(f"📁 Traditional analysis files:")
            print(f"   📈 control_variance_distribution.png")
            print(f"   🔥 company_coverage_heatmap.png") 
            print(f"   📊 control_family_analysis.png")
            print(f"   🌟 interactive_control_analysis.html")
            print(f"   ❌ missing_controls_analysis.png")
            print(f"   ☁️ test_language_wordcloud.png (if wordcloud installed)")
            print(f"   📊 soc2_dashboard.png")
            
            print(f"\n🧠 Phase 4 semantic analysis files:")
            print(f"   🔥 semantic_similarity_summary.png")
            print(f"   🔧 methodology_clustering_analysis.png")
            print(f"   📊 semantic_vs_lexical_analysis.png")
            print(f"   🎯 gap_analysis_dashboard.png")
        else:
            print(f"\n⚠️  Phase 4 visualizations skipped (no semantic data)")
            print(f"✅ Traditional visualizations generated!")
            print(f"📁 Files created:")
            print(f"   📈 control_variance_distribution.png")
            print(f"   🔥 company_coverage_heatmap.png") 
            print(f"   📊 control_family_analysis.png")
            print(f"   🌟 interactive_control_analysis.html")
            print(f"   ❌ missing_controls_analysis.png")
            print(f"   ☁️ test_language_wordcloud.png (if wordcloud installed)")
            print(f"   📊 soc2_dashboard.png")

def main():
    """Main execution function"""
    visualizer = ControlVarianceVisualizer()
    
    if visualizer.data is None:
        print("❌ Could not load variance report data")
        return
    
    # Install required packages reminder
    try:
        import seaborn as sns
        import plotly.express as px
    except ImportError:
        print("📦 Installing required packages...")
        import subprocess
        subprocess.run(["pip", "install", "matplotlib", "seaborn", "plotly", "pandas", "networkx"])
    
    visualizer.generate_all_visualizations()
    
    print(f"\n💡 Next steps:")
    print(f"   • Open interactive_control_analysis.html in a web browser")
    print(f"   • Review soc2_dashboard.png for comprehensive overview")
    print(f"   • Use individual charts for detailed analysis")

if __name__ == "__main__":
    main()