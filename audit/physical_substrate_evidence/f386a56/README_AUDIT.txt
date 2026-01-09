AUDIT_REF=aimo3-submission-ready
AUDIT_SHA=f386a56a1be96dd671b6d6ce0d14cbc841ab3cc9

CHECKS (hostile):
1) Output contract: 0 <= int(ans) <= 99999 (no %1000 / clamp 999)
2) predict signature: def predict(*args, **kwargs) + list->list symmetry
3) No Windows paths: no C:\ literals
4) No runtime file IO on reference.csv/tools
5) Offline deps: requirements minimal / compatible

FILES:
- solver.py.txt
- kaggle_evaluation_aimo_3_inference_server.py.txt
- requirements.txt.txt
- ls_tree_name_only.txt