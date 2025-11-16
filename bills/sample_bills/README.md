# Sample Bills Directory

## File Format Requirements

**All bill files in this directory must be PDF files** (`.pdf` extension).

The pipeline uses `pdfplumber` which only works with PDF files, not text files.

## Converting Text to PDF

The `example_bill_text.txt` file is a template that you need to convert to PDF.

### Option 1: Microsoft Word
1. Open `example_bill_text.txt` in Microsoft Word
2. File → Save As
3. Choose "PDF" as the file type
4. Save as `test_bill.pdf` in this directory

### Option 2: Google Docs
1. Copy the text from `example_bill_text.txt`
2. Paste into a new Google Doc
3. File → Download → PDF Document (.pdf)
4. Save as `test_bill.pdf` in this directory

### Option 3: Online Converter
1. Use an online text-to-PDF converter (e.g., ilovepdf.com, smallpdf.com)
2. Upload `example_bill_text.txt`
3. Convert to PDF
4. Download and save as `test_bill.pdf` in this directory

### Option 4: Python Script (if you have reportlab)
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Read text file
with open('example_bill_text.txt', 'r') as f:
    text = f.read()

# Create PDF
c = canvas.Canvas('test_bill.pdf', pagesize=letter)
y = 750
for line in text.split('\n'):
    c.drawString(50, y, line)
    y -= 15
    if y < 50:
        c.showPage()
        y = 750
c.save()
```

## Testing Your PDF

After creating the PDF, test it:

```bash
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/test_bill.pdf \
    --scenario test
```

## Important Notes

1. **PDF must have selectable text** - Scanned images won't work. The PDF needs actual text that can be extracted.

2. **File naming** - You can name the PDF anything (e.g., `test_bill.pdf`, `funding_cut_2024.pdf`), just make sure it has the `.pdf` extension.

3. **Text-based PDFs work best** - PDFs created from Word/Google Docs work perfectly. Scanned PDFs (images) may not work unless they have OCR text layer.

## Example Usage

```bash
# After converting example_bill_text.txt to test_bill.pdf
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/test_bill.pdf \
    --scenario example_bill
```

