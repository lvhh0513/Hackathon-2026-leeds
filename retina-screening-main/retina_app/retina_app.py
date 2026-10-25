"""Retinal screening assistant (hackathon demo). Decision support, NOT diagnosis.

Run from the hack/ folder:   streamlit run retina_app/retina_app.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "backend"))  # reuse the starter's AI switch (llm.py)

from cam_onnx import CamOnnx  # noqa: E402
from grader import OnnxGrader  # noqa: E402
from logic import GRADES, decide, softmax  # noqa: E402
from quality import assess  # noqa: E402
from relevance import check_fundus  # noqa: E402

try:
    from dotenv import load_dotenv

    load_dotenv(HERE.parent / "backend" / ".env")
    import llm  # noqa: E402
except Exception:  # letter drafting is optional
    llm = None

# Find the model inside this repository, regardless of the developer's OS,
# username, Downloads folder name, or where the repository was cloned.
# Optional override: set RETINA_ONNX_PATH to a model file on this server.
MODEL_RELATIVE_PATH = (
    Path("central-system") / "backend" / "ml-pipeline"
    / "training" / "onnx_out" / "branchA_v1.onnx"
)


def find_onnx_model() -> str:
    import os

    override = os.environ.get("RETINA_ONNX_PATH", "").strip()
    if override:
        override_path = Path(override).expanduser().resolve()
        if override_path.is_file():
            return str(override_path)
        raise FileNotFoundError(
            f"RETINA_ONNX_PATH points to a missing file: {override_path}"
        )

    # Works for retina-screening-main/retina_app/retina_app.py nested inside
    # a project on Windows, macOS, or Linux.
    for folder in (HERE.resolve(), *HERE.resolve().parents):
        candidate = folder / MODEL_RELATIVE_PATH
        if candidate.is_file():
            return str(candidate)

    # Preserve a useful path in the settings input even when the file is absent.
    # The existing model-loading error will warn the user.
    return str(HERE.resolve().parent.parent / MODEL_RELATIVE_PATH)


DEFAULT_ONNX = find_onnx_model()

st.set_page_config(page_title="Retinal screening assistant", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500;700&display=swap');
:root {
  --cream: #FAF6EF; --cream-dark: #F0E4D0; --ink: #1A1008; --text: #2C1810;
  --crimson: #C42B2B; --crimson-dark: #9B1B1B; --border: rgba(26,16,8,.25);
  --mono: 'JetBrains Mono', ui-monospace, monospace;
}
html, body, [class*="st-"], .stMarkdown, p, li { font-family: 'Inter', system-ui, sans-serif; }
/* Keep Streamlit's icon font: the broad rule above must not hit icon spans. */
[data-testid="stIconMaterial"], span[class*="material"], .material-icons, .material-symbols-rounded {
  font-family: "Material Symbols Rounded" !important;
  font-feature-settings: "liga" !important;
}
.stApp { background: var(--cream); color: var(--text); }
[data-testid="stSidebar"] { background: var(--cream-dark); border-right: 2px solid var(--crimson); }
h1 { font-weight: 800; letter-spacing: -0.03em; color: var(--ink); }
h2, h3 { font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.06em;
         font-size: 1rem !important; color: var(--crimson-dark); border-bottom: 1px solid var(--border);
         padding-bottom: 4px; }
label, [data-testid="stWidgetLabel"] p, .stCaption, [data-testid="stCaptionContainer"] {
  font-family: var(--mono); letter-spacing: 0.04em; color: var(--text) !important; }
.stButton > button { font-family: var(--mono); font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; border: 2px solid var(--crimson); background: var(--crimson);
  color: #fff; border-radius: 2px; }
.stButton > button:hover { background: var(--crimson-dark); border-color: var(--crimson-dark); color: #fff; }
.stButton > button:disabled { background: #E3DACB; border-color: #5c5247; color: #3b332b; }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 2px; background: #fff; }
.warn-box {border: 4px solid var(--ink); background: #FFE066; color: var(--ink); padding: 12px 16px;
           border-radius: 2px; font-size: 1.1rem; margin-bottom: 1rem;}
.warn-box strong {font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.06em;}
.status-card {border: 2px solid; border-left-width: 12px; border-radius: 2px; padding: 14px 18px;
              margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(26,16,8,.12);}
.status-card .tag {font-family: var(--mono); font-size: 0.8rem; font-weight: 700;
                   letter-spacing: 0.1em; margin: 0 0 4px 0;}
.status-card .headline {font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.01em;}
.status-card .sentence {font-size: 1.15rem; margin: 6px 0 0 0;}
:focus-visible {outline: 3px solid #1a56db !important; outline-offset: 2px;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Retinal screening assistant")
st.markdown(
    '<div class="warn-box" role="alert"><strong>⚠️ Decision support, not diagnosis.</strong><br>'
    "Demo with public / synthetic data only. A clinician makes every decision.</div>",
    unsafe_allow_html=True,
)

# Each card has an icon AND words, so it never relies on colour alone.
STATUS_CARDS = {
    "not_retina": ("✖", "NOT A RETINA PHOTO", "#7A1010", "#FBE9E7",
                   "This does not look like a retina photo, so no grade is shown. Please upload a fundus photo."),
    "retake": ("🔁", "RETAKE THE PHOTO", "#7A1010", "#FBE9E7",
               "The photo is not good enough to assess. Take a new one before any grading."),
    "uncertain": ("⚠️", "UNCERTAIN: CLINICIAN REVIEW", "#5E3A00", "#FFF1D6",
                  "The model is not confident about this photo. A clinician should look at it."),
    "refer": ("🚩", "REFERRAL SUGGESTED", "#7A1010", "#FBE9E7",
              "The model sees a high chance of moderate or worse disease. Consider referral to the eye clinic."),
    "no_refer": ("✅", "NO REFERRAL SUGGESTED", "#14532D", "#E6F4EA",
                 "The provisional rule does not suggest referral. This is not a clearance."),
}


def show_status_card(status: str, referral_suggested: bool) -> None:
    key = status if status in ("not_retina", "retake", "uncertain") else ("refer" if referral_suggested else "no_refer")
    icon, headline, fg, bg, sentence = STATUS_CARDS[key]
    st.markdown(
        f'<div class="status-card" role="status" style="border-color:{fg};background:{bg};color:{fg}">'
        f'<p class="tag">RESULT</p><p class="headline">{icon} {headline}</p><p class="sentence">{sentence}</p></div>',
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_cam(path: str):
    return CamOnnx(str(Path(path).expanduser()))


@st.cache_resource
def load_onnx(path: str):
    return OnnxGrader(str(Path(path).expanduser()), size=384, label="Branch-A v1 classifier (third-party model)")


with st.sidebar:
    st.header("Settings")
    st.caption("Model: Branch-A v1 ONNX")
    with st.expander("Advanced settings"):
        check_relevance = st.checkbox("Check that the image is a retina photo", value=True)
        onnx_path = st.text_input("ONNX path", DEFAULT_ONNX)
        temperature = st.number_input("Calibration T (placeholder)", 0.5, 5.0, 1.0, 0.1)
        uncertain_below = st.slider("Uncertain if top probability below", 0.3, 0.9, 0.6, 0.05)
        referral_at = st.slider("Suggest referral if P(grade 2+) at least", 0.1, 0.9, 0.5, 0.05)
        st.caption("Referral threshold is provisional. The clinical team should set it.")
        st.subheader("Image quality gate")
        min_sharp = st.number_input("Min sharpness", 0.0, 500.0, 15.0, 1.0)
        min_bright = st.number_input("Min brightness", 0.0, 255.0, 40.0, 1.0)
        st.caption("Starting values. Check the numbers shown for good and bad photos, then tune.")
    st.divider()
    st.caption(
        "Credit: the Branch-A v1 model is from NetraSetu by team 'Game Of Codes' (Smart India Hackathon 2026), "
        "public mirror: github.com/Probot-01/Diabetic-Retinopathy-Screening. No licence is stated, so it is used "
        "here only for study and demo, pending permission."
    )

try:
    grader = load_onnx(onnx_path)
except Exception:
    st.error("Model file not found. Check the path in Advanced settings.")
    st.stop()

file = st.file_uploader("Upload a fundus (retina) photo", type=["jpg", "jpeg", "png"])
if not file:
    st.info("Upload a photo to begin.")
    st.stop()

bgr = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
if bgr is None:
    st.error("Could not read this image.")
    st.stop()

if check_relevance:
    relevance = check_fundus(bgr)
    if not relevance["ok"]:
        st.image(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), caption="Uploaded image", width=360)
        show_status_card("not_retina", False)
        for reason in relevance["reasons"]:
            st.caption(reason)
        st.stop()

quality = assess(bgr, min_sharp, min_bright)
probs = softmax(grader.predict(bgr), temperature)
result = decide(probs, quality["ok"], uncertain_below, referral_at)

left, right = st.columns(2)
left.image(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), caption="Input photo", use_container_width=True)

with right:
    show_status_card(result["status"], result["referral_suggested"])

    st.subheader("Image quality")
    if quality["ok"]:
        st.success("✅ Quality check passed (simple check)")
    else:
        st.error("❌ Quality check failed: " + "; ".join(quality["reasons"]) + ".")
    st.caption(
        f"sharpness {quality['sharpness']} · brightness {quality['brightness']} · retina area {quality['retina_fraction']}"
    )

    st.subheader("Model result")
    if result["status"] == "retake":
        st.write("No grade shown: the photo is not good enough to assess.")
    else:
        st.write(f"Model's best guess: **{result['grade_name']}** ({result['confidence']:.0%})")
        st.write(f"P(grade 2+) = **{result['p_referable']:.0%}** (provisional referral rule)")
        if result["status"] == "uncertain" and result["referral_suggested"]:
            st.warning("🚩 The provisional rule also suggests referral. Clinician review needed.")
        if not result["referral_suggested"]:
            st.caption("This is not a clearance. Photos can be missed or misread.")
        st.bar_chart(pd.DataFrame({"probability": probs}, index=GRADES))
    st.caption(f"Model: {grader.name}")

if result["status"] != "retake":
    with st.expander("Advanced details: where the model looked", expanded=False):
        cam_key = f"cam::{file.name}"
        if st.button("Show where the model looked"):
            with st.spinner("Computing the map..."):
                try:
                    st.session_state[cam_key] = load_cam(onnx_path).explain(bgr)
                except Exception as e:
                    st.error(f"Could not compute the map: {e}")
        cam = st.session_state.get(cam_key)
        if cam is not None:
            if cam["info"]["empty"]:
                st.info("No region stands out.")
            else:
                st.image(
                    cam["image"],
                    caption="Grad-CAM-style map (computed from the ONNX model). Each heat cell covers about "
                    "32x32 pixels, so it shows a region, not a single lesion. Where the model looked. "
                    "Not a diagnosis and not proof of where the disease is.",
                    use_container_width=True,
                )
                if cam["info"]["mostlyOutsideRetina"]:
                    st.warning("Most of the heat was outside the retina. Treat this map with care.")


def template_letter(result: dict, quality: dict) -> str:
    """Plain fallback letter built from the result. No AI, no diagnosis."""
    issues = "; ".join(quality["reasons"]) or "no issues found"
    return (
        "Dear GP,\n\n"
        "This patient had a retinal photo screened by our decision-support tool.\n"
        f"- Image quality check: {'passed' if quality['ok'] else 'failed'} ({issues}).\n"
        f"- Status: {result['status']}.\n"
        f"- Model best guess: {result['grade_name']} ({result['confidence']:.0%} confidence).\n"
        f"- Probability of grade 2 or worse: {result['p_referable']:.0%}.\n"
        f"- Referral suggested by the provisional rule: {'yes' if result['referral_suggested'] else 'no'}.\n\n"
        "The model can be wrong. A clinician should review the photo and decide on referral. "
        "No referral suggestion is not a clearance.\n\n"
        "Not medical advice - for clinician review."
    )


st.subheader("Draft referral letter for the GP")
if llm is None:
    st.info("Letter drafting needs backend/llm.py and a key in backend/.env.")
else:
    retake = result["status"] == "retake"
    clicked = st.button("Draft letter", disabled=retake)
    if retake:
        st.caption("Not available: retake the photo first.")
    elif clicked:
        with st.spinner("Writing..."):
            try:
                out = llm.generate(
                    "You draft short, plain-English referral letters from a screening service to a GP. "
                    "Never diagnose. State uncertainty and image-quality problems clearly. "
                    "End with: 'Not medical advice - for clinician review.'",
                    f"Demo case (public/synthetic image). Image quality passed: {quality['ok']} "
                    f"({'; '.join(quality['reasons']) or 'no issues'}). "
                    f"Model best guess: {result['grade_name']} at {result['confidence']:.0%} confidence. "
                    f"Probability of grade 2 or worse: {result['p_referable']:.0%}. "
                    f"Status: {result['status']}. Referral suggested by provisional rule: {result['referral_suggested']}.",
                )
                st.text_area("Draft (edit before use)", out["text"], height=260)
                st.caption(f"AI: {out['provider']} · {out['model']}")
            except Exception as e:
                st.warning("Template letter: the AI service is busy.")
                st.caption(f"Reason: {e}")
                st.text_area("Template (edit before use)", template_letter(result, quality), height=260)

with st.expander("Limitations (read this)"):
    st.markdown(
        "- Decision support only. It does not diagnose and does not replace a clinician.\n"
        "- Tested on 2 public images only (see docs/safety-experiments.md).\n"
        "- The quality check is simple (blur, darkness, retina found) and its thresholds are rough.\n"
        "- Probabilities may be over-confident: calibration here is a placeholder.\n"
        "- The model's authors report that performance drops on photos from a different camera "
        "(their own README, not measured by us).\n"
        "- Training data came from public datasets, not from UK patients. Fairness across groups is untested.\n"
        "- The referral rule is provisional and must be set by the clinical team."
    )
