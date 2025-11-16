# Quick Test Guide - End-to-End Pipeline Testing

## Step 1: Add Your PDF

Place your PDF bill file in the `bills/sample_bills/` directory:

```bash
# Copy your PDF to the sample_bills folder
# The PDF can have any name, just make sure it has .pdf extension
```

**Example:**
- `bills/sample_bills/my_test_bill.pdf`
- `bills/sample_bills/education_funding_2024.pdf`
- `bills/sample_bills/sb-743_0.pdf` (already tested)

## Step 2: Run the Pipeline

Use the main pipeline runner with your PDF:

```bash
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/YOUR_PDF_NAME.pdf \
    --scenario YOUR_SCENARIO_NAME
```

**Replace:**
- `YOUR_PDF_NAME.pdf` with your actual PDF filename
- `YOUR_SCENARIO_NAME` with a descriptive name (e.g., `funding_cut_2024`, `test_run_2`)

**Example:**
```bash
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/my_test_bill.pdf \
    --scenario test_run_2
```

## Step 3: Optional Flags

You can add optional flags for more features:

```bash
# With CSV analysis
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/my_test_bill.pdf \
    --scenario test_run_2 \
    --run-analysis

# Filter by specific states
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/my_test_bill.pdf \
    --scenario test_run_2 \
    --affected-states CA TX NY

# Full example with all options
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/my_test_bill.pdf \
    --scenario test_run_2 \
    --run-analysis \
    --affected-states CA
```

## Step 4: Check the Outputs

After running, check these directories:

### Main Outputs:
- `outputs/predictions/predicted_impact_YOUR_SCENARIO_NAME.csv` - College-level predictions
- `outputs/equity_analysis/equity_analysis_YOUR_SCENARIO_NAME.csv` - Equity breakdown
- `outputs/summaries/summary_YOUR_SCENARIO_NAME.json` - Summary statistics

### Analysis Outputs (if `--run-analysis` used):
- `outputs/analysis/YOUR_SCENARIO_NAME_statistics.json` - Statistical summary
- `outputs/analysis/YOUR_SCENARIO_NAME_correlations.csv` - Correlation matrix
- `outputs/analysis/YOUR_SCENARIO_NAME_plots/` - Distribution plots
- `outputs/analysis/YOUR_SCENARIO_NAME_custom_metrics.json` - Custom metrics

## Step 5: Verify Results

### Quick Verification:

1. **Check the console output** - Should show:
   - Number of colleges affected
   - Total students impacted
   - Average tuition change
   - Plain language summary

2. **Open the CSV in Excel/Tableau**:
   ```bash
   # Open the predictions CSV
   outputs/predictions/predicted_impact_YOUR_SCENARIO_NAME.csv
   ```

3. **Check the summary JSON**:
   ```bash
   # View summary statistics
   cat outputs/summaries/summary_YOUR_SCENARIO_NAME.json
   ```

## What Makes a Good Test PDF?

✅ **Good Test PDF:**
- Contains explicit numbers (percentages, dollar amounts)
- Mentions institution types (public, private, community)
- Uses clear language about funding changes
- Has selectable text (not just scanned images)

❌ **Poor Test PDF:**
- Only vague language ("substantial cuts", "significant increases")
- No explicit numbers
- Scanned images without OCR text
- Unclear which institutions are affected

## Troubleshooting

### Issue: "No colleges match the bill criteria"
**Solution:** The bill extraction didn't find matching institution types. Check:
- Does your master_colleges.csv have colleges of those types?
- Try running without `--affected-states` filter
- Check the bill extraction output in the logs

### Issue: "Low confidence extraction"
**Solution:** 
- Add `ANTHROPIC_API_KEY` to `.env` for LLM fallback
- Or improve bill PDF with more explicit numbers

### Issue: "Missing trained models"
**Solution:** Run model training first:
```bash
python -m models.train_models
```

### Issue: "Master colleges file not found"
**Solution:** Build master dataset first:
```bash
python -m data.build_master_colleges
```

## Example: Complete Test Workflow

```bash
# 1. Add your PDF
# (Copy PDF to bills/sample_bills/)

# 2. Run pipeline
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/my_bill.pdf \
    --scenario my_test \
    --run-analysis

# 3. Check outputs
# - outputs/predictions/predicted_impact_my_test.csv
# - outputs/summaries/summary_my_test.json

# 4. Open in Tableau
# Connect to: outputs/predictions/predicted_impact_my_test.csv
```

## Comparing Multiple Scenarios

You can run multiple scenarios and compare them:

```bash
# Scenario 1
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill1.pdf \
    --scenario scenario_1

# Scenario 2
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/bill2.pdf \
    --scenario scenario_2

# Then compare the CSVs in Tableau or Excel
```

## Quick Test Script

Create a simple test script `test_pipeline.sh` (or `.bat` for Windows):

```bash
#!/bin/bash
# test_pipeline.sh

PDF_NAME=$1
SCENARIO_NAME=$2

if [ -z "$PDF_NAME" ] || [ -z "$SCENARIO_NAME" ]; then
    echo "Usage: ./test_pipeline.sh <pdf_name> <scenario_name>"
    echo "Example: ./test_pipeline.sh my_bill.pdf test_run"
    exit 1
fi

python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/$PDF_NAME \
    --scenario $SCENARIO_NAME \
    --run-analysis

echo "Test complete! Check outputs/predictions/predicted_impact_${SCENARIO_NAME}.csv"
```

**Windows PowerShell version** (`test_pipeline.ps1`):
```powershell
param(
    [string]$PdfName,
    [string]$ScenarioName
)

if (-not $PdfName -or -not $ScenarioName) {
    Write-Host "Usage: .\test_pipeline.ps1 -PdfName <pdf_name> -ScenarioName <scenario_name>"
    Write-Host "Example: .\test_pipeline.ps1 -PdfName my_bill.pdf -ScenarioName test_run"
    exit 1
}

python pipeline/run_full_pipeline.py `
    --bill "bills/sample_bills/$PdfName" `
    --scenario $ScenarioName `
    --run-analysis

Write-Host "Test complete! Check outputs/predictions/predicted_impact_${ScenarioName}.csv"
```

## Next Steps

1. **Test with your PDF**: Follow steps 1-4 above
2. **Review outputs**: Check the CSV files and JSON summary
3. **Open in Tableau**: Connect to the predictions CSV and build visualizations
4. **Run analysis**: Use `--run-analysis` flag for detailed statistics
5. **Compare scenarios**: Run multiple bills and compare results

