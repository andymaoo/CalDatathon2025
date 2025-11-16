# Education Policy Impact ML Pipeline

A comprehensive data science pipeline that processes education bills, predicts impacts using machine learning models, and exports results for Tableau visualization. Built for civic tech applications to help voters understand how education policy affects colleges and students.

## Architecture Overview

**Core Flow:** Raw Data → Data Foundation → Training Data → ML Models → Bill Processing → Impact Prediction → CSV/JSON Export → Tableau Visualization

### Key Components

1. **Data Foundation Layer** - CSV aggregation, cleaning, quality checks
2. **Training Data Generation** - Synthetic scenarios with economic theory
3. **Model Training** - 4 specialized ML models (XGBoost, LightGBM, Random Forest)
4. **Bill Processing** - PDF → parameters extraction (rule-based + LLM fallback)
5. **Impact Prediction** - ML inference pipeline
6. **CSV Analysis Module** - Exploratory analysis, quality checks, custom metrics
7. **Export Layer** - Tableau-ready CSVs and JSON summaries
8. **Box Integration** - Cloud content management (optional)

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <your-repo-url> CalDatathon2025
cd CalDatathon2025

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configure Environment (Optional)

Create a `.env` file for API keys:

```bash
# LLM APIs (optional - for bill extraction and summaries)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Box Integration (optional)
BOX_CLIENT_ID=...
BOX_CLIENT_SECRET=...
BOX_ENTERPRISE_ID=...
BOX_JWT_PRIVATE_KEY_PATH=./box_config.json
```

### 3. Prepare Base Datasets

Place your raw CSV files in `data/raw/`:
- `affordability_gap.csv` - College affordability data
- `college_results.csv` - College outcomes and demographics

Then build the master dataset:

```bash
python data/build_master_colleges.py
```

This will:
- Merge CSV files on institution ID
- Clean and validate data
- Run quality checks
- Calculate custom metrics
- Output: `data/master_colleges.csv`

### 4. Generate Training Data

```bash
python data/create_training_data.py --n-scenarios 1000
```

This generates synthetic training scenarios using Monte Carlo simulation and economic elasticities.

### 5. Train Models

```bash
python models/train_models.py
```

This trains 4 ML models:
- **Tuition Change Regressor** (XGBoost)
- **Enrollment Change Regressor** (LightGBM)
- **Graduation Rate Regressor** (Random Forest)
- **Equity Risk Classifier** (XGBoost)

Models are saved to `models/saved_models/` with evaluation metrics and SHAP plots.

### 6. Process a Bill

```bash
# Process a local bill PDF
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill.pdf \
    --scenario 10pct_funding_cut

# Process a bill from Box
python pipeline/run_full_pipeline.py \
    --bill bill_2024_123.pdf \
    --scenario funding_cut \
    --use-box \
    --box-folder-id 123456789

# With CSV analysis
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill.pdf \
    --scenario test \
    --run-analysis
```

## Pipeline Workflow

### Stage 1: Data Foundation

```bash
# Build master colleges dataset
python data/build_master_colleges.py

# Check data quality
python data/quality_checker.py data/master_colleges.csv
```

### Stage 2: Training Data Generation

```bash
# Generate synthetic scenarios
python data/create_training_data.py \
    --master-colleges data/master_colleges.csv \
    --output outputs/training_data.csv \
    --n-scenarios 1000 \
    --seed 42
```

### Stage 3: Model Training

```bash
# Train all models
python models/train_models.py \
    --training-data outputs/training_data.csv \
    --output-dir models/saved_models
```

### Stage 4: Bill Processing & Prediction

```bash
# Full pipeline
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill.pdf \
    --scenario my_scenario \
    --run-analysis
```

## Output Files

After running the pipeline, you'll find:

### Predictions
- `outputs/predictions/predicted_impact_<scenario>.csv` - College-level predictions
- `outputs/equity_analysis/equity_analysis_<scenario>.csv` - Equity risk breakdown
- `outputs/summaries/summary_<scenario>.json` - Summary statistics and plain language summary

### Analysis (if `--run-analysis` used)
- `outputs/analysis/<scenario>_statistics.json` - Statistical summary
- `outputs/analysis/<scenario>_correlations.csv` - Correlation matrix
- `outputs/analysis/<scenario>_plots/` - Distribution plots
- `outputs/analysis/<scenario>_custom_metrics.json` - Domain-specific metrics

## CSV Analysis Module

The pipeline includes a comprehensive CSV analysis toolkit:

```python
from analysis.csv_analyzer import analyze_scenario
from analysis.custom_metrics import calculate_custom_metrics

# Analyze a scenario CSV
results = analyze_scenario("outputs/predictions/predicted_impact_test.csv", "test")

# Calculate custom metrics
metrics = calculate_custom_metrics(df, "outputs/analysis/test_custom_metrics.json")
```

Features:
- Statistical summaries (mean, median, std, quartiles)
- Correlation analysis
- Distribution plots (histograms, box plots)
- Group aggregations (by state, institution type)
- Scenario comparisons
- Custom domain metrics (affordability impact, equity gaps, state vulnerability)

## Box Integration

The pipeline supports Box Content Cloud for:
- Storing and retrieving bill PDFs
- Uploading prediction outputs
- Optional AI-powered extraction (Box AI)

### Setup Box Integration

1. Create a Box app and get credentials
2. Add credentials to `.env`:
   ```
   BOX_CLIENT_ID=...
   BOX_CLIENT_SECRET=...
   BOX_ENTERPRISE_ID=...
   BOX_JWT_PRIVATE_KEY_PATH=./box_config.json
   ```

3. Use Box in pipeline:
   ```bash
   python pipeline/run_full_pipeline.py \
       --bill bill.pdf \
       --scenario test \
       --use-box \
       --box-folder-id 123456789 \
       --upload-to-box \
       --box-output-folder-id 987654321
   ```

## Tableau Integration

All outputs are formatted as clean CSVs ready for Tableau:

1. **Connect to CSV in Tableau Desktop:**
   - Data → Connect to Data → Text File
   - Select `outputs/predictions/predicted_impact_<scenario>.csv`

2. **Key Columns Available:**
   - `institution_id`, `name`, `state`, `institution_type`
   - `tuition_change_pct`, `tuition_change_dollars`
   - `enrollment_change_pct`, `students_affected`
   - `grad_rate_change`, `equity_risk_class`
   - `hours_to_cover_gap`
   - Demographics: `pct_low_income`, `pct_minority`

3. **Join with Equity Analysis:**
   - Connect to `outputs/equity_analysis/equity_analysis_<scenario>.csv`
   - Join on `equity_risk_class`

## Model Details

### Tuition Change Model (XGBoost Regressor)
- **Target:** `tuition_change_pct`
- **Expected Performance:** R² = 0.75-0.85, MAE = 1-2%
- **Key Features:** Funding change, baseline tuition, low-income %, institution type

### Enrollment Change Model (LightGBM Regressor)
- **Target:** `enrollment_change_pct`
- **Expected Performance:** R² = 0.70-0.80, MAE = 2-3%
- **Key Features:** Tuition change, min wage, childcare subsidy, demographics

### Graduation Rate Model (Random Forest Regressor)
- **Target:** `grad_rate_change`
- **Expected Performance:** R² = 0.60-0.75, MAE = 0.5-1%
- **Key Features:** Financial stress, affordability gap, demographics

### Equity Risk Model (XGBoost Classifier)
- **Target:** `equity_risk_class` (Low/Medium/High)
- **Expected Performance:** Accuracy = 75-85%
- **Key Features:** Demographics, financial stress, institutional characteristics

## File Structure

```
CalDatathon2025/
├── data/
│   ├── raw/                          # Input CSVs
│   ├── processed/                    # Intermediate files
│   ├── master_colleges.csv           # Final merged dataset
│   ├── build_master_colleges.py      # CSV aggregation
│   ├── create_training_data.py       # Synthetic scenarios
│   ├── quality_checker.py           # Data validation
│   ├── custom_analysis.py           # Domain metrics
│   └── csv_processor.py              # CSV utilities
│
├── models/
│   ├── saved_models/                 # Trained .pkl files
│   ├── train_models.py               # Model training
│   ├── feature_engineering.py        # Feature creation
│   └── model_config.py               # Hyperparameters
│
├── pipeline/
│   ├── extract_bill.py               # PDF → parameters
│   ├── predict_impact.py             # ML inference
│   ├── export_for_tableau.py         # CSV/JSON export
│   ├── run_full_pipeline.py          # Main entry point
│   ├── box_client.py                 # Box API integration
│   └── utils.py                      # Shared utilities
│
├── analysis/
│   ├── csv_analyzer.py               # Exploratory analysis
│   └── custom_metrics.py             # Domain-specific metrics
│
├── outputs/
│   ├── predictions/                  # predicted_impact_*.csv
│   ├── equity_analysis/              # equity_analysis_*.csv
│   ├── summaries/                     # summary_*.json
│   ├── analysis/                      # Analysis reports
│   └── visualizations/                # SHAP plots, etc.
│
├── bills/
│   └── sample_bills/                 # Sample PDF bills
│
├── tableau/
│   └── dashboards/                   # Tableau workbooks
│
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
└── README.md                         # This file
```

## Dependencies

See `requirements.txt` for full list. Key packages:
- **Core:** pandas, numpy, scikit-learn
- **ML:** xgboost, lightgbm
- **NLP:** pdfplumber, spacy, nltk
- **LLM:** anthropic (Claude), openai
- **Box:** boxsdk
- **Analysis:** matplotlib, seaborn, scipy
- **Explainability:** shap

## Usage Examples

### Example 1: Basic Pipeline

```bash
# 1. Build data foundation
python data/build_master_colleges.py

# 2. Generate training data
python data/create_training_data.py

# 3. Train models
python models/train_models.py

# 4. Process a bill
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill.pdf \
    --scenario funding_cut_10pct
```

### Example 2: With Analysis

```bash
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill.pdf \
    --scenario test \
    --run-analysis
```

### Example 3: Box Integration

```bash
python pipeline/run_full_pipeline.py \
    --bill bill_2024_123.pdf \
    --scenario funding_cut \
    --use-box \
    --box-folder-id 123456789 \
    --upload-to-box \
    --box-output-folder-id 987654321
```

### Example 4: CSV Analysis Standalone

```python
from analysis.csv_analyzer import analyze_scenario
from analysis.custom_metrics import calculate_custom_metrics
import pandas as pd

# Load predictions
df = pd.read_csv("outputs/predictions/predicted_impact_test.csv")

# Run analysis
results = analyze_scenario("outputs/predictions/predicted_impact_test.csv", "test")

# Calculate custom metrics
metrics = calculate_custom_metrics(df)
```

## Troubleshooting

### Missing spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### Missing Master Colleges File
```bash
# Ensure raw CSVs are in data/raw/
# Then run:
python data/build_master_colleges.py
```

### Missing Trained Models
```bash
# Ensure training data exists, then:
python models/train_models.py
```

### Box Integration Not Working
- Check `.env` file has correct credentials
- Verify Box app has proper permissions
- Check JWT key file path is correct

## Contributing

This is a hackathon project. For production use, consider:
- Adding unit tests
- Implementing proper error handling
- Adding data validation at each stage
- Creating API endpoints
- Adding authentication/authorization

## License

[Your License Here]

## Acknowledgments

Built for CalDatathon 2025. Uses economic research on education policy impacts and ML best practices for civic tech applications.

