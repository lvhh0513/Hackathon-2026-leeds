"""Is this a retina (fundus) photo at all? A simple colour-and-shape check, NOT a trained model.

Why: the grading model always answers with a grade, even for a photo of a dog.
This gate runs first and says "not a retina photo" so no grade is shown.

How it works (all numbers are starting values, tune with check_relevance.py):
- A fundus photo is a round picture on a black background: the four corners of the frame are black.
- A fundus photo is mostly red-orange: red > green > blue, and the hue sits in a narrow band.
- Inside the lit area (green channel > 7) most pixels follow that pattern.
- Ordinary photos (animals, rooms, faces, screenshots) have mixed colours.

Limits (say this honestly): it can be fooled by a red-orange round picture on black,
and an unusual fundus photo may be rejected: a photo cropped to fill the whole frame (no black corners),
or a green-filter / black-and-white one. The app lets you switch this check off in Advanced settings.
"""
import cv2
import numpy as np

# Starting thresholds
MIN_LIT_FRACTION = 0.15  # below this the image is too dark to judge: pass it on to the quality gate
MIN_WARM_ORDER = 0.80  # share of lit pixels with red > green > blue
MIN_HUE_BAND = 0.85  # share of lit pixels with hue in the red-orange band
MIN_RED_GREEN_RATIO = 1.4  # mean red / mean green on lit pixels
MIN_DARK_CORNERS = 3  # how many of the 4 frame corners must be black
MAX_SIDE = 256


def check_fundus(bgr: np.ndarray) -> dict:
    """Returns {"ok", "reasons", "scores"}. Works on a small copy, so it is fast."""
    h, w = bgr.shape[:2]
    scale = MAX_SIDE / max(h, w)
    small = cv2.resize(bgr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)

    b, g, r = (small[:, :, i].astype(np.float32) for i in (0, 1, 2))
    lit = g > 7
    lit_fraction = float(lit.mean())
    reasons = []

    if lit_fraction < MIN_LIT_FRACTION:
        # Too dark to judge the colours. Not our job: the quality gate then says "retake / too dark".
        return {
            "ok": True,
            "reasons": [],
            "scores": {"lit_fraction": round(lit_fraction, 2), "skipped": "too dark to judge"},
        }

    ch, cw = max(2, int(small.shape[0] * 0.10)), max(2, int(small.shape[1] * 0.10))
    corners = [g[:ch, :cw], g[:ch, -cw:], g[-ch:, :cw], g[-ch:, -cw:]]
    dark_corners = int(sum(float((c <= 15).mean()) >= 0.85 for c in corners))
    warm_order = float(((r > g) & (g > b))[lit].mean())
    hue = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)[:, :, 0]  # OpenCV hue: 0..179
    in_band = (hue <= 22) | (hue >= 170)
    hue_band = float(in_band[lit].mean())
    red_green = float(r[lit].mean() / (g[lit].mean() + 1.0))

    if dark_corners < MIN_DARK_CORNERS:
        reasons.append("The picture is not a round retina image on a black background")
    if warm_order < MIN_WARM_ORDER or hue_band < MIN_HUE_BAND or red_green < MIN_RED_GREEN_RATIO:
        reasons.append("The colours do not look like a retina photo (a fundus photo is mostly red-orange)")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "scores": {
            "lit_fraction": round(lit_fraction, 2),
            "warm_order": round(warm_order, 2),
            "hue_band": round(hue_band, 2),
            "red_green": round(red_green, 2),
            "dark_corners": dark_corners,
        },
    }
