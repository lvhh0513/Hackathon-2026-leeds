"""Very simple image-quality gate for fundus photos (blur, darkness, retina found).

These are crude checks with STARTING thresholds. Tune them by looking at the numbers
the app shows for a few good and bad photos. Say "simple quality check" in the pitch.
"""
import cv2
import numpy as np


def retina_crop(bgr: np.ndarray) -> np.ndarray:
    """Crop the black border around the retina (green channel > 7)."""
    _, m = cv2.threshold(bgr[:, :, 1], 7, 255, cv2.THRESH_BINARY)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return bgr
    x, y, w, h = cv2.boundingRect(max(cs, key=cv2.contourArea))
    return bgr[y : y + h, x : x + w]


def assess(bgr: np.ndarray, min_sharpness: float = 15.0, min_brightness: float = 40.0) -> dict:
    """Returns metrics, ok flag and human-readable reasons."""
    retina_fraction = float((bgr[:, :, 1] > 7).mean())
    g = cv2.cvtColor(cv2.resize(retina_crop(bgr), (384, 384), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(g, cv2.CV_64F).var())
    lit = g[g > 7]
    brightness = float(lit.mean()) if lit.size else 0.0

    reasons = []
    if retina_fraction < 0.15:
        reasons.append("No retina found (is this a fundus photo?)")
    if sharpness < min_sharpness:
        reasons.append("Image looks blurry")
    if brightness < min_brightness:
        reasons.append("Image looks too dark")
    return {
        "ok": not reasons,
        "reasons": reasons,
        "sharpness": round(sharpness, 1),
        "brightness": round(brightness, 1),
        "retina_fraction": round(retina_fraction, 2),
    }
