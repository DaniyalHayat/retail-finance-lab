# Workbook guide

Open `workbooks/model.xlsx` in desktop Microsoft Excel. The workbook has live formulas and a native PivotTable. The Python pipeline and the checked-in workbook initially use the same synthetic inputs.

## Regenerate inputs

```bash
python run.py
python refresh_workbook.py
```

Close the workbook before running the refresh script. The script updates source cells only, preserves formulas and native PivotTable objects, and requests full recalculation and PivotTable refresh on open. After refreshing, open the workbook in Excel, use **Data > Refresh All**, recalculate, and save. Until then, cached values and the PivotTable cache may be stale. Always check the reconciliations after an input change.

The template intentionally enforces the original record counts. If a different dataset changes the row counts, the script stops rather than truncating data or leaving SUMIFS/PivotTable source ranges incomplete. Extend the source ranges, formulas, charts and any native PivotTable source bounds deliberately before using a different shape. Do not treat prior `excel_verification.json` as a newly executed verification after changes.

The SQL databases are generated locally and excluded from Git. CSVs, analysis JSON, HTML, workbook, source and tests are included in the repository.

## Excel features

- `Assumptions!D5`: 1 Base, 2 Downside, 3 Upside. CHOOSE selects each active driver; one Forecast build calculates all cases.
- `Forecast`: units × price, costs, cash tax, merchandise working capital, capex, and cash continuity.
- `Variance bridge`: SUMPRODUCT and explicit driver components reconcile actual EBITDA to budget.
- `Pivot review`: native month/category pivot with a region filter and revenue/EBITDA values.
- `Checks`: bridge difference, cash-flow identity, cash continuity and revenue source tie should be near zero.
- Backtest values on Summary are historical, fixed evaluation results; scenario selection changes future forecasts, not historical results.

The dashboard's three cases are snapshots rebuilt by Python. Editing Excel assumptions updates Excel immediately; rerun the Python analysis with matching assumptions to update the HTML report. The two files do not claim a live connection.
