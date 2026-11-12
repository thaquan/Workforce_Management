# Workforce Intelligence — DAX catalog

| Folder | Measure | Format | Definition |
|---|---|---|---|
| 01 Workforce | Ending Headcount | #,0 | Stock at last selected reporting month; never sum across months. |
| 01 Workforce | Ending FTE | #,0.0 | Stock at last selected reporting month. |
| 01 Workforce | Weighted Average Tenure Months | #,0.0 | Weighted by headcount, excluding unavailable tenure. |
| 01 Workforce | Prior Month Headcount | #,0 | See measures.dax. |
| 01 Workforce | Headcount MoM Change | #,0 | See measures.dax. |
| 01 Workforce | Headcount MoM % | 0.0%;-0.0%;0.0% | See measures.dax. |
| 01 Workforce | FTE per Headcount | 0.00 | See measures.dax. |
| 01 Workforce | Headcount YoY Change | #,0 | See measures.dax. |
| 02 Planning | Planned Headcount | #,0 | See measures.dax. |
| 02 Planning | Planning Actual Headcount | #,0 | See measures.dax. |
| 02 Planning | Headcount Gap | #,0 | See measures.dax. |
| 02 Planning | Headcount Attainment % | 0.0%;-0.0%;0.0% | See measures.dax. |
| 02 Planning | Budgeted FTE | #,0.0 | See measures.dax. |
| 02 Planning | Planning Actual FTE | #,0.0 | See measures.dax. |
| 02 Planning | FTE Gap | #,0.0 | See measures.dax. |
| 03 Attrition | Hires | #,0 | See measures.dax. |
| 03 Attrition | Terminations | #,0 | See measures.dax. |
| 03 Attrition | Voluntary Terminations | #,0 | See measures.dax. |
| 03 Attrition | Involuntary Terminations | #,0 | See measures.dax. |
| 03 Attrition | Net Hires | #,0 | Recorded hires less exits; not equivalent to snapshot headcount change. |
| 03 Attrition | Monthly Average Headcount | #,0.0 | See measures.dax. |
| 03 Attrition | Monthly Attrition % | 0.0%;-0.0%;0.0% | One month only. Source reconciliation may be provisional. |
| 03 Attrition | Monthly Voluntary Attrition % | 0.0%;-0.0%;0.0% | One month only. Source reconciliation may be provisional. |
| 03 Attrition | Monthly Involuntary Attrition % | 0.0%;-0.0%;0.0% | One month only. Source reconciliation may be provisional. |
| 03 Attrition | Attrition Quality Status |  | Company-level source warning propagated into department rates. |
| 04 Recruitment | Ending Open Requisitions | #,0 | See measures.dax. |
| 04 Recruitment | Filled Requisitions | #,0 | See measures.dax. |
| 04 Recruitment | Cancelled Requisitions | #,0 | See measures.dax. |
| 04 Recruitment | Weighted Days to Fill | #,0.0 | Weighted by fills with a known duration. |
| 04 Recruitment | Fill Share of Closed Requisitions | 0.0%;-0.0%;0.0% | Share of observed closed requisitions; not a funnel conversion rate. |
| 04 Recruitment | Prior Month Open Requisitions | #,0 | See measures.dax. |
| 05 Retention | Observed Employees | #,0 | Historical profile population at observation endpoint; not monthly headcount. |
| 05 Retention | Exited Employees | #,0 | See measures.dax. |
| 05 Retention | Active Employees | #,0 | See measures.dax. |
| 05 Retention | Average Engagement Score | 0.00 | Latest observed/pre-exit survey; excludes missing values. |
| 05 Retention | Average Performance Rating | 0.00 | See measures.dax. |
| 05 Retention | Average Prior 365d Absence Days | #,0.0 | See measures.dax. |
| 06 Time Intelligence | Headcount YoY % | 0.0%;-0.0%;0.0% | See measures.dax. |
| 06 Time Intelligence | YTD Hires | #,0 | See measures.dax. |
| 06 Time Intelligence | YTD Terminations | #,0 | See measures.dax. |
| 06 Time Intelligence | Period Attrition % | 0.0%;-0.0%;0.0% | Selected contiguous period exits divided by mean monthly workforce; blank if any month lacks valid denominator. |
| 06 Time Intelligence | Rolling 12M Attrition % | 0.0%;-0.0%;0.0% | Requires twelve consecutive valid monthly denominators. |
| 06 Time Intelligence | Rolling 12M Terminations | #,0 | See measures.dax. |
| 06 Time Intelligence | YTD Filled Requisitions | #,0 | See measures.dax. |
| 07 Data Quality | Snapshot Reconciliation Difference | #,0 | Company-wide; blank when department, location or level is filtered. |
| 07 Data Quality | Reconciliation Review Months | #,0 | See measures.dax. |
| 07 Data Quality | Latest Pipeline Run ID | #,0 | See measures.dax. |
| 07 Data Quality | Latest Pipeline Status |  | See measures.dax. |
| 07 Data Quality | Latest Quality PASS | #,0 | Blank when the latest run has no completed quality checks; zero only after checks exist. |
| 07 Data Quality | Latest Quality REVIEW | #,0 | Blank when the latest run has no completed quality checks; zero only after checks exist. |
| 07 Data Quality | Latest Quality FAIL | #,0 | Blank when the latest run has no completed quality checks; zero only after checks exist. |
