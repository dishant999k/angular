# --- Data split logic ---

def split_data(df, config):
    """70/15/15 temporal split. Validation frame is returned for completeness but unused."""
    n = len(df)
    train_end = int(n * config.TRAIN_FRAC)
    val_end = train_end + int(n * config.VAL_FRAC)
    return (
        df.iloc[:train_end].copy(),
        df.iloc[train_end:val_end].copy(),
        df.iloc[val_end:].copy(),
    )


def score_against_truth(pred, truth):
    tp = int((truth & pred).sum())
    fp = int((~truth & pred).sum())
    fn = int((truth & ~pred).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "alerts": int(pred.sum()),
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }