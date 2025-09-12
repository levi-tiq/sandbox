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

class ControlVarianceVisualizer:
    """
    Create visualizations for control variance analysis
    """
    
    def __init__(self, variance_report_path: str = "control_variance_report.json"):
        self.variance_report_path = variance_report_path
        self.data = None
        self.companies = []
        self.controls_df = None
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        self.load_data()
    
    def load_data(self):
        """Load the variance report data"""
        try:
            with open(self.variance_report_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.companies = self.data.get('analysis_summary', {}).get('companies_analyzed', [])
            
            print(f"✅ Loaded variance data: {len(self.data.get('variance_analysis', {}))} controls across {len(self.companies)} companies")
            
            # Convert to DataFrame for easier analysis
            self._create_dataframe()
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    
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
        plt.savefig('control_variance_distribution.png', dpi=300, bbox_inches='tight')
        print("📈 Saved: control_variance_distribution.png")
        
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
        plt.savefig('company_coverage_heatmap.png', dpi=300, bbox_inches='tight')
        print("🔥 Saved: company_coverage_heatmap.png")
        
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
        plt.savefig('control_family_analysis.png', dpi=300, bbox_inches='tight')
        print("📊 Saved: control_family_analysis.png")
        
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
        
        fig.write_html('interactive_control_analysis.html')
        print("🌟 Saved: interactive_control_analysis.html")
        
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
        plt.savefig('missing_controls_analysis.png', dpi=300, bbox_inches='tight')
        print("❌ Saved: missing_controls_analysis.png")
        
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
            plt.savefig('test_language_wordcloud.png', dpi=300, bbox_inches='tight')
            print("☁️ Saved: test_language_wordcloud.png")
            
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
        
        plt.savefig('soc2_dashboard.png', dpi=300, bbox_inches='tight')
        print("📊 Saved: soc2_dashboard.png")
        
        return fig
    
    def generate_all_visualizations(self):
        """Generate all visualizations"""
        print("🎨 Generating all visualizations...")
        print("=" * 50)
        
        # Generate all plots
        self.create_variance_distribution_plot()
        self.create_company_coverage_heatmap() 
        self.create_control_family_analysis()
        self.create_interactive_scatter_plot()
        self.create_missing_controls_analysis()
        self.create_language_pattern_wordcloud()
        self.generate_summary_dashboard()
        
        print(f"\n✅ All visualizations generated!")
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