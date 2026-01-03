def normalize_answer(ans):
    if ans is None:
        return None
    try:
        if hasattr(ans, "limit_denominator"):
            return str(ans.limit_denominator())
        return str(ans)
    except:
        return None
