import os
import hashlib
import csv

normalized_dir = os.path.join(os.getcwd(), 'normalized')
files = [f for f in os.listdir(normalized_dir) if f.endswith('.norm.txt')]
hashes = {}
for f in files:
    with open(os.path.join(normalized_dir, f), 'rb') as hf:
        hashes[f] = hashlib.sha256(hf.read()).hexdigest()

matrix_path = os.path.join(os.getcwd(), 'convergence_matrix.csv')
with open(matrix_path, 'w', newline='') as cm:
    writer = csv.writer(cm)
    writer.writerow([''] + files)
    for f1 in files:
        row = [f1]
        for f2 in files:
            row.append('True' if hashes[f1] == hashes[f2] else 'False')
        writer.writerow(row)

# Optional: create summary of True/False counts
summary_path = os.path.join(os.getcwd(), 'convergence_summary.txt')
true_count = sum([row.count('True') for row in [[hashes[f1]==hashes[f2] for f2 in files] for f1 in files]])
false_count = sum([row.count('False') for row in [[hashes[f1]==hashes[f2] for f2 in files] for f1 in files]])
with open(summary_path, 'w') as s:
    s.write(f'True: {true_count}\nFalse: {false_count}\n')
