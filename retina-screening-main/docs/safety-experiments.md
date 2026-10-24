# Safety experiments: what happens when the photo gets worse?

Status: draft, 24 Oct 2026. Decision support only, not diagnosis.

**Model tested:** Branch-A v1 classifier (EfficientNet-B0, 5 grades) from NetraSetu by team "Game Of Codes" (Smart India Hackathon 2026). Public mirror: github.com/Probot-01/Diabetic-Retinopathy-Screening. No licence is stated; used here for study and demo, pending permission. We did not train it.

## Why we ran this
A model gives a confidence number. We wanted to know if that number tells us when a photo is too poor to trust. We also wanted to test the simple quality gate we added in front of the model.

## Method
- Two test photos from the model repo's own test folder: `idrid_010_good_pass` (model says severe) and `idrid_163_good_borderline` (model says no DR). No ground-truth labels were used, so this is not an accuracy test.
- Each photo was degraded on the computer: Gaussian blur (sigma 1 to 12) and darkening (x0.8 down to x0.2).
- For every version we recorded: quality gate result, the model's best guess, its confidence, and P(grade 2 or worse).
- Settings: quality gate needs sharpness >= 15 and brightness >= 40; "uncertain" if top probability < 60%; referral suggested if P(grade 2+) >= 50% (provisional rule); calibration T = 1.0 (placeholder, so confidences are likely too high).

## Results

**Photo A: idrid_010 (model: severe)**

| Variant | Sharpness | Brightness | Gate | Best guess | Confidence | P(2+) |
| --- | --- | --- | --- | --- | --- | --- |
| original | 60.2 | 99.9 | pass | 3 Severe | 90% | 100% |
| blur 1 | 42.3 | 99.8 | pass | 3 Severe | 84% | 100% |
| blur 2 | 19.4 | 99.5 | pass | 2 Moderate | 61% | 100% |
| blur 3 | 9.6 | 99.3 | STOP | 2 Moderate | 90% | 100% |
| blur 5 | 4.0 | 98.7 | STOP | 2 Moderate | 95% | 98% |
| blur 8 | 2.4 | 97.8 | STOP | 1 Mild | 34% | 47% |
| blur 12 | 1.9 | 96.8 | STOP | 0 No DR | 34% | 51% |
| darker x0.8 | 42.0 | 79.6 | pass | 3 Severe | 64% | 100% |
| darker x0.6 | 24.0 | 59.7 | pass | 2 Moderate | 54% | 98% |
| darker x0.45 | 14.2 | 44.6 | STOP | 2 Moderate | 96% | 99% |
| darker x0.3 | 7.3 | 29.6 | STOP | 2 Moderate | 73% | 75% |
| darker x0.2 | 4.1 | 19.7 | STOP | 2 Moderate | 54% | 62% |

**Photo B: idrid_163 (model: no DR)**

| Variant | Sharpness | Brightness | Gate | Best guess | Confidence | P(2+) |
| --- | --- | --- | --- | --- | --- | --- |
| original | 46.9 | 86.2 | pass | 0 No DR | 74% | 11% |
| blur 1 | 42.6 | 86.3 | pass | 0 No DR | 73% | 12% |
| blur 2 | 33.4 | 86.3 | pass | 0 No DR | 80% | 11% |
| blur 3 | 24.9 | 86.4 | pass | 0 No DR | 79% | 11% |
| blur 5 | 13.6 | 86.5 | STOP | 0 No DR | 74% | 16% |
| blur 8 | 6.6 | 86.3 | STOP | 2 Moderate | 56% | 67% |
| blur 12 | 3.6 | 86.0 | STOP | 2 Moderate | 55% | 80% |
| darker x0.8 | 31.9 | 70.2 | pass | 0 No DR | 87% | 6% |
| darker x0.6 | 19.5 | 52.7 | pass | 0 No DR | 92% | 4% |
| darker x0.45 | 11.3 | 39.5 | STOP | 0 No DR | 98% | 1% |
| darker x0.3 | 5.9 | 26.2 | STOP | 0 No DR | 98% | 1% |
| darker x0.2 | 3.4 | 17.4 | STOP | 0 No DR | 84% | 14% |

## What we found
1. **Confidence is not a quality signal.** On degraded photos the model often became more sure, not less (photo A, blur 3 to 5: 90% to 95%; photo B, darker x0.6 to x0.45: 92% to 98%). A separate quality check is needed.
2. **In both photos, the referral decision never changed inside the zone the gate allowed.** It only changed or became unstable where the gate had already said STOP (heavy blur).
3. **The grade is less stable than the referral decision.** Photo A moved from "severe" to "moderate" with mild blur (blur 2) or darkening (x0.6), while P(grade 2+) stayed at 98% to 100%.
4. **Heavy blur pushes the model the wrong way in both directions.** The severe-looking photo drifted towards "no DR" (34%); the normal-looking photo drifted towards "moderate" (55%) and a referral. The gate stops both.
5. **When the model is unsure, it says so.** Photo A at darker x0.6 gave "uncertain" (54%), so the second safety layer worked there.

## What we do not know
- Only two photos, both from the model's own test folder. The pattern may not hold for others.
- Degradation was made on the computer. Real out-of-focus, motion blur, glare or a different camera may behave differently. The model's authors report lower sensitivity on a different camera (their own README, not measured by us).
- We have no ground-truth labels, so we cannot say the grades are correct.
- We did not test mild disease. A mild case looking normal after degradation is the error we most need to rule out.
- Gate thresholds were set by hand on a few images and are rough. Confidences are uncalibrated (T = 1.0).

## What this means for the design
- A quality check runs before any grade is shown. Poor photos get "please retake", not a result.
- A low top probability shows "uncertain: clinician review".
- Referral is shown as a provisional rule. "No referral" is never worded as an all-clear.
- A clinician decides. The tool never diagnoses.

## Open decision for the clinical lead
Minimum sharpness 15 or 20? At 20, more photos are retaken, but the grade shifts less (photo A, blur 2, would be stopped; photo B, darker x0.6, would also be stopped although its answer was right). In these two photos the referral decision is the same either way.
