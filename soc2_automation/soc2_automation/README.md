# SOC2 Automation System

A comprehensive Python system for automated SOC2 report generation and analysis, with advanced semantic analysis capabilities for understanding control testing methodologies.

## 📁 Directory Structure

```
soc2_automation/
├── core/                           # Core processing modules
│   ├── enhanced_batch_extractor.py    # Enhanced extraction with bullet point parsing
│   ├── control_variance_analyzer.py   # Language variance analysis across companies
│   ├── advanced_logo_replacer.py      # Context-aware logo replacement
│   ├── table_extractor.py             # Basic control table extraction
│   ├── document_generator.py          # Word document generation
│   └── report_metadata_extractor.py   # Company metadata extraction
├── cli/                            # Command-line interfaces
│   └── control_query_cli.py           # Interactive query interface for control data
├── visualizations/                 # Data visualization modules
│   └── control_variance_visualizer.py # Comprehensive variance visualization suite
├── semantic_analysis/              # Semantic analysis framework (planned)
│   ├── models/                        # ML models and embeddings
│   ├── processors/                    # Text processing pipelines
│   └── classifiers/                   # Methodology vs style classifiers
├── data/                           # Data storage
│   ├── raw/                           # Raw input data
│   │   └── report_analysis/           # Original extraction results
│   └── processed/                     # Processed JSON data with run tracking
│       ├── runs/                      # Timestamped analysis runs
│       │   └── YYYYMMDD_HHMMSS/      # Individual run directories
│       │       ├── company_organized_reports.json
│       │       ├── control_variance_report.json
│       │       └── [company]_reports.json
│       └── latest -> runs/YYYYMMDD_HHMMSS/  # Symlink to most recent run
├── outputs/                        # Generated outputs
│   ├── visualizations/               # Charts, dashboards, word clouds
│   └── reports/                      # Generated analysis reports
├── templates/                      # Word document templates
│   └── soc2t2-report-template-*.docx
├── docs/                          # Documentation
│   └── SEMANTIC_ANALYSIS_ROADMAP.md  # Development roadmap
└── legacy/                        # Backup of original files
```

## 🚀 Quick Start

### Prerequisites
```bash
pip install python-docx pandas matplotlib seaborn plotly tabulate
```

### Basic Usage

1. **Extract Controls from Reports** (Creates timestamped run):
   ```bash
   cd soc2_automation/core
   python enhanced_batch_extractor.py
   # Creates: ../data/processed/runs/20250911_124827/
   # Updates: ../data/processed/latest -> runs/20250911_124827/
   ```

2. **Analyze Language Variance** (Uses latest data):
   ```bash
   python control_variance_analyzer.py
   # Reads from: ../data/processed/latest/company_organized_reports.json
   # Outputs to: ../data/processed/latest/control_variance_report.json
   ```

3. **Generate Visualizations**:
   ```bash
   cd ../visualizations
   python control_variance_visualizer.py
   ```

4. **Interactive Query Interface**:
   ```bash
   cd ../cli
   python control_query_cli.py
   # Automatically uses latest variance data
   ```

### Run Management

**View Available Runs**:
```bash
ls -la data/processed/runs/
# Shows: 20250911_124827/, 20250911_130045/, etc.
```

**Access Specific Run**:
```bash
ls data/processed/runs/20250911_124827/
# Shows: company_organized_reports.json, control_variance_report.json, etc.
```

**Current Latest Run**:
```bash
ls -la data/processed/latest
# Shows: latest -> runs/20250911_130045/
```

## 📊 System Capabilities

### Current Features

#### ✅ **Control Extraction & Analysis**
- **Enhanced Bullet Point Parsing**: Handles concatenated text without line breaks
- **Control Name/Description Separation**: Smart parsing using dash separators  
- **Company Organization**: Automatic company metadata extraction
- **Variance Analysis**: Language variance detection across 382 unique controls

#### ✅ **Data Visualization**
- **Dashboard Creation**: 7-panel comprehensive analysis dashboard
- **Interactive Visualizations**: HTML-based interactive charts
- **Word Clouds**: Test language pattern visualization
- **Coverage Analysis**: Company control coverage heatmaps

#### ✅ **Interactive CLI**
- **Control Search**: Find controls by ID or name
- **Variance Queries**: Compare test language across companies
- **Pattern Analysis**: Common language pattern identification
- **Export Functionality**: JSON data export capabilities

#### ✅ **Document Processing**
- **Logo Replacement**: Context-aware logo sizing for different document sections
- **Template Management**: Word document template processing
- **Metadata Extraction**: Automatic company and date extraction

### 🎯 **Next Phase: Semantic Analysis** (See `docs/SEMANTIC_ANALYSIS_ROADMAP.md`)

#### Phase 1: Semantic Similarity Engine
- **Sentence-BERT Integration**: Semantic embeddings for test descriptions
- **Similarity Classification**: High (>0.8), Medium (0.5-0.8), Low (<0.5) semantic similarity
- **Clustering Algorithms**: Methodology-based grouping

#### Phase 2: Methodology Extraction System  
- **NLP Pipeline**: spaCy-based Named Entity Recognition
- **Action Classification**: Extract testing verbs and evidence types
- **Scope Analysis**: Sample sizes, time periods, system coverage

#### Phase 3: Difference Classification Engine
- **Style vs Methodology**: Distinguish between writing differences and testing differences
- **Gap Analysis**: Identify companies with fundamentally different approaches
- **Standardization Opportunities**: Automation candidate identification

## 📈 Analysis Results

### Current Dataset Coverage
- **382 unique control variants** across **8 companies**
- **High variance controls**: 186 controls with >70% unique test language
- **Average coverage**: 43.8% of companies implement each control
- **Most common testing verbs**: inquired, inspected, determined, observed

### Key Insights
- Significant language variance exists even for identical control requirements
- Many differences appear to be **style-based** rather than **methodology-based**  
- High potential for automation templates based on semantic similarity
- Clear standardization opportunities identified

## 🔧 Technical Architecture

### Core Processing Pipeline
```
Word Documents → enhanced_batch_extractor.py → JSON Data
     ↓
company_organized_reports.json → control_variance_analyzer.py
     ↓  
control_variance_report.json → control_variance_visualizer.py
     ↓
Comprehensive Visualizations + Interactive Dashboard
```

### Data Flow
1. **Input**: Word documents in `./reports/` folder
2. **Extraction**: Control tables → structured JSON
3. **Analysis**: Language variance detection and metrics
4. **Visualization**: Multi-panel dashboards and interactive charts
5. **Query**: CLI interface for data exploration

## 🛠 Development Roadmap

### Immediate Next Steps
1. **Semantic Analysis Implementation** (10-14 days)
   - Sentence-BERT integration for semantic similarity
   - Methodology extraction using spaCy NLP
   - Style vs methodology classification engine

2. **Enhanced Visualizations**
   - Semantic similarity heatmaps
   - Methodology clustering visualizations  
   - Automation feasibility scoring

3. **Advanced CLI Features**
   - Semantic search capabilities
   - Methodology-based filtering
   - Standardization opportunity identification

### Future Enhancements
- **Machine Learning Pipeline**: Automated methodology classification
- **Report Generation**: Automated SOC2 report writing based on templates
- **API Development**: REST API for programmatic access
- **Web Interface**: Browser-based analysis dashboard

## 📋 File Dependencies

### Core Dependencies
- `enhanced_batch_extractor.py` → Processes Word docs → Timestamped JSON data
- `control_variance_analyzer.py` → Analyzes JSON → Timestamped variance report
- `control_variance_visualizer.py` → Visualizes variance → Charts/dashboards
- `control_query_cli.py` → Queries latest variance data → Interactive analysis

### Data Dependencies  
- **Input**: Raw Word documents in `data/raw/report_analysis/reports/`
- **Processing**: Timestamped runs in `data/processed/runs/YYYYMMDD_HHMMSS/`
- **Access**: Latest data via `data/processed/latest/` symlink
- **Output**: Visualization files in `outputs/visualizations/`

### Run Tracking System
- **Automatic Timestamping**: Each analysis run creates `YYYYMMDD_HHMMSS` folder
- **Latest Symlink**: Always points to most recent successful run
- **Historical Data**: All previous runs preserved for comparison
- **Procedural Tracking**: Full audit trail of analysis iterations

## 🤝 Contributing

This is a specialized SOC2 analysis system. For modifications:

1. **Core Processing**: Modify files in `core/` directory
2. **Visualizations**: Extend `visualizations/control_variance_visualizer.py`
3. **CLI Features**: Add commands to `cli/control_query_cli.py`
4. **Semantic Analysis**: Follow roadmap in `docs/SEMANTIC_ANALYSIS_ROADMAP.md`

## 📝 Notes

- **Import Paths**: Updated for new directory structure
- **Backward Compatibility**: Original files preserved in `legacy/` directory
- **Extensibility**: Designed for semantic analysis integration
- **Performance**: Optimized for datasets with hundreds of controls across multiple companies

---

*Last Updated: September 11, 2024*  
*System Status: Ready for Semantic Analysis Implementation*