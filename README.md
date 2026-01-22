# Export Report Operator

#### Description

Export all generated plots from a given workflow in DOCX, PPTX or PDF format.

#### Usage

This operator reads plots from workflow steps and exports them as documents. No crosstab input is required.

#### Output

A single table containing the exported file with columns:
- `mimetype`: File MIME type
- `filename`: Output filename
- `.content`: File content reference
