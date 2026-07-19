# GitHub Publishing Checklist

**Author:** Md Imamuddin

## Before your first commit

- [ ] Add a `LICENSE` file — MIT is the standard, permissive choice for a portfolio project. Note in the README's existing License & Attribution section that the *code* license (yours) is separate from the *data* licenses (CC0/ODbL/non-commercial, already documented)
- [ ] Decide whether to commit the raw/processed CSVs at all. They're not huge (largest is the ~160MB Stack Overflow survey, which exceeds GitHub's 100MB hard limit) — either use Git LFS for that one file, or (recommended) leave data out per `.gitignore` and document the 3 download URLs in `docs/data_sources.md` so anyone cloning the repo can reproduce it
- [ ] Double-check no API keys, credentials, or personal file paths leaked into any script (a quick `grep -rn "password\|api_key\|/Users/\|/home/" .` before the first push)

## What NOT to do: don't hide the documented bugs — they're a strength

This is the single most important item on this checklist, and the easiest one to get backwards under pre-publish nerves.

Across this project there are several places where something didn't work cleanly: the classification models' class imbalance, the two likely data-collection artifacts in company-size and experience-level distributions, the CV-vs-test R² framing gap, a row-count arithmetic error caught during a final consistency pass (see below), the missing free-text descriptions that forced the NLP phase to adapt scope. The instinct before publishing something public is to quietly clean these out of the README and let the polished reports stand alone.

Don't. Every one of those is evidence of the thing a hiring manager actually wants to see — not "this person produced correct numbers" (any dataset can produce numbers), but "this person can tell when a number is misleading, and says so before someone else has to catch it." A project with zero visible mistakes reads as either too simple to have hit any, or as one where problems were found and quietly smoothed over. Neither is the impression you want.

Concretely:
- [ ] Leave every "honest limitation" callout in the README exactly as written — don't trim them down to make the summary look cleaner
- [ ] If asked in an interview "did you hit any problems," point directly at these sections instead of improvising a generic answer — they're already written, specific, and true
- [ ] Resist the urge to fix the class imbalance or the row-count error silently and remove the note that they existed — the fix matters less than the fact that you found it and can explain it

## Repo setup

- [ ] Repo name: something specific, not `data-project` — e.g. `global-job-market-intelligence`
- [ ] Topics: `data-science`, `sql`, `power-bi`, `machine-learning`, `nlp`, `postgresql`, `etl`
- [ ] Pin this repo on your GitHub profile if it's your strongest piece
- [ ] Repo description (GitHub's one-liner under the repo name): lead with the business framing, not the tech stack — e.g. "Salary and hiring trend intelligence across 142K+ real job records — SQL, ML, and Power BI, built with full data-quality transparency"

## README polish

- [ ] Add 1–2 actual screenshots once you've built the real `.pbix` in Power BI Desktop (the layout mockup included in this repo is a stand-in, not a substitute for a real screenshot)
- [ ] Consider a short GIF/Loom walkthrough of the dashboard linked near the top — this is a bigger differentiator than more text
- [ ] Verify every internal link (`reports/...`, `docs/...`) actually resolves once the repo is public

## Commit history

- [ ] Don't squash this into one commit. A believable history matches the phase structure this was actually built in: data acquisition → cleaning → schema → EDA → NLP → stats → ML → SQL → Power BI → docs. Structure commits phase-by-phase rather than one giant initial commit — it's a more honest and more readable history for a reviewer

## Final consistency pass (do this after any future edits)

- [ ] Any time you edit a number in one report, `grep -rn` for that number across the whole repo to catch copies in the README/resume bullets — a final consistency pass on this project caught exactly one such drift (a row-count arithmetic error propagated into 2 files) before publishing. Re-run that habit after any future edit, not just once at the end.
