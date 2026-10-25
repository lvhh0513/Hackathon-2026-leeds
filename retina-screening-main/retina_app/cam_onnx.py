"""Grad-CAM-equivalent heatmap straight from the ONNX file. No PyTorch, no checkpoint needed.

Why this works: Branch-A ends with  last conv map -> global average pool -> one linear layer.
For that shape, Grad-CAM is exactly:  heat_c = ReLU( sum_k W[c,k] * F_k )
where F is the feature map that goes INTO the pooling and W is the final linear layer's weights.
(The original project's own ONNX path says the same: "global-average-pool -> linear, closed form".)

What we do: open the .onnx, find the last global-average-pool, add its input as an extra output,
read the final linear weights from the file, and combine them. Everything is read from the model itself.

Say it honestly: the map is coarse (12x12 cells for a 384 px input, about 32x32 px each). It shows the region the
model weighted, never a single lesion. Heat outside the retina circle is removed (same safeguard as the original
gradcam.py). Not a diagnosis.

Quick test:  python retina_app/cam_onnx.py PHOTO.jpg path/to/branchA_v1.onnx
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from grader import preprocess  # noqa: E402
from quality import retina_crop  # noqa: E402


class CamOnnx:
    def __init__(self, onnx_path: str, size: int = 384):
        import onnx
        import onnxruntime as ort
        from onnx import TensorProto, helper, numpy_helper

        self.size = size
        model = onnx.load(str(Path(onnx_path).expanduser()))
        g = model.graph
        inits = {i.name: numpy_helper.to_array(i) for i in g.initializer}
        # constants stored as Constant nodes too
        for n in g.node:
            if n.op_type == "Constant" and n.attribute:
                for a in n.attribute:
                    if a.name == "value":
                        inits[n.output[0]] = numpy_helper.to_array(a.t)

        # 1) the LAST global average pool = the pooling before the classifier (earlier ones are squeeze-excite)
        pool = None
        for n in g.node:
            if n.op_type in ("GlobalAveragePool", "ReduceMean"):
                pool = n
        if pool is None:
            raise RuntimeError("No global average pool found in the ONNX graph")
        self.feature_name = pool.input[0]

        # 2) the LAST linear layer with a 2-D weight that has 5 outputs
        weight = None
        for n in g.node:
            if n.op_type in ("Gemm", "MatMul"):
                for i in n.input:
                    w = inits.get(i)
                    if w is not None and w.ndim == 2 and 5 in w.shape:
                        weight = w
        if weight is None:
            raise RuntimeError("No 5-output linear layer found in the ONNX graph")
        self.W = weight if weight.shape[0] == 5 else weight.T  # (5, K)

        self.logit_name = g.output[0].name
        g.output.append(helper.make_tensor_value_info(self.feature_name, TensorProto.FLOAT, None))
        self.session = ort.InferenceSession(model.SerializeToString(), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def explain(self, bgr: np.ndarray, class_idx=None) -> dict:
        x = preprocess(bgr, self.size)
        logits, feats = self.session.run([self.logit_name, self.feature_name], {self.input_name: x})
        logits = logits[0]
        F = feats[0]  # (K, h, w)
        if F.shape[0] != self.W.shape[1]:
            raise RuntimeError(f"Feature map {F.shape} does not match linear weights {self.W.shape}")
        if class_idx is None:
            class_idx = int(np.argmax(logits))
        cam = np.maximum(np.tensordot(self.W[class_idx], F, axes=(0, 0)), 0).astype(np.float32)
        peak = float(cam.max())
        if peak > 0:
            cam = cam / peak

        display = cv2.resize(retina_crop(bgr), (self.size, self.size), interpolation=cv2.INTER_AREA)
        heat = cv2.resize(cam, (self.size, self.size), interpolation=cv2.INTER_LINEAR)

        # ROI safeguard: remove heat outside the retina circle, and report how much that was
        lit = cv2.morphologyEx((display[:, :, 1] > 7).astype(np.uint8), cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))).astype(bool)
        total = float(heat.sum())
        inside = float(heat[lit].sum())
        frac = inside / total if total > 0 else None
        heat = heat * lit
        if heat.max() > 0:
            heat = heat / heat.max()

        colour = cv2.applyColorMap(np.uint8(255 * heat), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(colour, 0.4, display, 0.6, 0)
        e = np.exp(logits - logits.max())
        return {
            "image": cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB),
            "class_idx": class_idx,
            "probs": e / e.sum(),
            "info": {
                "camResolution": list(cam.shape),
                "fractionInsideRetina": frac,
                "mostlyOutsideRetina": bool(frac is not None and frac < 0.5),
                "empty": peak <= 0,
            },
        }


if __name__ == "__main__":
    photo, path = sys.argv[1], sys.argv[2]
    out = CamOnnx(path).explain(cv2.imread(photo))
    cv2.imwrite("cam_test.png", cv2.cvtColor(out["image"], cv2.COLOR_RGB2BGR))
    print("grade index:", out["class_idx"], "| probs:", np.round(out["probs"], 2))
    print("info:", out["info"])
    print("saved cam_test.png")
