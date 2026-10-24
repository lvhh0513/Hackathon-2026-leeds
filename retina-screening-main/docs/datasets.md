# Datasets (public or synthetic only)

Check each licence before use. Prefer **no-login** sources — sign-ups can take days.

| Source | What | Login? | Good for |
|---|---|---|---|
| Synthea (synthetichealth.github.io/synthea) | Realistic synthetic EHRs (FHIR/CSV). Pre-generated sample CSVs available | No | Patient pathways, records, special award |
| Our `generate_synthetic.py` | Tiny tailored synthetic set | No | Fast demos, any idea |
| PhysioNet open-access (physionet.org) | ECG, vitals, waveforms | Open-access subsets: no. MIMIC: credentialed — skip | Signals, monitoring |
| Kaggle (kaggle.com/datasets) | Many: diabetes, heart disease, stroke, skin lesions, chest X-ray | Free account | Quick ML baselines |
| NHS England statistics (england.nhs.uk/statistics) | Waiting times (RTT), A&E, cancer waits | No | Impact numbers for the pitch |
| NHS Digital / OpenPrescribing (openprescribing.net) | GP prescribing data | No | Medication / pharmacy ideas |
| UCI ML Repository | Classic health tabular data | No | Baselines |
| MedMNIST | Small medical image sets | No | Lightweight image models |
| Surgical video (e.g. Cholec80, JIGSAWS) | Surgical tool/skill data | Usually request form — check early | Surgery talk ideas, MediaPipe/OpenCV |

## Tips
- Download Synthea sample CSVs **tonight** if possible (large file, slow Wi-Fi).
- Grab 2–3 NHS stats (e.g. waiting list size) to cite in the problem slide.
- For pose/tracking ideas (rehab, posture), you can record **yourselves** with consent — no patient data needed.
