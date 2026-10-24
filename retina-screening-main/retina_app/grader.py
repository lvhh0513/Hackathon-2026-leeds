"""Pluggable graders. Each has .name, .is_mock and .predict(bgr) -> logits (5,).

Swap the model without touching the app:
  - MockGrader: no model, clearly labelled fake output (for UI work and as a safety net)
  - OnnxGrader: branch-A style classifier, input (1,3,S,S), output logits (1,5)
Add your own class (e.g. a model we fine-tune on public APTOS data) with the same two methods.
"""
import cv2
import numpy as np

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def preprocess(bgr: np.ndarray, size: int = 384) -> np.ndarray:
    """Crop border -> resize -> Ben Graham contrast enhancement -> normalise -> NCHW."""
    from quality import retina_crop

    r = cv2.resize(retina_crop(bgr), (size, size), interpolation=cv2.INTER_AREA)
    s = size / 30.0
    blur = cv2.GaussianBlur(r, (int(s) * 2 + 1,) * 2, s)
    e = cv2.addWeighted(r, 4, blur, -4, 128)
    x = cv2.cvtColor(e, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    return ((x - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)


class MockGrader:
    name = "MOCK (no model loaded) - output is NOT a real prediction"
    is_mock = True

    def predict(self, bgr: np.ndarray) -> np.ndarray:
        return np.log(np.array([0.20, 0.20, 0.30, 0.20, 0.10]))


class OnnxGrader:
    is_mock = False

    def __init__(self, path: str, size: int = 384, label: str = "ONNX classifier"):
        import onnxruntime as ort

        self.session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        self.size = size
        self.name = label

    def predict(self, bgr: np.ndarray) -> np.ndarray:
        x = preprocess(bgr, self.size)
        return self.session.run(["logits"], {"input": x})[0][0]
