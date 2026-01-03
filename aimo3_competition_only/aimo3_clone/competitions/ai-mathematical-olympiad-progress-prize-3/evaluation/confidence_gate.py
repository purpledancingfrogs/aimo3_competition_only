CONFIDENCE_THRESHOLD = 0.6
MIN_SOLVED = 10

def ready_for_submission(results):
    solved = [r for r in results if r['answer'] is not None and r['confidence'] >= CONFIDENCE_THRESHOLD]
    return len(solved) >= MIN_SOLVED
