How to execute (Windows / PowerShell)
1) Single problem via file:
   Get-Content .\input.txt | python .\solver.py

2) Single problem via literal:
   "2*x+3=11" | Set-Content .\input.txt
   Get-Content .\input.txt | python .\solver.py

3) Batch (if run_all.py exists and is used):
   python .\run_all.py
