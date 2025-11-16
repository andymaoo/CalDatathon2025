# Tableau Connection Guide

## Quick Start: Connect to Your Predictions

### Step 1: Open Tableau Desktop

1. Launch Tableau Desktop
2. Click **"Connect to Data"** or go to **Data → New Data Source**

### Step 2: Connect to CSV File

1. Under **"Connect"**, select **"Text file"** (or **"More..." → Text file**)
2. Navigate to your output file:
   ```
   outputs/predictions/predicted_impact_test.csv
   ```
3. Click **"Open"**

### Step 3: Verify Data

Tableau will show a preview of your data. You should see columns like:
- `institution_id`
- `name`
- `state`
- `institution_type`
- `tuition_change_pct`
- `tuition_change_dollars`
- `enrollment_change_pct`
- `students_affected`
- `equity_risk_class`
- etc.

### Step 4: Start Building

Click **"Sheet 1"** to start creating visualizations!

---

## Available Data Files

### Main Predictions File
**File:** `outputs/predictions/predicted_impact_<scenario>.csv`

**What it contains:**
- One row per college
- All prediction metrics
- Demographics and college attributes
- **Use for:** Detailed college-level analysis, maps, scatter plots

### Equity Analysis File
**File:** `outputs/equity_analysis/equity_analysis_<scenario>.csv`

**What it contains:**
- Aggregated statistics by equity risk class (Low/Medium/High)
- Average impacts per risk level
- Total students affected per risk level
- **Use for:** Equity scorecard, risk breakdowns

### Summary JSON
**File:** `outputs/summaries/summary_<scenario>.json`

**What it contains:**
- Top-line statistics
- Plain language summary
- Metadata
- **Use for:** KPI cards, summary text

---

## Recommended Dashboard Layouts

### Dashboard 1: Geographic Impact Map

**Purpose:** Show which states are most affected

**Steps:**
1. **Connect to:** `predicted_impact_<scenario>.csv`
2. **Create Map:**
   - Drag `State` to **Rows**
   - Drag `tuition_change_dollars` to **Color** (or **Size**)
   - Change mark type to **Filled Map**
3. **Add Filters:**
   - `institution_type` (public/private/community)
   - `equity_risk_class`
4. **Add Tooltip:**
   - College name
   - Tuition change ($)
   - Students affected
   - Equity risk class

**Calculated Fields:**
```
// Total Students Affected per State
{ FIXED [State] : SUM([students_affected]) }

// Average Tuition Impact per State
{ FIXED [State] : AVG([tuition_change_dollars]) }
```

---

### Dashboard 2: College-Level Detail View

**Purpose:** Show impact for individual colleges

**Steps:**
1. **Create Parameter:**
   - Name: `Selected College`
   - Data type: String
   - Allowable values: List
   - List of values: `name` (from your data)

2. **Create Filter:**
   - Drag `name` to Filters
   - Select **"Use Parameter"** → `Selected College`

3. **Create KPI Cards:**
   - **Tuition Change:** `tuition_change_dollars` (formatted as currency)
   - **Students Affected:** `students_affected` (formatted as number)
   - **Hours to Cover Gap:** `hours_to_cover_gap` (formatted as number)
   - **Equity Risk:** `equity_risk_class` (formatted as text)

4. **Create Bar Chart:**
   - X-axis: Metrics (Tuition Change, Enrollment Change, etc.)
   - Y-axis: Values
   - Use **"Measure Names"** and **"Measure Values"**

5. **Add Plain Language Summary:**
   - Create text box
   - Reference summary from JSON file (or create calculated field)

---

### Dashboard 3: Equity Scorecard

**Purpose:** Show equity impact analysis

**Steps:**
1. **Connect to:** `predicted_impact_<scenario>.csv`

2. **Create Scatter Plot:**
   - X-axis: `pct_low_income` (if available) or `tuition_change_dollars`
   - Y-axis: `tuition_change_dollars`
   - Color: `equity_risk_class` (Green/Yellow/Red)
   - Size: `students_affected` or `enrollment`

3. **Add Reference Lines:**
   - X-axis: 50% (high low-income threshold)
   - Y-axis: $1000 (high impact threshold)

4. **Create Quadrant Analysis:**
   - Top-right quadrant = High impact + Vulnerable = CRISIS
   - Add annotations for each quadrant

5. **Add Filters:**
   - `state`
   - `institution_type`
   - `equity_risk_class`

**Calculated Fields:**
```
// High Risk Flag
IF [equity_risk_class] = "High" THEN "High Risk"
ELSEIF [equity_risk_class] = "Medium" THEN "Medium Risk"
ELSE "Low Risk"
END

// Impact Category
IF [tuition_change_dollars] > 1000 AND [pct_low_income] > 50 THEN "Crisis"
ELSEIF [tuition_change_dollars] > 500 THEN "High Impact"
ELSE "Manageable"
END
```

---

## Key Columns to Use

### For Maps:
- `state` - State abbreviation
- `tuition_change_dollars` - Color/size encoding
- `students_affected` - Size encoding

### For Bar Charts:
- `tuition_change_pct` - Percentage change
- `tuition_change_dollars` - Dollar impact
- `enrollment_change_pct` - Enrollment impact
- `grad_rate_change` - Graduation rate impact

### For Scatter Plots:
- `pct_low_income` - X-axis (if available)
- `pct_minority` - X-axis (if available)
- `tuition_change_dollars` - Y-axis
- `equity_risk_class` - Color

### For Filters:
- `institution_type` - Public/Private/Community
- `state` - State filter
- `equity_risk_class` - Risk level filter

---

## Connecting Multiple Data Sources

### Join Predictions with Equity Analysis

1. **Connect to both files:**
   - `predicted_impact_<scenario>.csv` (primary)
   - `equity_analysis_<scenario>.csv` (secondary)

2. **Create Relationship:**
   - Join on: `equity_risk_class`
   - Join type: **Inner** or **Left**

3. **Use combined data** for aggregated views

---

## Calculated Fields You Should Create

### 1. Impact Severity
```
IF [tuition_change_dollars] > 2000 THEN "Severe"
ELSEIF [tuition_change_dollars] > 1000 THEN "High"
ELSEIF [tuition_change_dollars] > 0 THEN "Moderate"
ELSE "Positive"
END
```

### 2. Students Affected (Formatted)
```
ROUND([students_affected], 0)
```

### 3. Tuition Change (Percentage with Sign)
```
STR([tuition_change_pct]) + "%"
```

### 4. Risk Level Color
```
IF [equity_risk_class] = "High" THEN "#FF0000"
ELSEIF [equity_risk_class] = "Medium" THEN "#FFA500"
ELSE "#00FF00"
END
```

### 5. Top 10 Most Affected
```
RANK(SUM([tuition_change_dollars]), 'desc')
```

---

## Dashboard Best Practices

### 1. Use Consistent Color Schemes
- **Equity Risk:** Red (High), Orange (Medium), Green (Low)
- **Impact:** Red (negative), Green (positive)
- **States:** Use Tableau's built-in state color palette

### 2. Add Interactivity
- **Filters:** Make them visible and easy to use
- **Actions:** Add highlight actions between charts
- **Tooltips:** Include key metrics and plain language explanations

### 3. Mobile-Friendly
- Use responsive layouts
- Stack filters vertically on mobile
- Simplify complex charts for small screens

### 4. Performance
- Use data extracts (`.hyper`) for large datasets
- Aggregate data when possible
- Limit number of marks on screen

---

## Step-by-Step: Your First Dashboard

### Create a Simple Impact Map

1. **Connect to CSV:**
   - Data → Connect → Text file
   - Select `outputs/predictions/predicted_impact_test.csv`

2. **Create Map:**
   - Drag `State` to canvas
   - Tableau should auto-detect geographic role
   - If not: Right-click `State` → Geographic Role → State

3. **Add Color:**
   - Drag `tuition_change_dollars` to **Color**
   - Change mark type to **Filled Map**
   - Adjust color scheme (Red-Blue diverging for negative/positive)

4. **Add Size (Bubble Overlay):**
   - Drag `students_affected` to **Size**
   - Adjust size range

5. **Add Tooltip:**
   - Click **Tooltip** in marks card
   - Add:
     ```
     <College Name>: <name>
     Tuition Change: $<tuition_change_dollars>
     Students Affected: <students_affected>
     Risk Level: <equity_risk_class>
     ```

6. **Add Filter:**
   - Drag `institution_type` to **Filters**
   - Select **"Show Filter"**

7. **Save:**
   - File → Save As → `tableau/dashboards/impact_map.twbx`

---

## Publishing to Tableau Public (Optional)

1. **Prepare:**
   - Remove any sensitive data
   - Ensure all data sources are included

2. **Publish:**
   - Server → Tableau Public → Save to Tableau Public
   - Sign in with Tableau Public account
   - Choose name and description

3. **Share:**
   - Get shareable URL
   - Embed in presentations or websites

---

## Troubleshooting

### Issue: "State not recognized as geographic"
**Solution:** Right-click `State` column → Geographic Role → State

### Issue: "Missing data in map"
**Solution:** Check that state abbreviations match Tableau's expected format (2-letter codes)

### Issue: "CSV file too large"
**Solution:** 
- Use data extract (Data → Extract Data)
- Filter data before connecting
- Aggregate at state level instead of college level

### Issue: "Can't join equity analysis"
**Solution:** Ensure `equity_risk_class` values match exactly (case-sensitive)

---

## Example Dashboard Structure

```
┌─────────────────────────────────────────────────┐
│  Education Policy Impact Dashboard              │
├─────────────────────────────────────────────────┤
│  Filters: [State] [Institution Type] [Risk]    │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Impact Map   │  │ Top 10 Most  │            │
│  │ (by State)   │  │  Affected    │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────────────────────────────────┐  │
│  │ Equity Scorecard (Scatter Plot)          │  │
│  │ X: % Low Income, Y: Tuition Impact       │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ KPI Cards    │  │ Summary Text │            │
│  │ (Totals)     │  │ (Plain Lang) │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
```

---

## Quick Reference: File Locations

- **Predictions:** `outputs/predictions/predicted_impact_<scenario>.csv`
- **Equity Analysis:** `outputs/equity_analysis/equity_analysis_<scenario>.csv`
- **Summary:** `outputs/summaries/summary_<scenario>.json`
- **Save Workbooks:** `tableau/dashboards/`

---

## Next Steps

1. **Connect to your CSV** using the steps above
2. **Build your first map** to see geographic impacts
3. **Create filters** for interactivity
4. **Add calculated fields** for custom metrics
5. **Build the equity scorecard** for detailed analysis
6. **Publish** to share with others

For more advanced Tableau features, refer to Tableau's official documentation or training resources.

