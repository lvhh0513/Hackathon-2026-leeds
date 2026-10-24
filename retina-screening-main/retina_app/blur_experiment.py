"""Stress test: blur / darken one good photo step by step and watch the quality gate and the model.

Run from the project folder:
    python retina_app/blur_experiment.py PATH_TO_GOOD_IMAGE [PATH_TO_ONNX]

Why: to see (1) where the quality gate starts to stop images, and (2) whether the model stays
confident on degraded images that the gate lets through. That second part is the real safety question.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from grader import OnnxGrader  # noqa: E402
from logic import GRADES, decide, softmax  # noqa: E402
from quality import assess  # noqa: E402

DEFAULT_ONNX = (
    "~/Downloads/Diabetic-Retinopathy-Screening/central-system/backend/ml-pipeline/training/onnx_out/branchA_v1.onnx"
)


def variants(bgr):
    for s in [0, 1, 2, 3, 5, 8, 12]:
        yield (f"blur sigma {s}", bgr if s == 0 else cv2.GaussianBlur(bgr, (0, 0), s))
    for f in [0.8, 0.6, 0.45, 0.3, 0.2]:
        yield (f"darker x{f}", np.clip(bgr.astype(np.float32) * f, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    bgr = cv2.imread(sys.argv[1], cv2.IMREAD_COLOR)
    if bgr is None:
        sys.exit(f"Cannot read image: {sys.argv[1]}")
    model = OnnxGrader(str(Path(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_ONNX).expanduser()))
    print(f"{'variant':<14} {'sharp':>7} {'bright':>7} {'gate':>5}  {'best guess':<16} {'conf':>5} {'P(2+)':>6}  status")
    for name, im in variants(bgr):
        q = assess(im)
        p = softmax(model.predict(im))
        d = decide(p, q["ok"])
        print(f"{name:<14} {q['sharpness']:>7} {q['brightness']:>7} {'pass' if q['ok'] else 'STOP':>5}  "
              f"{GRADES[d['grade']]:<16} {d['confidence']:>5.0%} {d['p_referable']:>6.0%}  {d['status']}")
