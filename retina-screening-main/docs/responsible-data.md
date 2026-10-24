# Responsible use of data — special award (£300, LIDA)

Judged on **Privacy · Security · Fairness · Transparency**. Put one slide + a README section on this.

## One-liner for the pitch
> "We used only synthetic/public data, store no personal information, keep a clinician in the loop, and show the model's limits on screen."

## Checklist
**Privacy**
- [ ] Only public or synthetic data (state the source + licence)
- [ ] No PII stored; age bands instead of DOB; no names
- [ ] If camera/MediaPipe: process on-device, don't save video frames

**Security**
- [ ] API keys in `.env`, never in git; `.gitignore` checked
- [ ] CORS locked to the frontend origin
- [ ] No patient data sent to third parties in a real deployment without a DPA (say this)

**Fairness**
- [ ] Note dataset demographics and gaps (age, sex, ethnicity, skin tone for images)
- [ ] If a model: report performance per subgroup, even a simple table

**Transparency**
- [ ] UI label: "Decision support, not diagnosis"
- [ ] Show *why* (inputs used, confidence, source)
- [ ] Limitations slide: what it can't do, failure cases
- [ ] Human-in-the-loop: clinician confirms every action

## Words judges like
UK GDPR, data minimisation, NHS DSPT, DCB0129/DCB0160 (clinical safety), MHRA Software as a Medical Device, human-in-the-loop, model card.
