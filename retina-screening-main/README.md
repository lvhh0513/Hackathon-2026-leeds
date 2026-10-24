# Retinal screening assistant (hackathon demo)

Decision support, not diagnosis. Public / synthetic data only.

We add a safety layer in front of an existing diabetic retinopathy (DR) model:
a photo quality check ("retake"), an uncertainty flag ("clinician review"),
a provisional referral suggestion, and an optional GP letter draft.

Built for the Leeds AI Society "AI in Healthcare Hackathon" (24-25 Oct 2026).

## Credit
The classifier (Branch-A v1, ONNX) is NOT ours. It comes from NetraSetu by team "Game Of Codes"
(Smart India Hackathon 2026): https://github.com/Probot-01/Diabetic-Retinopathy-Screening
No licence is stated, so we use it only for study and demo. The model file is NOT in this repo.

What we added: the quality gate, the uncertainty and referral logic, the UI, the letter drafting,
and the safety experiments (`docs/safety-experiments.md`).

## Run it

1. Get the model (one time):
   ```bash
   cd ~/Downloads
   git clone --depth 1 https://github.com/Probot-01/Diabetic-Retinopathy-Screening
   ```
   The model file is at:
   `Diabetic-Retinopathy-Screening/central-system/backend/ml-pipeline/training/onnx_out/branchA_v1.onnx`

2. Install and start the app (from the folder of this repo):
   ```bash
   pip install -r retina_app/requirements.txt
   cp backend/.env.example backend/.env    # then put your own GEMINI_API_KEY in it
   streamlit run retina_app/retina_app.py
   ```
   Open http://localhost:8501

3. Point the app to the model:
   in the left sidebar open **Advanced settings** and set **ONNX path**
   to where the file is on YOUR computer (the default is
   `~/Downloads/Diabetic-Retinopathy-Screening/...`).

If the model file is missing, the app shows an error and stops. It never shows fake grades.

## Optional: letter drafting
Needs a key in `backend/.env`. Never commit `.env`.
Choose the model with `GEMINI_MODEL=gemini-3.5-flash-lite` (fast).
If the AI service is busy, the app retries, then shows a template letter.

## Test photos
Use public images only, for example `tests/fixtures/idrid_*` in the model repo (IDRiD dataset).
Do not upload photos of real people.

## Limits
- Tested on 2 public images only.
- Quality thresholds and the referral rule are provisional. The clinical team should set them.
- Not tested: mild disease that looks normal after the photo gets worse.

## More
- `docs/safety-experiments.md`: what happens when the photo gets worse
- `CLAUDE.md`: rules for working with Claude Code
