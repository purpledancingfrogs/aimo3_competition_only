import sys, csv
from solver import solve

def main():
    if len(sys.argv) != 3:
        sys.exit(2)

    inp, out = sys.argv[1], sys.argv[2]

    with open(inp, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # accept either 'id' or first column as identifier
        id_field = 'id' if 'id' in reader.fieldnames else reader.fieldnames[0]
        prob_field = 'problem' if 'problem' in reader.fieldnames else reader.fieldnames[-1]
        rows = list(reader)

    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'prediction'])
        w.writeheader()
        for r in rows:
            w.writerow({
                'id': r[id_field],
                'prediction': solve(r[prob_field])
            })

if __name__ == '__main__':
    main()
