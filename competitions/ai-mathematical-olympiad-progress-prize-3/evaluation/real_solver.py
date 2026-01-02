import csv
import sys

def solve(text):
    t = text.replace('$','').replace('?','').strip()

    # normalize LaTeX
    t = t.replace('\\times','*')

    if t.startswith('What is'):
        expr = t[len('What is'):].strip().replace(' ','')
        return eval(expr, {'__builtins__':{}})

    if t.startswith('Solve') and 'for x' in t:
        # Solve 4+x=4
        core = t[len('Solve'):].replace('for x','').strip()
        left,right = core.split('=')
        a = int(left.replace('+x',''))
        b = int(right)
        return b - a

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

with open('submission_final.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['id','prediction'])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f'OK SOLVED {len(rows)}')
