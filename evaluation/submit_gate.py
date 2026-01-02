# Submission gate: confidence + solved-count enforcement

MIN_SOLVED = 40
MIN_CONFIDENCE = 0.6

def allow_submit(results):
    solved = sum(1 for r in results if r['answer'] is not None)
    avg_conf = sum(r['confidence'] for r in results if r['answer'] is not None) / max(solved,1)
    return solved >= MIN_SOLVED and avg_conf >= MIN_CONFIDENCE
