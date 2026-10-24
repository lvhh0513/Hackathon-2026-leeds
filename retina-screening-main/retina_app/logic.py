"""Decision logic, kept separate from the UI so it is easy to test and to explain."""
import numpy as np

GRADES = ["0 No DR", "1 Mild", "2 Moderate", "3 Severe", "4 Proliferative"]


def softmax(v: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    z = np.asarray(v, dtype=np.float64) / temperature
    e = np.exp(z - z.max())
    return e / e.sum()


def decide(probs: np.ndarray, quality_ok: bool, uncertain_below: float = 0.6, referral_at: float = 0.5) -> dict:
    """status: 'retake' | 'uncertain' | 'ok'. Referral rule is PROVISIONAL (clinical team decides)."""
    grade = int(np.argmax(probs))
    confidence = float(probs[grade])
    p_ref = float(np.sum(probs[2:]))  # probability of grade 2 or worse
    if not quality_ok:
        status = "retake"
    elif confidence < uncertain_below:
        status = "uncertain"
    else:
        status = "ok"
    return {
        "status": status,
        "grade": grade,
        "grade_name": GRADES[grade],
        "confidence": confidence,
        "p_referable": p_ref,
        "referral_suggested": p_ref >= referral_at,
    }
