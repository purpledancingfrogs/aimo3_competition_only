import csv
import ast
import operator

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.floordiv,
    ast.Pow: operator.pow,
}

def eval_expr(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp):
        return OPS[type(node.op)](eval_expr(node.left), eval_expr(node.right))
    raise ValueError('Unsupported expression')

rows = []
with open('test.csv', newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        expr = ast.parse(row['problem'], mode='eval').body
        val = eval_expr(expr)
        rows.append({'id': row['id'], 'prediction': val})

with open('submission_final.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['id','prediction'])
    w.writeheader()
    for r in rows:
        w.writerow(r)
