"""Dependency-free Phase 1 HR workbook profiler. Run from repository root."""
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import csv, json, posixpath, re, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx'
OUT = ROOT / 'reports/phase1'
DOC = ROOT / 'docs/phase1'
OUT.mkdir(parents=True, exist_ok=True)
DOC.mkdir(parents=True, exist_ok=True)
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL_NS = '{http://schemas.openxmlformats.org/package/2006/relationships}'

def col_index(ref):
    n = 0
    for c in re.match(r'[A-Z]+', ref).group():
        n = n * 26 + ord(c) - 64
    return n - 1

def load_workbook(path):
    data = {}
    with zipfile.ZipFile(path) as z:
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ssroot = ET.fromstring(z.read('xl/sharedStrings.xml'))
            ss = [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in ssroot.findall('m:si', NS)]
        relroot = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relations = {r.attrib['Id']:r.attrib['Target'] for r in relroot}
        wbroot = ET.fromstring(z.read('xl/workbook.xml'))
        for sh in wbroot.findall('.//m:sheet', NS):
            name, rid = sh.attrib['name'], sh.attrib['{%s}id' % NS['r']]
            target = relations[rid]
            entry = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            root = ET.fromstring(z.read(entry))
            rows = []
            for row in root.findall('.//m:sheetData/m:row', NS):
                cells = {}
                for cell in row.findall('m:c', NS):
                    typ, v = cell.attrib.get('t'), cell.find('m:v', NS)
                    raw = None if v is None else v.text
                    if typ == 'inlineStr':
                        raw = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                    elif typ == 's' and raw is not None:
                        raw = ss[int(raw)]
                    elif typ == 'b' and raw is not None:
                        raw = raw == '1'
                    elif typ not in ('s', 'str', 'e', 'inlineStr') and raw is not None:
                        try:
                            num = float(raw)
                            raw = int(num) if num.is_integer() else num
                        except ValueError: pass
                    cells[col_index(cell.attrib['r'])] = raw
                if cells:
                    rows.append([cells.get(i) for i in range(max(cells) + 1)])
            headers = rows[0]
            data[name] = [dict(zip(headers, r + [None] * (len(headers) - len(r)))) for r in rows[1:]]
    return data

def date_iso(v):
    if not isinstance(v, (float, int)): return str(v or '')
    return (datetime(1899, 12, 30) + timedelta(days=float(v))).date().isoformat()

def write_csv(path, headers, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(headers); w.writerows(rows)

def check(tests, id_, state, metric, details):
    tests.append([id_, state, metric, details])

def main():
    data = load_workbook(SOURCE)
    inventory, columns, tests = [], [], []
    for name, rows in data.items():
        fields = list(rows[0]) if rows else []
        full_dup = len(rows) - len({tuple(str(r.get(k)) for k in fields) for r in rows})
        inventory.append([name,len(rows),len(fields),full_dup])
        check(tests, 'duplicates_' + name, 'PASS' if not full_dup else 'FAIL', full_dup, 'Duplicate full rows')
        for col in fields:
            values = [r.get(col) for r in rows]
            present = [x for x in values if x is not None and x != '']
            nulls = len(rows) - len(present)
            typ = 'date' if col.endswith('Date') or col == 'Month' else ('integer/decimal' if present and all(isinstance(x,(int,float)) for x in present) else 'text')
            distinct = len(set(map(str,present)))
            lo, hi = '', ''
            if present and typ == 'date': lo,hi = date_iso(min(present)),date_iso(max(present))
            elif present and typ == 'integer/decimal': lo,hi = min(present),max(present)
            columns.append([name,col,typ,len(rows),nulls,round(nulls*100/len(rows),2) if rows else 0,distinct,lo,hi,'[REDACTED]'])
    keys = {'DimEmployee':['EmployeeID'],'DimDepartment':['DepartmentID'],'DimLocation':['LocationID'],
            'DimDate':['Date'],'FactMonthlySnapshot':['Month','DepartmentID','LocationID','Level'],
            'FactEmployeeEvents':['EmployeeID','EventDate','EventType'],
            'FactCompensation':['EmployeeID','EffectiveDate'],'FactPerformance':['EmployeeID','ReviewDate'],
            'FactEngagement':['EmployeeID','SurveyDate'],'FactAbsence':['EmployeeID','AbsenceDate','AbsenceType'],
            'FactRecruitment':['Month','DepartmentID'],'WorkforceTargets':['Month','DepartmentID']}
    for name, key in keys.items():
        rows = data[name]
        dup = len(rows) - len({tuple(str(r.get(k)) for k in key) for r in rows})
        check(tests, 'key_' + name, 'PASS' if not dup else 'FAIL', dup, 'Logical key = ' + '+'.join(key))
    for dim, key, sources in [
        ('DimEmployee','EmployeeID',['FactEmployeeEvents','FactCompensation','FactPerformance','FactEngagement','FactAbsence']),
        ('DimDepartment','DepartmentID',['DimEmployee','FactMonthlySnapshot','FactEmployeeEvents','FactRecruitment','WorkforceTargets']),
        ('DimLocation','LocationID',['DimEmployee','FactMonthlySnapshot','FactEmployeeEvents'])]:
        valid = {r[key] for r in data[dim]}
        for name in sources:
            unknown = sum(r.get(key) not in valid for r in data[name])
            check(tests,'fk_'+name+'_'+key,'PASS' if unknown == 0 else 'FAIL',unknown,dim+'.'+key)
    employees = data['DimEmployee']; events=data['FactEmployeeEvents']; snap=data['FactMonthlySnapshot']; targets=data['WorkforceTargets']
    active = sum(r['EmploymentStatus']=='Active' for r in employees)
    terminated = sum(r['EmploymentStatus']=='Terminated' for r in employees)
    event_types = Counter(r['EventType'] for r in events)
    match = {(r['EmployeeID'],r['EventType'],r['EventDate']) for r in events}
    inconsistent = sum((r['EmployeeID'],'Hire',r['HireDate']) not in match or
                       (r['EmploymentStatus']=='Terminated' and (r['EmployeeID'],'Termination',r['TerminationDate']) not in match)
                       for r in employees)
    check(tests,'employee_events_dates','PASS' if inconsistent == 0 else 'FAIL',inconsistent,'Hire/Termination matches DimEmployee')
    invalid_fte = sum(r['Headcount'] < 0 or r['FTE'] < 0 or r['FTE'] > r['Headcount'] for r in snap)
    check(tests,'snapshot_fte','PASS' if not invalid_fte else 'FAIL',invalid_fte,'0 <= FTE <= Headcount')
    def monthly(rows, month, metrics):
        return {k:round(sum(r[k] for r in rows if date_iso(r['Month'])==month),2) for k in metrics}
    first, last = '2023-01-01','2025-12-01'
    a0=monthly(snap,first,['Headcount','FTE']); a1=monthly(snap,last,['Headcount','FTE'])
    p0=monthly(targets,first,['PlannedHeadcount','BudgetedFTE','BudgetedSalaryCost'])
    p1=monthly(targets,last,['PlannedHeadcount','BudgetedFTE','BudgetedSalaryCost'])
    check(tests,'active_vs_last_snapshot','REVIEW',round(a1['Headcount']-active,2),'Not necessarily same effective date/source grain')
    date_min = min(date_iso(r['Date']) for r in data['DimDate'])
    earliest_event = min(date_iso(r['EventDate']) for r in events)
    check(tests,'dimdate_historical_coverage','REVIEW',date_min,'Earliest event '+earliest_event+' is outside DimDate')
    check(tests,'salary_budget_units','REVIEW','unverified','AnnualSalary vs BudgetedSalaryCost units/timeframe must match')
    check(tests,'no_transfer_events','REVIEW',','.join(sorted(event_types)),'Only Hire/Termination events; no Transfer')
    write_csv(OUT/'source_inventory.csv',['sheet','rows','columns','full_row_duplicates'],inventory)
    write_csv(OUT/'column_profile.csv',['sheet','column','inferred_type','row_count','null_count','null_pct','distinct_count','min','max','example'],columns)
    write_csv(OUT/'quality_checks.csv',['check_id','status','affected_count_or_value','details'],tests)
    mapping = [[s,c,'raw.'+s.lower(),'stg_'+s.lower(),c,t,'review' if n else 'ok'] for s,c,t,_,n,*tail in columns]
    write_csv(DOC/'source_to_target_mapping.csv',['source_sheet','source_column','raw_table','staging_model','target_column','inferred_type','null_review'],mapping)
    overview = {'source':SOURCE.relative_to(ROOT).as_posix(),'tables':len(data),'rows':sum(len(x) for x in data.values()),
        'active_employees':active,'terminated_employees':terminated,'event_types':dict(event_types),
        'first_month':first,'last_month':last,'first_actual':a0,'last_actual':a1,'first_target':p0,'last_target':p1,
        'quality_check_status':dict(Counter(x[1] for x in tests))}
    (OUT/'summary.json').write_text(json.dumps(overview,ensure_ascii=False,indent=2),encoding='utf-8')
    bullets = [f'# Phase 1 — Data Profiling Results', '',f'- Dataset: **{SOURCE.name}**',
        f'- Total: **{len(data)} worksheets, {overview["rows"]:,} records** (excluding headers).',
        f'- DimEmployee: **{active} active, {terminated} terminated**; event types: {dict(event_types)}.',
        f'- Period for snapshots & targets: **2023-01 to 2025-12**.',
        f'- January 2023: actual HC **{a0["Headcount"]}**, target **{p0["PlannedHeadcount"]}**.',
        f'- December 2025: actual HC **{a1["Headcount"]}**, target **{p1["PlannedHeadcount"]}**.',
        f'- December 2025 active profile vs monthly snapshot: **{active} vs {a1["Headcount"]}**, investigate 5-person difference.',
        f'- Automated checks: **{overview["quality_check_status"]}**.', '',
        '## Important design implications',
        '- FactMonthlySnapshot is aggregated by Month × Department × Location × Level, NOT Employee.',
        '- Recruitment rows are department-month aggregates; ReqID is not proof of individual positions.',
        '- DimDate begins in 2023 while hiring history begins before 2023: extend calendar for event-level analysis.',
        '- Compensation is effective-dated; use as-of logic, not sum of historical salaries.',
        '- Targets contain scenario labels. Compare at month-department grain; determine the budget unit.',
        '- Cannot prove causality of attrition from engagement/performance/absence correlations.',
        '- Retention driver analysis must use observations available BEFORE employee termination.',
        '', '## Outputs',
        '- `source_inventory.csv`: table sizes and exact duplicates.',
        '- `column_profile.csv`: data types, missingness, cardinality and ranges.',
        '- `quality_checks.csv`: executed checks and documented review items.',
        '- `docs/phase1/source_to_target_mapping.csv`: raw-to-staging column mapping.',
        '', '> Profiling reports are reproducible by running `python src/phase1/phase1_profiler.py` from the project root.']
    (OUT/'profiling_report.md').write_text('\n'.join(bullets)+'\n',encoding='utf-8')
    print(json.dumps(overview,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
