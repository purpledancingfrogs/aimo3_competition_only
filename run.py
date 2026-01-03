import sys, csv
from solver import solve

def main():
    if len(sys.argv) != 3:
        sys.exit(2)
    inp, out = sys.argv[1], sys.argv[2]
    with open(inp, newline='') as f:
        rows = list(csv.DictReader(f))
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id','prediction'])
        w.writeheader()
        for r in rows:
            w.writerow({'id': r['id'], 'prediction': solve(r['problem'])})

if __name__ == '__main__':
    main()
