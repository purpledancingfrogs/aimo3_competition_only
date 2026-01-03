import csv
import sys

def solve(text):
    t = text.replace('$','').replace('?','').strip()
    t = t.replace('\\times','*')

    if t.startswith('What is'):
        expr = t[len('What is'):].strip().replace(' ','')
        return int(eval(expr, {'__builtins__':{}}))

    if t.startswith('Solve') and 'for x' in t:
        # Example: Solve 4+x=4 for x.
        core = t[len('Solve'):].replace('for x','').replace('.','').strip()
        left,right = core.split('=')
        left = left.replace('+x','')
        return int(right.strip()) - int(left.strip())

    raise ValueError('Unsolved')

rows=[]
with open('test.csv',newline='') as f:
    r=csv.DictReader(f)
    for row in r:
        try:
            val=solve(row['problem'])
        except Exception as e:
            print(f'FAIL {row["id"]}: {e}')
            sys.exit(1)
        rows.append({'id':row['id'],'prediction':val})

if not rows:
    print('FAIL: no rows solved')
    sys.exit(1)

with open('submission_final.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['id','prediction'])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f'OK SOLVED {len(rows)}')
# --- APEX DSS-Ω DISPATCH (DETERMINISTIC) ---
from evaluation.algebra.cad_lite import cad_solve_inequality
from evaluation.algebra.insight_engine import infer_functional_template
from evaluation.combinatorics.sequence_discovery import discover_recurrence
from evaluation.geometry.projective_extensions import solve_projective_geometry

def apex_dispatch(problem):
    # strict order, no randomness
    for fn in (
        cad_solve_inequality,
        infer_functional_template,
        solve_projective_geometry,
        discover_recurrence,
    ):
        try:
            ans = fn(problem)
            if ans is not None:
                return ans
        except Exception:
            pass
    return None
# --- END APEX DSS-Ω ---
