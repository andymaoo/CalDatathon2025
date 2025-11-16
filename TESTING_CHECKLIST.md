# Testing Checklist

## Prerequisites Before Testing

### ✅ 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Download spaCy model (REQUIRED)
python -m spacy download en_core_web_sm
```

### ✅ 2. Add Data Files

Place these files in `data/raw/`:
- `affordability_gap.csv` - See `data/raw/README.md` for structure
- `college_results.csv` - See `data/raw/README.md` for structure

**Minimum test data:** You can create minimal sample CSVs to test the pipeline structure.

### ✅ 3. Build Master Dataset

```bash
python data/build_master_colleges.py
```

This creates `data/master_colleges.csv` which is required for all subsequent steps.

### ✅ 4. Generate Training Data

```bash
python data/create_training_data.py --n-scenarios 1000
```

This creates `outputs/training_data.csv` required for model training.

### ✅ 5. Train Models

```bash
python models/train_models.py
```

This creates trained models in `models/saved_models/`:
- `tuition_model.pkl`
- `enrollment_model.pkl`
- `grad_model.pkl`
- `equity_model.pkl`
- `scaler.pkl`
- `encoders.pkl`

### ✅ 6. (Optional) Configure API Keys

Create `.env` file for optional features:
```bash
# For LLM-based bill extraction and plain language summaries
ANTHROPIC_API_KEY=sk-ant-...

# For Box integration
BOX_CLIENT_ID=...
BOX_CLIENT_SECRET=...
BOX_ENTERPRISE_ID=...
```

**Note:** The pipeline works without API keys, but:
- Rule-based extraction will be used (may have lower confidence)
- Template summaries instead of LLM-generated ones

## Bill PDF Requirements

### What the Pipeline Extracts

The bill processing pipeline looks for these policy parameters:

1. **Funding Changes**
   - Keywords: "funding", "appropriation", "budget", "allocation"
   - Verbs: "cut", "reduce", "decrease", "increase", "boost"
   - Format: Percentage changes (e.g., "10% cut", "5 percent reduction")

2. **Minimum Wage Changes**
   - Keywords: "minimum wage", "min wage", "wage"
   - Format: Dollar amounts (e.g., "$15", "$2 increase")

3. **Childcare Subsidies**
   - Keywords: "childcare", "child care", "child-care"
   - Format: Dollar amounts (e.g., "$3000 subsidy", "$5000 grant")

4. **Tuition Caps**
   - Keywords: "tuition cap", "tuition limit", "tuition increase limit"
   - Format: Percentage (e.g., "5% cap", "10 percent limit")

5. **Institution Types**
   - Keywords: "public university", "public college", "community college", "private institution"
   - If not specified, assumes all types are affected

### Ideal Bill PDF Structure

A good test bill PDF should contain:

**Example Bill Text:**
```
EDUCATION FUNDING ACT OF 2024

Section 1: State Appropriations
This bill reduces state funding for public universities by 10 percent.
Community colleges will see a 5% reduction in state appropriations.

Section 2: Minimum Wage
The minimum wage shall be increased to $15.00 per hour.

Section 3: Student Support
A childcare subsidy of $3,000 per year shall be provided to eligible 
student-parents attending public and community colleges.

Section 4: Tuition Regulations
Public universities are limited to a 5% annual tuition increase.
```

### What Makes a Good Test Bill

✅ **Good Test Bill:**
- Contains explicit numbers (percentages, dollar amounts)
- Mentions institution types (public, private, community)
- Uses clear language about funding changes
- Has structured sections

❌ **Poor Test Bill:**
- Only contains vague language ("substantial cuts", "significant increases")
- No explicit numbers
- Unclear which institutions are affected
- Scanned images without OCR (text extraction may fail)

### Creating a Test Bill PDF

**Option 1: Use a Real Bill**
- Download an actual education policy bill from a state legislature
- Most state legislatures publish bills as PDFs

**Option 2: Create a Simple Test Bill**
1. Create a text file with sample bill content (see example above)
2. Convert to PDF using:
   - Microsoft Word → Save as PDF
   - Google Docs → Download as PDF
   - Online converter

**Option 3: Use Sample Bill Generator**
The pipeline includes a script to create mock bills:
```bash
python scripts/generate_scenarios.py
```
This creates text files in `bills/sample_bills/` that you can convert to PDF.

## Testing Workflow

### Step 1: Quick Test (Minimal Data)

```bash
# 1. Create minimal test CSVs (see data/raw/README.md for structure)
# 2. Build master dataset
python data/build_master_colleges.py

# 3. Generate training data (use smaller number for quick test)
python data/create_training_data.py --n-scenarios 100

# 4. Train models
python models/train_models.py

# 5. Create a simple test bill PDF and place in bills/
# 6. Run pipeline
python pipeline/run_full_pipeline.py \
    --bill bills/your_test_bill.pdf \
    --scenario test_run
```

### Step 2: Verify Outputs

Check that these files were created:
- `outputs/predictions/predicted_impact_test_run.csv`
- `outputs/equity_analysis/equity_analysis_test_run.csv`
- `outputs/summaries/summary_test_run.json`

### Step 3: Test with Analysis

```bash
python pipeline/run_full_pipeline.py \
    --bill bills/your_test_bill.pdf \
    --scenario test_run \
    --run-analysis
```

This adds:
- `outputs/analysis/test_run_statistics.json`
- `outputs/analysis/test_run_correlations.csv`
- `outputs/analysis/test_run_plots/`

## Common Issues & Solutions

### Issue: "Master colleges file not found"
**Solution:** Run `python data/build_master_colleges.py` first

### Issue: "Missing trained models"
**Solution:** Run `python models/train_models.py` first

### Issue: "spaCy model not found"
**Solution:** Run `python -m spacy download en_core_web_sm`

### Issue: "No colleges match the bill criteria"
**Solution:** 
- Check that your master_colleges.csv has colleges matching the bill's institution types
- Verify the bill extraction found the correct institution types
- Check the bill parameters in the summary JSON

### Issue: "Low confidence extraction"
**Solution:**
- Add ANTHROPIC_API_KEY to .env for LLM fallback
- Or improve bill PDF with more explicit numbers

### Issue: "PDF text extraction failed"
**Solution:**
- Ensure PDF has selectable text (not just images)
- Try a different PDF
- Check that pdfplumber is installed correctly

## Sample Bill PDF Content

Here's a complete example you can use to create a test bill:

```
EDUCATION POLICY IMPACT BILL - TEST VERSION

AN ACT TO MODIFY STATE EDUCATION FUNDING AND SUPPORT

Section 1: State Funding Reductions
This bill reduces state appropriations for public universities by 10 percent.
Community colleges will receive a 5% reduction in state funding.
Private institutions are not affected by this provision.

Section 2: Minimum Wage Increase
The state minimum wage shall be increased by $2.00 per hour, from $13.00 to $15.00.

Section 3: Childcare Assistance
Eligible student-parents attending public universities and community colleges 
shall receive a childcare subsidy of $3,000 per academic year.

Section 4: Tuition Regulations
Public universities are hereby limited to a maximum annual tuition increase of 5 percent.
This cap applies to all public institutions of higher education.

Section 5: Effective Date
This act shall take effect on January 1, 2025.
```

Save this as a text file, convert to PDF, and place in `bills/sample_bills/test_bill.pdf`.

## Next Steps After Testing

1. **Verify Predictions:** Check that predictions make sense (tuition changes, enrollment impacts)
2. **Check Tableau Compatibility:** Open CSV in Tableau and verify it loads correctly
3. **Test Analysis Module:** Run with `--run-analysis` and review generated reports
4. **Test Box Integration:** If using Box, test download/upload functionality
5. **Scale Up:** Use real data files and actual bills for full testing

