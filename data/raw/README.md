# Data Files Required

Place the following CSV files in this directory (`data/raw/`):

## Required Files

### 1. `affordability_gap.csv`
**Purpose:** College affordability and financial gap data

**Required Columns:**
- `institution_id` (or `id`, `unitid`, `opeid`, `college_id`) - Unique identifier for each college
- `net_price` - Net price of attendance (numeric)
- `affordability_gap` - Gap between cost and ability to pay (numeric, dollars)
- `hours_to_cover_gap` - Hours of work needed to cover affordability gap (numeric)
- `state` - State abbreviation (e.g., "CA", "TX")
- `institution_type` - Type of institution ("public", "private", "community")

**Optional but Recommended Columns:**
- `name` - College name
- `min_wage` - State minimum wage (numeric)
- `affordability_gap_student_parents` - Gap for student-parents (numeric)

**Example Structure:**
```csv
institution_id,name,state,institution_type,net_price,affordability_gap,hours_to_cover_gap,min_wage
1001,University of California,CA,public,15000,5000,333,15.00
1002,State University,TX,public,12000,3000,200,15.00
```

### 2. `college_results.csv`
**Purpose:** College outcomes, demographics, and performance data

**Required Columns:**
- `institution_id` (or `id`, `unitid`, `opeid`, `college_id`) - Unique identifier (must match affordability_gap.csv)
- `enrollment` - Total enrollment (numeric)
- `grad_rate` or `graduation_rate` - Graduation rate (numeric, 0-100)
- `pct_low_income` or `pell_pct` - Percentage of low-income students (numeric, 0-100)
- `pct_minority` - Percentage of minority students (numeric, 0-100)

**Optional but Recommended Columns:**
- `name` - College name
- `state` - State abbreviation
- `institution_type` - Type of institution
- `tuition` - Tuition amount (numeric)
- `completion_rate` - Completion rate (numeric, 0-100)
- `pct_pell` - Percentage receiving Pell grants (numeric, 0-100)

**Example Structure:**
```csv
institution_id,name,state,institution_type,enrollment,grad_rate,pct_low_income,pct_minority,tuition
1001,University of California,CA,public,30000,75,35,45,12000
1002,State University,TX,public,25000,70,40,50,10000
```

## Column Name Flexibility

The pipeline will automatically try to match common column name variations:

**For Institution ID:**
- `institution_id`, `id`, `unitid`, `opeid`, `college_id`

**For Graduation Rate:**
- `grad_rate`, `graduation_rate`

**For Low-Income Percentage:**
- `pct_low_income`, `pell_pct`, `pct_pell`

## Data Requirements

1. **Institution ID Matching:** Both files must have a common identifier column that can be used to merge them. The pipeline will automatically rename common ID column names to `institution_id`.

2. **Data Types:**
   - Numeric columns should be numeric (not strings with commas)
   - Percentages can be 0-100 or 0-1 (pipeline will normalize)
   - Missing values are handled automatically

3. **Minimum Data:**
   - At least one row per college
   - At least the required columns listed above
   - More columns = richer analysis

## Example: Creating Sample Data

If you don't have real data yet, you can create a minimal sample CSV to test the pipeline:

**affordability_gap.csv:**
```csv
institution_id,name,state,institution_type,net_price,affordability_gap,hours_to_cover_gap
1,Test College 1,CA,public,15000,5000,333
2,Test College 2,TX,public,12000,3000,200
3,Test College 3,NY,private,25000,8000,533
```

**college_results.csv:**
```csv
institution_id,name,state,institution_type,enrollment,grad_rate,pct_low_income,pct_minority
1,Test College 1,CA,public,5000,60,30,25
2,Test College 2,TX,public,3000,55,40,35
3,Test College 3,NY,private,2000,70,20,15
```

## Data Sources

These files typically come from:
- **Affordability Gap Data:** Education Trust, College Scorecard, or custom analysis
- **College Results Data:** IPEDS, College Scorecard, state education departments

## After Adding Files

Once you've placed the files in `data/raw/`, run:

```bash
python data/build_master_colleges.py
```

This will:
1. Load and merge the CSV files
2. Clean and validate the data
3. Run quality checks
4. Calculate custom metrics
5. Output `data/master_colleges.csv`

