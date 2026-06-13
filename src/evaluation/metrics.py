def precision(tp, fp):
    return tp / (tp + fp + 1e-9)

def recall(tp, fn):
    return tp / (tp + fn + 1e-9)

def f1(p, r):
    return 2 * p * r / (p + r + 1e-9)