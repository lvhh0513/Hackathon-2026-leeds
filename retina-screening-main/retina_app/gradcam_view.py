"""Grad-CAM view for the app. A thin wrapper around the ORIGINAL project's gradcam.py.

The real work (hook on `backbone.bn2.act`, Grad-CAM maths, ROI safeguard that removes heat outside the
retina) is done by gradcam.py from NetraSetu (team "Game Of Codes"). Copy that file, unchanged, next to this one:
    retina_app/gradcam.py
We only (1) build the PyTorch model from the checkpoint, (2) feed it OUR preprocess(), (3) return a picture.

Needs: pip install torch timm   and the checkpoint branchA_v1.pt from the model repo.
Say it honestly: the map is 12x12 cells (each covers 32x32 pixels). It shows the region the model weighted,
never a single lesion. Not a diagnosis.

Quick test:  python retina_app/gradcam_view.py PHOTO.jpg path/to/branchA_v1.pt
"""
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from grader import preprocess  # noqa: E402
from quality import retina_crop  # noqa: E402


def load_model(ckpt_path: str):
    """Build the Branch-A classifier from the checkpoint (same recipe as the original check_gradcam.py)."""
    import timm
    import torch
    import torch.nn as nn

    ck = torch.load(str(Path(ckpt_path).expanduser()), map_location="cpu", weights_only=False)

    class DRClassifier(nn.Module):
        def __init__(self, name, n, drop):
            super().__init__()
            self.backbone = timm.create_model(name, pretrained=False, num_classes=0, drop_rate=0.0)
            self.num_features = self.backbone.num_features
            self.drop = nn.Dropout(p=drop)
            self.head = nn.Linear(self.num_features, n)

        def forward(self, x):
            return self.head(self.drop(self.backbone(x)))

    model = DRClassifier(ck.get("model_name", "efficientnet_b0"), int(ck.get("num_classes", 5)),
                         float(ck.get("drop_rate", 0.3)))
    model.load_state_dict(ck["model_state_dict"], strict=True)
    model.img_size = int(ck.get("img_size", 384))
    return model.eval()  # eval() is required: dropout would randomise the explanation


def explain(model, bgr: np.ndarray) -> dict:
    """Returns {"image": RGB overlay, "class_idx", "probs", "info"}. info has fractionInsideRetina etc."""
    import torch

    from gradcam import compute_gradcam, save_overlay  # the original project's file

    size = getattr(model, "img_size", 384)
    x = torch.from_numpy(preprocess(bgr, size))
    cam, class_idx, logits = compute_gradcam(model, x)

    display = cv2.resize(retina_crop(bgr), (size, size), interpolation=cv2.INTER_AREA)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        info = save_overlay(cam, display, tmp)
        overlay_rgb = cv2.cvtColor(cv2.imread(tmp), cv2.COLOR_BGR2RGB)
    finally:
        os.remove(tmp)

    e = np.exp(logits - logits.max())
    return {"image": overlay_rgb, "class_idx": int(class_idx), "probs": e / e.sum(), "info": info}


if __name__ == "__main__":
    photo, ckpt = sys.argv[1], sys.argv[2]
    out = explain(load_model(ckpt), cv2.imread(photo))
    cv2.imwrite("gradcam_test.png", cv2.cvtColor(out["image"], cv2.COLOR_RGB2BGR))
    print("grade index:", out["class_idx"], "| probs:", np.round(out["probs"], 2))
    print("inside retina:", out["info"].get("fractionInsideRetina"), "| mostly outside:", out["info"].get("mostlyOutsideRetina"))
    print("saved gradcam_test.png")
