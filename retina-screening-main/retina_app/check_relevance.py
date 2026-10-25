"""Print the 'is this a retina photo?' numbers for any images, to tune the thresholds.

Usage (from the repo root):
    python retina_app/check_relevance.py photo1.jpg photo2.jpg ...
Try the 4 fundus fixtures (all should say RETINA) and a few non-retina photos (should say NOT).
"""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).parent))
from relevance import check_fundus  # noqa: E402

for path in sys.argv[1:]:
    img = cv2.imread(path)
    if img is None:
        print(f"{path}: cannot read")
        continue
    res = check_fundus(img)
    verdict = "RETINA" if res["ok"] else "NOT a retina photo"
    print(f"{Path(path).name:45s} {verdict:20s} {res['scores']}")
